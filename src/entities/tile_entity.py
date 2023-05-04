from dataclass.position import Position
from dataclass.rotation import Rotation
from entities.entity import Entity

class TileEntity(Entity):
    """Blocks with extra functionality"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
