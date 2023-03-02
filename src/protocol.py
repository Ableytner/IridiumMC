import asyncio
import json
import logging
import struct

DEFAULT_PROTOCOL_VERSION = 47
STATUS_STATE = 1
LOGIN_STATE = 2

log = logging.getLogger(__name__)

class Packet:
    def __init__(self, data=None, stream=None):
        self.data = data
        self.stream = stream

    async def load(self):
        raise NotImplementedError()

    async def reply(self, writer, data=None):
        if data is None:
            data = self.data

        writer.write(_encode_varint(len(data)))
        writer.write(data)
        await writer.drain()

class HandshakePacket(Packet):
    def __init__(self, address=None, port=None, next_state=None, **kwargs):
        super().__init__(**kwargs)
        self.address = address
        self.port = port
        self.next_state = next_state
        self.protocol_version = DEFAULT_PROTOCOL_VERSION

    async def load(self):
        self.protocol_version = await _decode_varint(self.stream)
        self.address = await _decode_string(self.stream)
        self.port = await _decode_unsigned_short(self.stream)
        self.next_state = await _decode_varint(self.stream)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=_encode_varint(0) +
                                               _encode_varint(self.protocol_version) +
                                               _encode_string(self.address) +
                                               _encode_unsigned_short(self.port) +
                                               _encode_varint(self.next_state))

    def is_login_next(self):
        return self.next_state == 2

    def is_status_next(self):
        return self.next_state == 1


class StatusRequestPacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def load(self):
        pass

    async def reply(self, writer, data=None):
        await super().reply(writer, data=_encode_varint(0))


# noinspection PyAttributeOutsideInit
class StatusResponsePacket(Packet):
    def __init__(self, json_data=None, **kwargs):
        super().__init__(**kwargs)
        self.json = json_data

    async def load(self):
        json_str = await _decode_string(self.stream)
        self.json = json.loads(json_str)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=_encode_varint(0) +
                                               _encode_string(json.dumps(self.json)))

    @property
    def users(self):
        return self.json['players']['online']

    @users.setter
    def users(self, value):
        self.json['players']['online'] = value


class PingRequestPacket(Packet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.time = None

    async def load(self):
        self.time = await _decode_long(self.stream)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=_encode_varint(1) +
                                               _encode_long(self.time))


class PingResponsePacket(Packet):
    def __init__(self, time=None, **kwargs):
        super().__init__(**kwargs)
        self.time = time

    async def load(self):
        self.time = await _decode_long(self.stream)

    async def reply(self, writer, data=None):
        await super().reply(writer, data=_encode_varint(1) +
                                               _encode_long(self.time))


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
        log.debug("received: {}".format(data))


    async def read_packet(self, packet_class):
        packet_length = await _decode_varint(self._stream_reader)
        packet_data = await self._stream_reader.read(packet_length)
        packet_stream = asyncio.StreamReader()
        packet_stream.feed_data(packet_data)
        packet_id = (await _decode_varint(packet_stream))

        if packet_class is not None:
            log.debug("Loading packet class: {}".format(packet_class))
            packet = packet_class(data=packet_data, stream=packet_stream)
            await packet.load()
            return packet
        else:
            raise ValueError("Unknown packet id: {}".format(packet_id))

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
        conn = HandshakePacket(address=address,
                               port=port,
                               next_state=STATUS_STATE)
        yield from self.write_packet(conn)
        yield from self.write_packet(StatusRequestPacket())
        status_response = yield from self.read_packet(StatusResponsePacket)
        return status_response.json

    def handle_status(self, status_json):
        yield from self.read_packet(StatusRequestPacket)
        yield from self.write_packet(StatusResponsePacket(status_json))
        ping = yield from self.read_packet(PingRequestPacket)
        yield from self.write_packet(PingResponsePacket(time=ping.time))
        self.close()

    def close(self):
        if self._transport:
            self._transport.close()
        else:
            log.warn("No transport to close")


def _encode_varint(val):
    total = b''
    if val < 0:
        val = (1 << 32) + val
    while val >= 0x80:
        bits = val & 0x7F
        val >>= 7
        total += struct.pack('B', (0x80 | bits))
    bits = val & 0x7F
    total += struct.pack('B', bits)
    return total

async def _decode_varint(stream):
    total = 0
    shift = 0
    val = 0x80
    while val & 0x80:
        raw = await stream.read(1)
        val = struct.unpack('B', raw)[0]
        total |= ((val & 0x7F) << shift)
        shift += 7
        if total & (1 << 31):
            total = total - (1 << 32)
    return total

async def _decode_string(stream):
    varint = await _decode_varint(stream)
    b = await stream.read(varint)
    return b.decode(encoding='UTF-8')

def _encode_string(value):
    data = value.encode('utf-8')
    # noinspection PyArgumentList
    return _encode_varint(len(data)) + data

def _encode_unsigned_short(value):
    return struct.pack('>H', value)

async def _decode_unsigned_short(stream):
    raw_bytes = await stream.read(2)
    return struct.unpack('>H', raw_bytes)[0]

def _encode_long(value):
    return struct.pack('>q', value)

async def _decode_long(stream):
    raw_bytes = await stream.read(8)
    return struct.unpack('>q', raw_bytes)[0]
