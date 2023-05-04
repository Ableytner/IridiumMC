from dataclass.position import Position
from dataclass.rotation import Rotation

class Entity():
    def __init__(self, position: Position, rotation: Rotation, on_ground: bool) -> None:
        self.position = position
        self.rotation = rotation
        self.on_ground = on_ground
