from dataclass.position import Position
from dataclass.rotation import Rotation
from entities.entity import Entity
from blocks.block import Block

class TileEntity(Entity, Block):
    """Blocks with extra functionality"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
