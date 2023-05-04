from dataclass.position import Position
from dataclass.rotation import Rotation
from entities.entity import Entity

class LivingEntity(Entity):
    """Entities that are alive (animals, mobs, ...)"""

    def __init__(self, health: float, **kwargs) -> None:
        super().__init__(**kwargs)
        self.health = health
