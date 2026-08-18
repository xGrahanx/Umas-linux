from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent

from ..settings import Preferences
from ..states import Direction

DirectionMap = {
    (+0, +0): Direction.NONE,
    (-1, +0): Direction.UP,
    (+1, +0): Direction.DOWN,
    (+0, -1): Direction.LEFT,
    (+0, +1): Direction.RIGHT,
    (-1, -1): Direction.UP_LEFT,
    (-1, +1): Direction.UP_RIGHT,
    (+1, -1): Direction.DOWN_LEFT,
    (+1, +1): Direction.DOWN_RIGHT,
}


class WalkManager:
    def __init__(self):
        # state of movement keys
        self.w = False
        self.a = False
        self.s = False
        self.d = False

        # move speed (pixel per frame)
        self.base_v = Preferences.MoveSpeed
        self.is_running = False

        # random walk properties
        self.is_random_walking = False
        self.rand_hor = 0
        self.rand_ver = 0

    """
    @! ---- Movement Resolves ----------------------------------------------------------------------
    """

    def start_random_walk(self) -> None:
        import random
        self.is_random_walking = True
        self.rand_ver = random.choice([-1, 0, 1])
        self.rand_hor = random.choice([-1, 0, 1])
        # Ensure at least one direction is non-zero
        if self.rand_ver == 0 and self.rand_hor == 0:
            self.rand_hor = random.choice([-1, 1])
            
        # Randomly choose if running or walking
        self.is_running = random.choice([True, False])

    def stop_random_walk(self) -> None:
        self.is_random_walking = False

    @property
    def v(self) -> int:
        return self.base_v if self.is_running else max(1, self.base_v // 2)

    def get_velocity(self) -> tuple[int, int]:
        """
        Returns the velocity vector based on the current key states or random walk.
        If both keys in a direction are pressed, they cancel each other out.
        """
        if self.is_random_walking:
            return self.rand_hor * self.v, self.rand_ver * self.v
            
        vy = 0
        vx = 0
        if self.w ^ self.s:
            vy = -self.v if self.w else self.v
        if self.a ^ self.d:
            vx = -self.v if self.a else self.v
        return vx, vy

    def is_moving(self) -> bool:
        """
        Returns True if either vertical or horizontal movement is occurring.
        """
        if self.is_random_walking:
            return True
        return (self.w ^ self.s) or (self.a ^ self.d)

    def get_direction(self):
        """
        Returns a string representing the current movement direction for animation purposes.
        """
        if self.is_random_walking:
            return DirectionMap[(self.rand_ver, self.rand_hor)]
            
        ver = 0
        hor = 0
        if self.w ^ self.s:
            ver = -1 if self.w else 1
        if self.a ^ self.d:
            hor = -1 if self.a else 1
        return DirectionMap[(ver, hor)]

    """
    @! ---- Event Recorders ------------------------------------------------------------------------
    """

    def record_key_press(self, event: QKeyEvent):
        self.stop_random_walk()
        key = event.key()
        match key:
            case Qt.Key.Key_W:
                self.w = True
            case Qt.Key.Key_A:
                self.a = True
            case Qt.Key.Key_S:
                self.s = True
            case Qt.Key.Key_D:
                self.d = True
            case _:
                pass

    def record_key_release(self, event: QKeyEvent):
        key = event.key()
        match key:
            case Qt.Key.Key_W:
                self.w = False
            case Qt.Key.Key_A:
                self.a = False
            case Qt.Key.Key_S:
                self.s = False
            case Qt.Key.Key_D:
                self.d = False
            case _:
                pass

    def record_mouse_leave(self):
        # stop all movement when mouse leaves window
        self.w = False
        self.a = False
        self.s = False
        self.d = False
