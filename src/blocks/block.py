from dataclass.position import Position

class Block():
    def __init__(self, position: Position) -> None:
        self.position = position
    
    block_id = -1
