import random

from PySide6.QtCore import QTimer

from ..resources import ResourceRegistry, SpriteProperties
from ..settings import EmotePreferences, Preferences
from ..states import AllowedEmoteStates, Direction, EndByTimeoutAnimations, State
from .animation_ticker import AnimationTicker
from .state_manager import StateManager
from .walk_manager import WalkManager


def _mins2ms(mins: int) -> int:
    return int(mins * 60 * 1000)


class TimerManager:
    def __init__(
        self,
        state_manager: StateManager,
        animation_ticker: AnimationTicker,
        walk_manager: WalkManager,
    ) -> None:
        """
        List of timers
        - master_timer:     Each tick updates one animation frame.
        - idle_timer:       Time spent idle; Tick fires sleep animation.
        - sleep_timer:      Time spent sleeping; Tick fires idle animation.
        - walk_idle_timer:  Time since last walking; Tick fires idle animation.
        - emote_timer:      Tick triggers emote animation.
        - emote_dur_timer:  Time spent emoting; Tick triggers idle animation.
        """

        self.state_manager = state_manager
        self.walk_manager = walk_manager

        self.master_timer = QTimer()
        self.idle_timer = QTimer()
        self.sleep_timer = QTimer()
        self.walk_idle_timer = QTimer()
        self.emote_timer = QTimer()
        self.emote_dur_timer = QTimer()

        self.walk_idle_timer.setSingleShot(True)
        self.emote_dur_timer.setSingleShot(True)

        self.master_timer.timeout.connect(animation_ticker.tick)
        self.idle_timer.timeout.connect(self.tick_idle_timer)
        self.sleep_timer.timeout.connect(self.tick_sleep_timer)
        self.walk_idle_timer.timeout.connect(self.tick_walk_idle_timer)
        self.emote_timer.timeout.connect(self.tick_emote_timer)
        self.emote_dur_timer.timeout.connect(self.tick_emote_dur_timer)

    def stop_all(self) -> None:
        """
        Stop every timer (called on shutdown).
        """
        for timer in (
            self.master_timer,
            self.idle_timer,
            self.sleep_timer,
            self.walk_idle_timer,
            self.emote_timer,
            self.emote_dur_timer,
        ):
            timer.stop()

    """
    @! ---- Package Timer Kickoffs -----------------------------------------------------------------
    """

    def start_passive_timer(self) -> None:
        base_interval = 1000 // SpriteProperties.FrameRate
        adjusted_interval = int(base_interval / Preferences.AnimationSpeed)
        self.master_timer.start(max(1, adjusted_interval))
        self.reset_passive_timer()

    def reset_passive_timer(self) -> None:
        self.reset_idle_timer()
        self.reset_emote_timer()

    """
    @! ---- Individual Timer Kickoffs --------------------------------------------------------------
    """

    def reset_idle_timer(self) -> None:
        timeout = _mins2ms(Preferences.IdleMinutes)
        self.idle_timer.start(timeout)

    def reset_sleep_timer(self) -> None:
        timeout = _mins2ms(Preferences.SleepMinutes)
        self.sleep_timer.start(timeout)

    def reset_walk_idle_timer(self) -> None:
        timeout = 10000
        self.walk_idle_timer.start(timeout)

    def reset_emote_timer(self) -> None:
        min_ms = _mins2ms(EmotePreferences.MinEmoteTriggerMinutes)
        max_ms = _mins2ms(EmotePreferences.MaxEmoteTriggerMinutes)

        # extra safety
        min_ms = max(10000, min_ms)
        max_ms = max(min_ms, max_ms)

        timeout = random.randint(min_ms, max_ms)
        self.emote_timer.start(timeout)

    def reset_emote_dur_timer(self) -> None:
        timeout = EmotePreferences.EmoteDuration
        self.emote_dur_timer.start(timeout)

    """
    @! ---- Timer Tick -----------------------------------------------------------------------------
    """

    def tick_idle_timer(self) -> None:
        if self.state_manager.current_state == State.IDLE:
            self.state_manager.transition_to(State.SLEEP)
            self.reset_sleep_timer()

    def tick_sleep_timer(self) -> None:
        if self.state_manager.current_state == State.SLEEP:
            self.state_manager.transition_to(State.IDLE)
            self.reset_idle_timer()

    def tick_walk_idle_timer(self) -> None:
        if self.state_manager.current_state == State.WALK_IDLE:
            self.state_manager.to_idle_or_hover()

    def tick_emote_timer(self) -> None:
        if self.state_manager.current_state in AllowedEmoteStates:
            possible_actions = [
                State.EMOTE,
                State.PAT,
                State.POKE,
                State.LEFT_ACTION,
                State.RIGHT_ACTION,
            ]
            available_actions = [
                state for state in possible_actions
                if (state, Direction.NONE) in ResourceRegistry.animations
            ]
            
            # Check if walk or run animations exist
            if (State.WALK, Direction.LEFT) in ResourceRegistry.animations or (State.RUN, Direction.LEFT) in ResourceRegistry.animations:
                available_actions.extend(["RANDOM_WALK"] * max(1, len(available_actions)))

            if not available_actions:
                self.reset_emote_timer()
                return

            action = random.choice(available_actions)
            
            if action == "RANDOM_WALK":
                self.walk_manager.start_random_walk()
                target_state = State.RUN if self.walk_manager.is_running else State.WALK
                if (target_state, self.walk_manager.get_direction()) not in ResourceRegistry.animations:
                    target_state = State.WALK if target_state == State.RUN else State.RUN
                self.state_manager.transition_to(target_state, self.walk_manager.get_direction())
                self.reset_emote_dur_timer()
            else:
                self.state_manager.transition_to(action)
                if action in EndByTimeoutAnimations:
                    self.reset_emote_dur_timer()
                else:
                    # Frame animations end through on_completion, so we restart passive timer now
                    self.reset_passive_timer()
        else:
            self.reset_emote_timer()

    def tick_emote_dur_timer(self) -> None:
        if self.state_manager.current_state == State.EMOTE:
            self.state_manager.to_idle_or_hover()
            self.reset_passive_timer()
        elif self.state_manager.current_state == State.WALK and self.walk_manager.is_random_walking:
            self.walk_manager.stop_random_walk()
            self.state_manager.transition_to(State.WALK_IDLE)
            self.reset_walk_idle_timer()
            self.reset_passive_timer()
