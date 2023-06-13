from dataclass.position import Position
from dataclass.rotation import Rotation

class Entity():
    def __init__(self, entity_id: int, position: Position, rotation: Rotation, on_ground: bool) -> None:
        self.entity_id = entity_id
        self.position = position
        self.rotation = rotation
        self.on_ground = on_ground
