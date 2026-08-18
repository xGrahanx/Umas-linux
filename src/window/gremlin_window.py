import sys
import os
import subprocess
import threading

from PySide6.QtCore import Qt, QMetaObject, Slot
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from .. import resources
from ..engines import FrameEngine, SoundEngine
from ..fsm.animation_ticker import AnimationTicker
from ..fsm.state_manager import StateManager
from ..fsm.timer_manager import TimerManager
from ..fsm.walk_manager import WalkManager
from ..settings import Preferences
from ..states import State, AllowedClickStates, Direction
from .hotspot_manager import HotspotManager
from .hover_manager import HoverManager
from .input_filter import WindowInputFilter
from .keyboard_manager import KeyboardManager
from .mouse_manager import MouseManager
from .systray_icon import SystrayIcon


class GremlinWindow(QWidget):

    def __init__(self) -> None:
        super().__init__()

        # --- Window setup ---------------------------------------------------------------
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )

        # True if running under the niri compositor
        self.is_niri = os.environ.get("NIRI_SOCKET") is not None

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        scale = Preferences.Scale
        w = int(resources.SpriteProperties.FrameWidth * scale)
        h = int(resources.SpriteProperties.FrameHeight * scale)
        self.setFixedSize(w, h)
        self.setWindowTitle("ilgwg_desktop_gremlins.py")

        # --- Sprite label ---------------------------------------------------------------
        self.sprite_label = QLabel(self)
        self.sprite_label.setGeometry(0, 0, w, h)
        self.sprite_label.setScaledContents(True)

        # --- Core logic components ------------------------------------------------------
        self.frame_engine = FrameEngine(self.sprite_label)
        self.sound_engine = SoundEngine(self)
        self.walk_manager = WalkManager()
        self.state_manager = StateManager(
            self.sound_engine, self.underMouse, self._on_exit
        )
        self.animation_ticker = AnimationTicker(
            self.state_manager, self.frame_engine, self._update_position
        )
        self.timer_manager = TimerManager(
            self.state_manager, self.animation_ticker, self.walk_manager
        )

        # --- Input managers (no event-slot assignment) ----------------------------------
        self.mouse_manager = MouseManager(
            self.state_manager, self.timer_manager, self.walk_manager, self
        )
        self.keyboard_manager = KeyboardManager(
            self.state_manager, self.walk_manager, self.timer_manager
        )
        self.hover_manager = HoverManager(
            self.walk_manager, self.state_manager, self.timer_manager, self
        )
        self.hotspot_manager = HotspotManager(
            self.state_manager, self.timer_manager, self.mouse_manager, self
        )

        # --- Centralised event filter ---------------------------------------------------
        self.input_filter = WindowInputFilter(self)
        self.input_filter.register_mouse(self.mouse_manager)
        self.input_filter.register_keyboard(self.keyboard_manager)
        self.input_filter.register_hover(self.hover_manager)
        self.installEventFilter(self.input_filter)

        # --- Systray + start ------------------------------------------------------------
        self.systray_icon = SystrayIcon(self, self.close_app)
        self._closing = False

        # start optional Niri background listener (will gracefully fail if not on niri)
        self._start_niri_listener()

        self.state_manager.transition_to(State.INTRO)
        self.timer_manager.start_passive_timer()

    def _update_position(self) -> None:
        dx, dy = 0, 0
        cur_state = self.state_manager.current_state
        screen = QApplication.primaryScreen().availableGeometry()

        # 1. Walk velocity
        if cur_state in (State.WALK, State.RUN) or self.walk_manager.is_thrown:
            dx, dy = self.walk_manager.get_velocity(self.pos(), self.width(), self.height())
            
            if self.walk_manager.is_tracking_mouse:
                if dx == 0 and dy == 0:
                    self.walk_manager.stop_mouse_tracking()
                    self.state_manager.transition_to(State.WALK_IDLE)
                else:
                    new_dir = self.walk_manager.get_direction()
                    if new_dir != self.state_manager.current_direction and new_dir != Direction.NONE:
                        self.state_manager.transition_to(cur_state, new_dir)
                    
            if self.walk_manager.is_random_walking:
                new_x = self.pos().x() + dx
                new_y = self.pos().y() + dy
                # bounce horizontally
                if new_x < screen.left() or new_x + self.width() > screen.right():
                    self.walk_manager.rand_hor *= -1
                    dx = self.walk_manager.rand_hor * self.walk_manager.v
                    self.state_manager.transition_to(cur_state, self.walk_manager.get_direction())
                # bounce vertically
                if new_y < screen.top() or new_y + self.height() > screen.bottom():
                    self.walk_manager.rand_ver *= -1
                    dy = self.walk_manager.rand_ver * self.walk_manager.v
                    self.state_manager.transition_to(cur_state, self.walk_manager.get_direction())

            if self.walk_manager.is_thrown:
                new_x = self.pos().x() + dx
                new_y = self.pos().y() + dy
                # bounce horizontally
                if new_x < screen.left() or new_x + self.width() > screen.right():
                    self.walk_manager.throw_vx *= -0.8
                    dx = int(self.walk_manager.throw_vx)
                # bounce vertically
                if new_y < screen.top() or new_y + self.height() > screen.bottom():
                    self.walk_manager.throw_vy *= -0.8
                    dy = int(self.walk_manager.throw_vy)

        # 2. Apply movement
        if dx != 0 or dy != 0:
            new_x = self.pos().x() + dx
            new_y = self.pos().y() + dy

            if new_x != self.pos().x() or new_y != self.pos().y():
                self.move(new_x, new_y)
                if self.is_niri:
                    subprocess.run(
                        [
                            "niri",
                            "msg",
                            "action",
                            "move-floating-window",
                            "--x",
                            str(new_x),
                            "--y",
                            str(new_y),
                        ],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )

    def _on_exit(self) -> None:
        self.timer_manager.stop_all()
        QApplication.quit()
        sys.exit(0)

    def _start_niri_listener(self) -> None:
        def listen():
            try:
                proc = subprocess.Popen(
                    ["niri", "msg", "-j", "event-stream"],
                    stdout=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                for line in iter(proc.stdout.readline, ''):
                    if "WindowFocusChanged" in line or "WorkspaceActivated" in line:
                        QMetaObject.invokeMethod(self, "_on_window_focus_changed", Qt.ConnectionType.QueuedConnection)
            except Exception:
                pass
                
        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    @Slot()
    def _on_window_focus_changed(self) -> None:
        # Check if we are in a state that can be interrupted
        if self.state_manager.current_state in AllowedClickStates:
            self.state_manager.transition_to(State.POKE)
            self.timer_manager.reset_emote_dur_timer()

    def close_app(self) -> None:
        if self._closing:
            return
        self._closing = True
        self.state_manager.transition_to(State.OUTRO)
        self.input_filter.unregister_all()

    def closeEvent(self, event) -> None:
        event.ignore()
        self.close_app()
