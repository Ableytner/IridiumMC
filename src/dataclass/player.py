import asyncio
import uuid
from dataclasses import dataclass
from threading import Thread, Event
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

    def __post_init__(self):
        if self.network_in is None:
            self.network_in = Queue()

    def network_func(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self._network_func_async())
        loop.close()

    async def _network_func_async(self):
        while True:
            print("Client network")
            try:
                conn_info = await self.mcprot.read_packet()
                self.network_in.put(conn_info)
            except asyncio.TimeoutError:
                pass
            except ConnectionAbortedError:
                return

    def __str__(self) -> str:
        return f"uuid={self.uuid}, name={self.name}, pos={self.pos}, rot={self.rot}, on_ground={self.on_ground}"
