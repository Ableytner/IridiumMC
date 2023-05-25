import logging
import struct
import uuid
from dataclasses import dataclass
from queue import Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from network.protocol import MinecraftProtocol

from core import server_provider
from network import server_packets
from dataclass.save import World
from dataclass.position import Position
from entities.living_entity import LivingEntity

class PlayerEntity(LivingEntity):
    def __init__(self, uuid: uuid.UUID, name: str, view_dist: int, mcprot: "MinecraftProtocol", **kwargs) -> None:
        super().__init__(**kwargs)
        self.uuid = uuid
        self.name = name
        self.view_dist = view_dist
        self.mcprot = mcprot
        self.network_in = Queue()

        # [status_id, remaining, value]
        # status_id: 0=WAITING, 1=SENT_TO_CLIENT
        # remaining: ticks until next status change
        # value: random int to be sent back by client, or 0
        self.keepalive = [0, 100, 0]
        self.loaded_chunks = {}

    def load_chunks(self, world: World):
        chunk_radius = self.view_dist
        if chunk_radius > server_provider.get().VIEW_DIST:
            chunk_radius = server_provider.get().VIEW_DIST
        center_chunk_pos = Position(self.position.x//16, self.position.y, self.position.z//16)
        for dist_to_center_blocks in range(chunk_radius):
            for x in range(int(center_chunk_pos.x - dist_to_center_blocks), int(center_chunk_pos.x + dist_to_center_blocks)):
                for z in range(int(center_chunk_pos.z - dist_to_center_blocks), int(center_chunk_pos.z + dist_to_center_blocks)):
                    if not self._is_chunk_loaded(x, z):
                        chunk_data = world.to_packet_data(x, z)
                        self.mcprot.write_packet(server_packets.MapChunkBulk(*chunk_data))
                        
                        if not (x in self.loaded_chunks.keys()):
                            self.loaded_chunks[x] = {}
                        self.loaded_chunks[x][z] = True
                        return

    def network_func(self):
        while True:
            try:
                conn_info = self.mcprot.read_packet()
                if not isinstance(conn_info, int):
                    self.network_in.put(conn_info)
                else:
                    logging.error(f"Unknown packet id: {hex(conn_info)}")
                    server_provider.get().disconnect_player(self, {"text": f"Unknown packet id: {hex(conn_info)}", "bold": True, "color": "dark_green"})
                    return
            except TimeoutError:
                pass
            except (ConnectionAbortedError, OSError):
                return
            except struct.error as err:
                # assume that the player disconnected client-side
                logging.debug(err)
                server_provider.get().disconnect_player(self)
                return

    def _is_chunk_loaded(self, chunk_x: int, chunk_z: int) -> bool:
        if not (chunk_x in self.loaded_chunks.keys()):
            return False
        if not (chunk_z in self.loaded_chunks[chunk_x].keys()):
            return False
        return self.loaded_chunks[chunk_x][chunk_z]

    def __str__(self) -> str:
        return f"uuid={self.uuid}, name={self.name}, pos={self.pos}, rot={self.rot}, on_ground={self.on_ground}"
