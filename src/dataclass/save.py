from __future__ import annotations
from collections import defaultdict
import zlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.iridium_server import IridiumServer
from dataclass.position import Position
from blocks.air import Air
from blocks.block import Block
from core import binary_operations

@dataclass
class Chunk():
    blocks: dict[int, Block|None] = field(default_factory=lambda: {})

    def set_block(self, pos: Position, block: Block) -> None:
        self.blocks[self._pos_to_int(pos)] = block
    
    def get_block(self, pos: Position) -> Block:
        block_pos = self._pos_to_int(pos)
        if not block_pos in self.blocks.keys():
            return Air()
        return self.blocks[self._pos_to_int(pos)]

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
                        block_types.append(self.get_block(Position(x, y, z)).block_id)
                        block_metadatas.append(0b0110) # broken
                        block_lights.append(0b100) # can't check if its working
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

    def _pos_to_int(self, pos: Position) -> int:
        return ((pos.x << 8) + (pos.y << 4) + pos.z)

    def _int_to_pos(self, value: int) -> Position:
        x = value >> 8
        y = (value - (x << 8)) >> 4
        z = value - ((x << 8) + (y << 4))
        return Position(x, y, z)

@dataclass
class ChunkColumn():
    chunks: dict[int, Chunk] = field(default_factory=lambda: {})

    def get_block(self, pos: Position) -> Block:
        if not (pos.y//16) in self.chunks:
            return Air()
        return self.chunks[pos.y//16].get_block(Position(pos.x, pos.y%16, pos.z))

    def set_block(self, pos: Position, block: Block) -> None:
        if not (pos.y//16) in self.chunks:
            self.chunks[pos.y//16] = Chunk()
        return self.chunks[pos.y//16].set_block(Position(pos.x, pos.y%16, pos.z), block)

    def to_packet_data(self, chunk_x: int, chunk_z: int) -> tuple[int, int, bool, bytes, bytes]:
        block_type = b""
        block_metadata = b""
        block_light = b""
        sky_light = b""
        add = b""
        biome = b""
        primary_bitmap = 0

        for c in range(16):
            if c in self.chunks.keys():
                chunk_data = self.chunks[c].to_packet_data()
                block_type += chunk_data[0]
                block_metadata += chunk_data[1]
                block_light += chunk_data[2]
                sky_light += chunk_data[3]
                add += chunk_data[4]
                biome += chunk_data[5]
                primary_bitmap += (1 << c)

        zlibbed_str = zlib.compress(block_type + block_metadata + block_light + sky_light + add + biome)
        data_compressed = zlibbed_str
        data_len = len(data_compressed)

        metadata = binary_operations._encode_int(chunk_x)
        metadata += binary_operations._encode_int(chunk_z)
        metadata += binary_operations._encode_unsigned_short(primary_bitmap) # primary bitmap, 1 sends chunk
        metadata += binary_operations._encode_unsigned_short(0b0000000000000000) # add bitmap, all empty
        return (1, data_len, True, data_compressed, metadata)

@dataclass
class World():
    server: "IridiumServer"
    dim_id: int
    chunk_columns: dict[int, dict[int, ChunkColumn|None]] = field(default_factory=lambda: defaultdict(dict))

    def get_block(self, pos: Position) -> Block:
        if (not (pos.z//16) in self.chunk_columns[pos.x//16].keys()) or \
           self.chunk_columns[pos.x//16][pos.z//16] is None:
            raise Exception("Chunk not generated!")
        return self.chunk_columns[pos.x//16][pos.z//16].get_block(Position(pos.x%16, pos.y, pos.z%16))

    def set_block(self, pos: Position, block: Block) -> None:
        if not (pos.z//16) in self.chunk_columns[pos.x//16].keys():
            self.chunk_columns[pos.x//16][pos.z//16] = ChunkColumn()
        return self.chunk_columns[pos.x//16][pos.z//16].set_block(Position(pos.x%16, pos.y, pos.z%16), block)

    def to_packet_data(self, chunk_x: int, chunk_z: int):
        if not self.chunk_exists(chunk_x, chunk_z):
            self.server.generate_chunk(chunk_x*16, chunk_z*16)
        return self.chunk_columns[chunk_x][chunk_z].to_packet_data(chunk_x, chunk_z)

    def chunk_exists(self, chunk_x: int, chunk_z: int) -> bool:
        if not (chunk_x in self.chunk_columns.keys()):
            return False
        if not (chunk_z in self.chunk_columns[chunk_x].keys()):
            return False
        return isinstance(self.chunk_columns[chunk_x][chunk_z], ChunkColumn)
