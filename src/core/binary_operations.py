import struct

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

def _encode_string(value):
    data = value.encode('utf-8')
    # noinspection PyArgumentList
    return _encode_varint(len(data)) + data

async def _decode_string(stream):
    varint = await _decode_varint(stream)
    b = await stream.read(varint)
    return b.decode(encoding='UTF-8')

def _encode_unsigned_short(value):
    return struct.pack('>H', value)

async def _decode_unsigned_short(stream):
    raw_bytes = await stream.read(2)
    return struct.unpack('>H', raw_bytes)[0]

def _encode_short(value):
    return struct.pack('>h', value)

async def _decode_short(stream):
    raw_bytes = await stream.read(2)
    return struct.unpack('>h', raw_bytes)[0]

def _encode_int(value):
    return struct.pack('>i', value)

async def _decode_int(stream):
    raw_bytes = await stream.read(4)
    return struct.unpack('>i', raw_bytes)[0]

def _encode_long(value):
    return struct.pack('>q', value)

async def _decode_long(stream):
    raw_bytes = await stream.read(8)
    return struct.unpack('>q', raw_bytes)[0]

def _encode_boolean(value):
    return struct.pack('>?', value)

async def _decode_boolean(stream):
    raw_bytes = await stream.read(1)
    return struct.unpack('>?', raw_bytes)[0]

def _encode_unsigned_byte(value):
    return struct.pack('>B', value)

async def _decode_unsigned_byte(stream):
    raw_bytes = await stream.read(1)
    return struct.unpack('>B', raw_bytes)[0]

def _encode_byte(value):
    return struct.pack('>b', value)

async def _decode_byte(stream):
    raw_bytes = await stream.read(1)
    return struct.unpack('>b', raw_bytes)[0]
