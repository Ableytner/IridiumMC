import logging
import struct
import uuid
from dataclasses import dataclass
from queue import Queue
from typing import TYPE_CHECKING

from network import server_packets
if TYPE_CHECKING:
    from core.iridium_server import IridiumServer
from dataclass.save import World
from dataclass.position import Position
from network.protocol import MinecraftProtocol

@dataclass
class Player():
    server: "IridiumServer"
    uuid: uuid.UUID
    name: str
    pos: Position
    rot: tuple[float, float]
    on_ground: bool
    view_dist: int
    mcprot: MinecraftProtocol
    network_in: Queue = None
    keepalive: list[int, int, int] = None
    loaded_chunks: dict[int, dict[int, bool]] = None

    def __post_init__(self):
        if self.network_in is None:
            self.network_in = Queue()
        
        # [status_id, remaining, value]
        # status_id: 0=WAITING, 1=SENT_TO_CLIENT
        # remaining: ticks until next status change
        # value: random int to be sent back by client, or 0
        self.keepalive = [0, 100, 0]
        self.loaded_chunks = {}

    def load_chunks(self, world: World):
        center_chunk_pos = Position(self.pos.x//16, self.pos.y, self.pos.z//16)
        for dist_to_center_blocks in range(self.view_dist):
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
                    self.server.disconnect_player(self, {"text": f"Unknown packet id: {hex(conn_info)}", "bold": True, "color": "dark_green"})
                    return
            except TimeoutError:
                pass
            except (ConnectionAbortedError, OSError):
                return
            except struct.error as err:
                # assume that the player disconnected client-side
                logging.debug(err)
                self.server.disconnect_player(self)
                return

    def _is_chunk_loaded(self, chunk_x: int, chunk_z: int) -> bool:
        if not (chunk_x in self.loaded_chunks.keys()):
            return False
        if not (chunk_z in self.loaded_chunks[chunk_x].keys()):
            return False
        return self.loaded_chunks[chunk_x][chunk_z]

    def __str__(self) -> str:
        return f"uuid={self.uuid}, name={self.name}, pos={self.pos}, rot={self.rot}, on_ground={self.on_ground}"
