import string

from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import Qt

from ..fsm.state_manager import StateManager
from ..fsm.timer_manager import TimerManager
from ..fsm.walk_manager import WalkManager
from ..resources import ResourceRegistry
from ..settings import Preferences
from ..states import AllowedEmoteStates, AllowedWalkStates, State, Direction


def resolve_emote_key() -> int | None:
    """
    If the emote key is enabled and valid, returns its ord key code.
    Otherwise, return None.
    """

    if not Preferences.EmoteKeyEnabled:
        return None

    key = Preferences.EmoteKey

    try:
        # limits to qwerty alphanumerical chars and digits 0-9
        char = key.strip().upper()
        if char not in string.ascii_uppercase + string.digits:
            print(f"\n[Warning] EmoteKey {key!r} not allowed (allowed: A-Z, 0-9)")
            return None
        return ord(char)
    except Exception:
        return None


class KeyboardManager:
    def __init__(
        self,
        state_manager: StateManager,
        walk_manager: WalkManager,
        timer_manager: TimerManager,
    ) -> None:
        self.state_manager = state_manager
        self.walk_manager = walk_manager
        self.timer_manager = timer_manager
        self.emote_key = resolve_emote_key()

    def on_key_press(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return

        # check for walk
        self.walk_manager.record_key_press(event)
        if (
            self.walk_manager.is_moving()
            and self.state_manager.current_state in AllowedWalkStates
        ):
            target_state = State.RUN
            if (target_state, self.walk_manager.get_direction()) not in ResourceRegistry.animations:
                target_state = State.WALK
            
            self.walk_manager.is_running = (target_state == State.RUN)
            self.state_manager.transition_to(
                target_state, self.walk_manager.get_direction()
            )
            self.timer_manager.reset_passive_timer()

        if event.key() == Qt.Key.Key_M:
            if self.walk_manager.is_tracking_mouse:
                self.walk_manager.stop_mouse_tracking()
                self.state_manager.transition_to(State.WALK_IDLE)
            elif self.state_manager.current_state in AllowedWalkStates:
                self.walk_manager.stop_random_walk()
                self.walk_manager.start_mouse_tracking(True)
                target_state = State.RUN
                if (target_state, self.walk_manager.get_direction()) not in ResourceRegistry.animations:
                    target_state = State.WALK
                self.walk_manager.is_running = (target_state == State.RUN)
                self.state_manager.transition_to(target_state, self.walk_manager.get_direction())
                self.timer_manager.reset_emote_dur_timer()
            return

        if event.key() == Qt.Key.Key_O:
            if self.walk_manager.is_orbiting:
                self.walk_manager.stop_orbit()
                self.state_manager.transition_to(State.WALK_IDLE)
            elif self.state_manager.current_state in AllowedWalkStates:
                self.walk_manager.start_orbit()
                initial_dir = self.walk_manager.get_direction()
                if initial_dir == Direction.NONE:
                    initial_dir = Direction.DOWN
                    
                target_state = State.RUN
                if (target_state, initial_dir) not in ResourceRegistry.animations:
                    target_state = State.WALK
                self.walk_manager.is_running = (target_state == State.RUN)
                self.state_manager.transition_to(target_state, initial_dir)
            return
            
        if event.key() == Qt.Key.Key_R:
            if self.walk_manager.is_stealing_mouse:
                self.walk_manager.stop_stealing_mouse()
                self.state_manager.transition_to(State.WALK_IDLE)
            elif self.state_manager.current_state in AllowedWalkStates:
                self.walk_manager.start_stealing_mouse()
                initial_dir = self.walk_manager.get_direction()
                if initial_dir == Direction.NONE:
                    initial_dir = Direction.DOWN
                    
                target_state = State.RUN
                if (target_state, initial_dir) not in ResourceRegistry.animations:
                    target_state = State.WALK
                self.walk_manager.is_running = (target_state == State.RUN)
                self.state_manager.transition_to(target_state, initial_dir)
                self.timer_manager.reset_emote_dur_timer(5000) # steal mouse for 5 seconds max
            return

        # check for manual emote trigger
        if (
            self.emote_key is not None
            and event.key() == self.emote_key
            and self.state_manager.current_state in AllowedEmoteStates
        ):
            self.state_manager.transition_to(State.EMOTE)
            self.timer_manager.reset_emote_dur_timer()
            self.timer_manager.reset_passive_timer()

    def on_key_release(self, event: QKeyEvent) -> None:
        if event.isAutoRepeat():
            return

        self.walk_manager.record_key_release(event)

        # if was walking or running...
        if self.state_manager.current_state in (State.WALK, State.RUN):
            # ...and continued walking, change direction
            if self.walk_manager.is_moving():
                target_state = State.RUN if self.walk_manager.is_running else State.WALK
                if (target_state, self.walk_manager.get_direction()) not in ResourceRegistry.animations:
                    target_state = State.WALK
                    
                self.state_manager.transition_to(
                    target_state, self.walk_manager.get_direction()
                )
            # ...and not walking anymore, switch to walk idle
            else:
                self.state_manager.transition_to(State.WALK_IDLE)
                self.timer_manager.reset_walk_idle_timer()
