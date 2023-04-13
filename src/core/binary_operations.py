import struct

def bools_to_binary(vals: list[bool]) -> bytes:
    inp = [True, True, True, False, False, True, False, False, False, True]
    outp = 0
    c = len(inp) - 1
    for val in inp:
        outp += (int(val) << c)
        c -= 1
    return _encode_byte(bin(outp).removeprefix("0b"))

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

def _decode_varint(socket_conn):
    total = 0
    shift = 0
    val = 0x80
    while val & 0x80:
        raw = socket_conn.recv(1)
        val = struct.unpack('B', raw)[0]
        total |= ((val & 0x7F) << shift)
        shift += 7
        if total & (1 << 31):
            total = total - (1 << 32)
    return total

def _encode_string(value) -> bytes:
    data = value.encode('utf-8')
    # noinspection PyArgumentList
    return _encode_varint(len(data)) + data

def _decode_string(socket_conn) -> str:
    varint = _decode_varint(socket_conn)
    b = socket_conn.recv(varint)
    return b.decode(encoding='UTF-8')

def _encode_unsigned_short(value) -> bytes:
    return struct.pack('>H', value)

def _decode_unsigned_short(socket_conn) -> int:
    raw_bytes = socket_conn.recv(2)
    return struct.unpack('>H', raw_bytes)[0]

def _encode_short(value) -> bytes:
    return struct.pack('>h', value)

def _decode_short(socket_conn) -> int:
    raw_bytes = socket_conn.recv(2)
    return struct.unpack('>h', raw_bytes)[0]

def _encode_int(value) -> bytes:
    return struct.pack('>i', value)

def _decode_int(socket_conn) -> int:
    raw_bytes = socket_conn.recv(4)
    return struct.unpack('>i', raw_bytes)[0]

def _encode_long(value) -> bytes:
    return struct.pack('>q', value)

def _decode_long(socket_conn) -> int:
    raw_bytes = socket_conn.recv(8)
    return struct.unpack('>q', raw_bytes)[0]

def _encode_float(value) -> bytes:
    return struct.pack('>f', value)

def _decode_float(socket_conn):
    raw_bytes = socket_conn.recv(4)
    return struct.unpack('>f', raw_bytes)[0]

def _encode_double(value) -> bytes:
    return struct.pack('>d', value)

def _decode_double(socket_conn):
    raw_bytes = socket_conn.recv(8)
    return struct.unpack('>d', raw_bytes)[0]

def _encode_boolean(value) -> bytes:
    return struct.pack('>?', value)

def _decode_boolean(socket_conn) -> bool:
    raw_bytes = socket_conn.recv(1)
    return struct.unpack('>?', raw_bytes)[0]

def _encode_unsigned_byte(value) -> bytes:
    return struct.pack('>B', value)

def _decode_unsigned_byte(socket_conn) -> int:
    raw_bytes = socket_conn.recv(1)
    return struct.unpack('>B', raw_bytes)[0]

def _encode_byte(value) -> bytes:
    return struct.pack('>b', value)

def _decode_byte(socket_conn) -> int:
    raw_bytes = socket_conn.recv(1)
    return struct.unpack('>b', raw_bytes)[0]

def _encode_nibbles(a, b) -> bytes:
    return ((a << 4) + b).to_bytes(1, byteorder='big')

def _decode_nibbles(socket_conn) -> tuple[int, int]:
    raw_bytes = socket_conn.recv(1)
    a = int.from_bytes(raw_bytes, byteorder="big") >> 4
    return (a, int.from_bytes(raw_bytes, byteorder="big") - (a << 4))

def _encode_bytearray(value: list[bytes]) -> tuple[int, bytes]:
    x = b""
    for y in value:
        x += y
    return (len(value), x)

def _decode_bytearray(socket_conn, length: int) -> list[bytes]:
    x = []
    for _ in range(length):
        x.append(socket_conn.recv(1))
    return x

def _encode_metakey(key, typ) -> bytes:
    return ((key << 5) + typ).to_bytes(1, byteorder='big')

def _decode_metakey(socket_conn) -> tuple[int, int]:
    raw_bytes = socket_conn.recv(1)
    a = int.from_bytes(raw_bytes, byteorder="big") >> 3
    return (a, int.from_bytes(raw_bytes, byteorder="big") - (a << 3))
