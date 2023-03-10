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
        for x in range(-4, 4):
            for z in range(-4, 4):
                self._generate_chunk_column(((position.x//16) * 16) + (x*16), ((position.z//16) * 16) + (z*16))

    def _generate_chunk_column(self, start_pos_x: int, start_pos_z):
        chunk_column = ChunkColumn()
        
        if self._level_type == "flat":
            for y1 in range(16):
                new_chunk = Chunk(start_pos_x, start_pos_z)
                for y2 in range(16):
                    for x in range(16):
                        for z in range(16):
                            if (y1+y2) <= 5:
                                new_chunk.blocks[x][(y1*16)+y2][z] = Block(Position(start_pos_x + x, (y1*16)+y2, start_pos_z + z), 3)
                chunk_column.chunks[y1] = new_chunk

        self.world.chunk_columns[start_pos_x][start_pos_z] = chunk_column
