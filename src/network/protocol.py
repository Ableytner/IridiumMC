import asyncio
import logging
import random
import uuid

from core import binary_operations
from network import packet, handshake_packets, status_packets, login_packets, play_packets, client_packets

STATUS_STATE = 1
LOGIN_STATE = 2

log = logging.getLogger(__name__)

class MinecraftProtocol(asyncio.StreamReaderProtocol):
    _transport = None

    def __init__(self, stream_reader, stream_writer=None, on_status=None, client_connected_cb=None,
                 loop=None):
        super().__init__(stream_reader, client_connected_cb, loop)
        if stream_writer:
            self._stream_writer = stream_writer
        self.on_status = on_status

    def data_received(self, data):
        super().data_received(data)
        logging.debug("received: {}".format(data))

    async def read_packet(self, packet_class=None) -> packet.Packet | None:
        packet_length = await binary_operations._decode_varint(self._stream_reader)
        packet_data = await self._stream_reader.read(packet_length)
        packet_stream = asyncio.StreamReader()
        packet_stream.feed_data(packet_data)
        packet_id = (await binary_operations._decode_varint(packet_stream))

        if packet_class is None:
            if packet_id not in client_packets.packet_id_map.keys():
                logging.error(f"Unknown packet id: {packet_id}")
                await self.write_packet(play_packets.DisconnectPacket(f"Unknown packet id: {packet_id}"))
                return None
            packet_class = client_packets.packet_id_map[packet_id]

        logging.debug("Loading packet class: {}".format(packet_class))
        packet = packet_class(data=packet_data, stream=packet_stream)
        await packet.load()
        return packet

    async def write_packet(self, packet):
        await packet.reply(self._stream_writer)

    def connection_made(self, transport):
        super().connection_made(transport)
        self._transport = transport
        self._stream_writer = asyncio.StreamWriter(transport, self, self._stream_reader, asyncio.get_event_loop())

    def connection_lost(self, exc):
        super().connection_lost(exc)
        self._transport = None

    def get_status(self, address, port):
        conn = handshake_packets.HandshakePacket(address=address,
                               port=port,
                               next_state=STATUS_STATE)
        yield from self.write_packet(conn)
        yield from self.write_packet(status_packets.StatusRequestPacket())
        status_response = yield from self.read_packet(status_packets.StatusResponsePacket)
        return status_response.json

    def handle_status(self, status_json):
        yield from self.read_packet(status_packets.StatusRequestPacket)
        yield from self.write_packet(status_packets.StatusResponsePacket(status_json))
        ping = yield from self.read_packet(status_packets.PingRequestPacket)
        yield from self.write_packet(status_packets.PingResponsePacket(time=ping.time))
        self.close()

    async def handle_login(self):
        conn_info = await self.read_packet(login_packets.LoginStartPacket)
        player_uuid = uuid.uuid4()
        await self.write_packet(login_packets.LoginSuccessPacket(conn_info.name, player_uuid))
        await self.write_packet(play_packets.JoinGamePacket())
        return (player_uuid, conn_info.name)

    async def handle_server_keepalive(self):
        rand_int = random.randint(1, 1000)
        await self.write_packet(play_packets.KeepAlivePacket(rand_int))
        conn_info = await self.read_packet(play_packets.KeepAlivePacket)
        if rand_int != conn_info.rand_number:
            await self.write_packet(play_packets.DisconnectPacket("Timed out"))

    def close(self):
        if self._transport:
            self._transport.close()
        else:
            logging.warn("No transport to close")
