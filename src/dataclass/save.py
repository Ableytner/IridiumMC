from __future__ import annotations
from collections import defaultdict
import zlib
from dataclasses import dataclass, field

from dataclass.position import Position
from core import binary_operations

@dataclass
class Block():
    pos: Position
    block_id: int

    @property
    def chunk_pos(self) -> Position:
        return Position(self.pos.x % 16, self.pos.y, self.pos.z % 16)

    @staticmethod
    def air() -> Block:
        return Block(Position(0, 0, 0), 0)

@dataclass
class Chunk():
    x: int
    z: int
    blocks: dict[int, dict[int, dict[int, Block|None]]] = field(default_factory=lambda: defaultdict(lambda: defaultdict(dict)))

    def to_packet_data(self) -> tuple[bytes, bytes, bytes, bytes, bytes, bytes]:
        block_types = []
        block_metadatas = []
        block_lights = []
        sky_lights = []
        adds = []
        biomes = []

        for chunk_c in range(16):
            for y in range(chunk_c, chunk_c + 16):
                for z in range(16):
                    for x in range(16):
                        try:
                            block = self.blocks[x][y][z]
                        except KeyError:
                            block = Block.air()

                        block_types.append(block.block_id)
                        block_metadatas.append(0b0000)
                        block_lights.append(0b1000)
                        sky_lights.append(0b1111)
                        adds.append(0b0000)
                    biomes.append(1)

        block_type = b""
        block_metadata = b""
        block_light = b""
        sky_light = b""
        add = b""
        biome = b""
        for c in range(len(block_types)):
            block_type += binary_operations._encode_byte(block_types[c])
            if c % 2 != 0:
                block_metadata += binary_operations._encode_nibbles(block_metadatas[c-1], block_metadatas[c])
                block_light += binary_operations._encode_nibbles(block_lights[c-1], block_lights[c])
                sky_light += binary_operations._encode_nibbles(sky_lights[c-1], sky_lights[c])
                # add += binary_operations._encode_nibbles(adds[c-1], adds[c])
            if c % 16 == 0:
                biome += binary_operations._encode_byte(biomes[int(c/16)])

        return (block_type, block_metadata, block_light, sky_light, add, biome)

@dataclass
class ChunkColumn():
    chunks: dict[int, Chunk] = field(default_factory=lambda: {})

    def to_packet_data(self) -> tuple[int, int, bool, bytes, bytes]:
        block_type = b""
        block_metadata = b""
        block_light = b""
        sky_light = b""
        add = b""
        biome = b""

        for c in range(16):
            chunk_data = self.chunks[c].to_packet_data()
            block_type += chunk_data[0]
            block_metadata += chunk_data[1]
            block_light += chunk_data[2]
            sky_light += chunk_data[3]
            add += chunk_data[4]
            biome += chunk_data[5]

        zlibbed_str = zlib.compress(block_type + block_metadata + block_light + sky_light + add + biome)
        data_compressed = zlibbed_str
        data_len = len(data_compressed)

        metadata = binary_operations._encode_int(self.chunks[0].x) # chunk x
        metadata += binary_operations._encode_int(self.chunks[0].z) # chunk z
        metadata += binary_operations._encode_unsigned_short(0b1111111111111111) # primary bitmap, all 1 to send all chunks
        metadata += binary_operations._encode_unsigned_short(0b0000000000000000) # add bitmap, all empty
        return (1, data_len, True, data_compressed, metadata)

@dataclass
class World():
    dim_id: int
    chunk_columns: dict[int, dict[int, ChunkColumn|None]] = field(default_factory=lambda: defaultdict(dict))
    
    def chunk_column_count(self) -> int:
        c = 0
        for item in self.chunk_columns.values():
            for item2 in item.values():
                c += 1
        return c

    def to_packet_data(self, chunk_x: int, chunk_z: int):
        return self.chunk_columns[chunk_x][chunk_z].to_packet_data()
