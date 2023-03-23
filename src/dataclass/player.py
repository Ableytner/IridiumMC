import uuid
from dataclasses import dataclass
from datetime import datetime
from queue import Queue

from dataclass.position import Position
from network.protocol import MinecraftProtocol

@dataclass
class Player():
    uuid: uuid.UUID
    name: str
    pos: Position
    rot: tuple[float, float]
    on_ground: bool
    mcprot: MinecraftProtocol
    network_in: Queue = None
    last_pos_update: datetime = None

    def __post_init__(self):
        if self.network_in is None:
            self.network_in = Queue()
        self.last_pos_update = datetime.now()

    def network_func(self):
        while True:
            try:
                conn_info = self.mcprot.read_packet()
                self.network_in.put(conn_info)
            except TimeoutError:
                pass
            except ConnectionAbortedError:
                return

    def __str__(self) -> str:
        return f"uuid={self.uuid}, name={self.name}, pos={self.pos}, rot={self.rot}, on_ground={self.on_ground}"
