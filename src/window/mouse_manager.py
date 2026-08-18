import time
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget

from ..fsm.state_manager import StateManager
from ..fsm.timer_manager import TimerManager
from ..fsm.walk_manager import WalkManager
from ..states import AllowedClickStates, State


class MouseManager:
    def __init__(
        self,
        state_manager: StateManager,
        timer_manager: TimerManager,
        walk_manager: WalkManager,
        window: QWidget,
    ) -> None:
        self.state_manager = state_manager
        self.timer_manager = timer_manager
        self.walk_manager = walk_manager

        self._move_window = window.move
        self._window_pos = window.pos
        self._drag_pos = QPoint(0, 0)
        self._last_mouse_time = 0.0
        self._last_mouse_pos = QPoint(0, 0)

    def on_mouse_press(self, event: QMouseEvent) -> None:
        # ignore clicks in disallowed states
        if self.state_manager.current_state not in AllowedClickStates:
            return

        # received interation from user --> reset passive timer
        self.timer_manager.reset_passive_timer()

        # transition to grab
        if event.button() == Qt.MouseButton.LeftButton:
            self.state_manager.transition_to(State.GRAB)
            self._drag_pos = event.globalPosition().toPoint() - self._window_pos()
        # transition to poke
        elif event.button() == Qt.MouseButton.RightButton:
            self.state_manager.transition_to(State.POKE)

    def on_mouse_move(self, event: QMouseEvent) -> None:
        if (
            self.state_manager.current_state == State.GRAB
            and event.buttons() == Qt.MouseButton.LeftButton
        ):
            # calculate throwing physics
            now = time.time()
            if self._last_mouse_time > 0 and (now - self._last_mouse_time) < 0.2:
                # keep track of velocity
                dt = now - self._last_mouse_time
                if dt > 0:
                    dx = event.globalPosition().x() - self._last_mouse_pos.x()
                    dy = event.globalPosition().y() - self._last_mouse_pos.y()
                    # velocity in pixels per second, converted to pixels per frame (assuming 60fps)
                    self._throw_vx = (dx / dt) / 60.0
                    self._throw_vy = (dy / dt) / 60.0
            else:
                self._throw_vx = 0.0
                self._throw_vy = 0.0

            self._last_mouse_pos = event.globalPosition().toPoint()
            self._last_mouse_time = now

            self._move_window(event.globalPosition().toPoint() - self._drag_pos)

    def on_mouse_release(self, event: QMouseEvent) -> None:
        # release from grab
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.state_manager.current_state == State.GRAB
        ):
            # Check if we should throw
            now = time.time()
            if self._last_mouse_time > 0 and (now - self._last_mouse_time) < 0.15:
                # If velocity is high enough, start throw
                if abs(getattr(self, '_throw_vx', 0)) > 2 or abs(getattr(self, '_throw_vy', 0)) > 2:
                    self.walk_manager.start_throw(self._throw_vx, self._throw_vy)
            
            self._throw_vx = 0.0
            self._throw_vy = 0.0
            self.state_manager.to_idle_or_hover()
