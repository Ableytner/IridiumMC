from blocks.block import Block
from dataclass.position import Position
from entities.tile_entity import TileEntity

class TNT(Block):
    def __init__(self, position: Position) -> None:
        super().__init__(position)

    block_id = 46
