from entities.entity import Entity

class LivingEntity(Entity):
    """Entities that are alive (animals, mobs, ...)"""

    def __init__(self, health: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.health = health
