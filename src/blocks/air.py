from blocks.block import Block
from dataclass.position import Position

class Air(Block):
    def __init__(self, position: Position) -> None:
        super().__init__(position)

    block_id = 0
