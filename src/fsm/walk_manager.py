from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QKeyEvent, QCursor

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

        # mouse tracking
        self.is_tracking_mouse = False
        self.is_tracking_manually = False
        self.tracking_ver = 0
        self.tracking_hor = 0

        # throwing physics
        self.is_thrown = False
        self.throw_vx = 0.0
        self.throw_vy = 0.0

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

    def start_mouse_tracking(self, manual: bool = False) -> None:
        self.is_tracking_mouse = True
        self.is_tracking_manually = manual
        self.is_running = True # Run when chasing mouse
        self.is_thrown = False

    def stop_mouse_tracking(self) -> None:
        self.is_tracking_mouse = False
        self.is_tracking_manually = False

    def start_throw(self, vx: float, vy: float) -> None:
        self.is_thrown = True
        self.throw_vx = vx
        self.throw_vy = vy
        self.is_random_walking = False
        self.is_tracking_mouse = False

    def stop_throw(self) -> None:
        self.is_thrown = False
        self.throw_vx = 0.0
        self.throw_vy = 0.0

    @property
    def v(self) -> int:
        return self.base_v if self.is_running else max(1, self.base_v // 2)

    def get_velocity(self, current_pos: QPoint = None, width: int = 0, height: int = 0) -> tuple[int, int]:
        """
        Returns a tuple of (vx, vy) based on the current movement parameters.
        Applies friction if throwing.
        """
        if self.is_thrown:
            self.throw_vx *= 0.98  # friction
            self.throw_vy *= 0.98
            
            # stop if too slow
            if abs(self.throw_vx) < 0.5 and abs(self.throw_vy) < 0.5:
                self.stop_throw()
                return 0, 0
                
            return int(self.throw_vx), int(self.throw_vy)
            
        if self.is_tracking_mouse and current_pos is not None:
            import math
            cursor_pos = QCursor.pos()
            
            # Center of the gremlin
            cx = current_pos.x() + width / 2
            cy = current_pos.y() + height / 2
            
            dx = cursor_pos.x() - cx
            dy = cursor_pos.y() - cy
            
            dist = math.hypot(dx, dy)
            if dist < 10:  # stop if close enough
                self.tracking_ver = 0
                self.tracking_hor = 0
                return 0, 0
                
            # Determine direction mapping (-1, 0, 1)
            self.tracking_ver = -1 if dy < -dist/2.5 else (1 if dy > dist/2.5 else 0)
            self.tracking_hor = -1 if dx < -dist/2.5 else (1 if dx > dist/2.5 else 0)
            if self.tracking_ver == 0 and self.tracking_hor == 0:
                if abs(dx) > abs(dy):
                    self.tracking_hor = -1 if dx < 0 else 1
                else:
                    self.tracking_ver = -1 if dy < 0 else 1
                
            # Boost speed significantly when chasing the mouse so it feels more like a sprint
            chase_speed = int(self.v * 1.8)
            vx = int((dx / dist) * chase_speed)
            vy = int((dy / dist) * chase_speed)
            return vx, vy

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
        if self.is_tracking_mouse:
            return self.tracking_ver != 0 or self.tracking_hor != 0
        if self.is_random_walking:
            return True
        return (self.w ^ self.s) or (self.a ^ self.d)

    def get_direction(self):
        """
        Returns a string representing the current movement direction for animation purposes.
        """
        if self.is_tracking_mouse:
            dir = DirectionMap.get((self.tracking_ver, self.tracking_hor), Direction.NONE)
            if dir == Direction.NONE:
                return Direction.DOWN
            return dir
            
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
