from dataclass.position import Position
from dataclass.save import Block, Chunk, ChunkColumn, World

class WorldGenerator():
    def __init__(self, level_type, world: World) -> None:
        self._level_type = level_type
        self._world = world
    
    @property
    def world(self) -> World:
        return self._world

    def generate_start_region(self, position: Position):
        for x in range(-(4*16), 4*16, 16):
            for z in range(-(4*16), 4*16, 16):
                self._generate_chunk_column(((position.x//16) * 16) + x, ((position.z//16) * 16) + z)

    def _generate_chunk_column(self, start_pos_x: int, start_pos_z):
        if self._level_type == "flat":
            for y in range(256):
                for x in range(16):
                    for z in range(16):
                        if (y) <= 5:
                            self.world.set_block(Position(start_pos_x + x, y, start_pos_z + z), Block(17))
