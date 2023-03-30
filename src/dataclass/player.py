import logging
import uuid
from dataclasses import dataclass
from queue import Queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.iridium_server import IridiumServer
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
    mcprot: MinecraftProtocol
    network_in: Queue = None
    keepalive: list[int, int, int] = None

    def __post_init__(self):
        if self.network_in is None:
            self.network_in = Queue()
        
        # [status_id, remaining, value]
        # status_id: 0=WAITING, 1=SENT_TO_CLIENT
        # remaining: ticks until next status change
        # value: random int to be sent back by client, or 0
        self.keepalive = [0, 100, 0]

    def network_func(self):
        while True:
            try:
                conn_info = self.mcprot.read_packet()
                if not isinstance(conn_info, int):
                    self.network_in.put(conn_info)
                else:
                    logging.error(f"Unknown packet id: {hex(conn_info)}")
                    self.server.disconnect_player(self, f"Unknown packet id: {hex(conn_info)}")
                    return
            except TimeoutError:
                pass
            except (ConnectionAbortedError, OSError):
                return

    def __str__(self) -> str:
        return f"uuid={self.uuid}, name={self.name}, pos={self.pos}, rot={self.rot}, on_ground={self.on_ground}"
