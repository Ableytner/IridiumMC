from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from entities.player_entity import PlayerEntity
    from core.iridium_server import IridiumServer

from core import binary_operations

class Packet:
    def __init__(self, data=None, stream=None):
        self.data = data
        self.stream = stream

class ClientPacket(Packet):
    """A packet that the client sends"""

    def load(self):
        raise NotImplementedError()

    def process(self, player: "PlayerEntity"):
        raise NotImplementedError()

class ServerPacket(Packet):
    """A packet that the server sends"""

    def reply(self, socket_conn, data=None):
        if data is None:
            data = self.data

        socket_conn.send(binary_operations._encode_varint(len(data)))
        socket_conn.send(data)
        # writer.drain()
