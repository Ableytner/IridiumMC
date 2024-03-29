"""Packets sent by the server"""

import json
import random
import math

from core import binary_operations
from dataclass.position import Position
from dataclass.rotation import Rotation
from network.packet import ServerPacket

packet_id_map: dict

class KeepAlive(ServerPacket): # 0x00
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.keep_alive_id = random.randint(0, math.pow(2, 31) - 1)

    def reply(self, socket_conn):
        super().reply(socket_conn, data=binary_operations._encode_varint(0x00) +
                                         binary_operations._encode_int(self.keep_alive_id)) # random integer

class JoinGame(ServerPacket): # 0x01
    def __init__(self, entity_id: int, gamemode: int, dim_id: int, difficulty: int, max_players: int, level_type: str, **kwargs):
        super().__init__(**kwargs)
        self.entity_id = entity_id
        self.gamemode = gamemode
        self.dim_id = dim_id
        self.difficulty = difficulty
        self.max_players = max_players
        self.level_type = level_type

    def reply(self, socket_conn):
        super().reply(socket_conn, data=binary_operations._encode_varint(0x01) +
                                         binary_operations._encode_int(self.entity_id) + # player entity id
                                         binary_operations._encode_unsigned_byte(self.gamemode) + # gamemode, 0=survival, 1=creative
                                         binary_operations._encode_byte(self.dim_id) + # dimension, -1=nether, 0=overworld, 1=end
                                         binary_operations._encode_unsigned_byte(self.difficulty) + # difficulty, 0=peaceful
                                         binary_operations._encode_unsigned_byte(self.max_players) + # max players
                                         binary_operations._encode_string(self.level_type)) # level type

class ChatMesage(ServerPacket): # 0x02
    def __init__(self, message: str|dict, **kwargs):
        super().__init__(**kwargs)
        if isinstance(message, dict):
            self.message = json.dumps(message)
        else:
            self.message = json.dumps({
                "text": message
            })

    def reply(self, socket_conn):
        super().reply(socket_conn, data=binary_operations._encode_varint(0x02) +
                                         binary_operations._encode_string(self.message))

class SpawnPosition(ServerPacket): # 0x05
    def __init__(self, position: Position, **kwargs):
        super().__init__(**kwargs)
        self.position = position

    def reply(self, socket_conn):
        super().reply(socket_conn, data=binary_operations._encode_varint(0x05) +
                                         binary_operations._encode_int(self.position.x) +
                                         binary_operations._encode_int(self.position.y) +
                                         binary_operations._encode_int(self.position.z))

class PlayerPositionAndLook(ServerPacket): # 0x08
    def __init__(self, position: Position, look: Rotation, on_ground: bool, **kwargs):
        super().__init__(**kwargs)
        self.position = position
        self.look = look
        self.on_ground = on_ground

    def reply(self, socket_conn):
        super().reply(socket_conn, data=binary_operations._encode_varint(0x08) +
                                         binary_operations._encode_double(self.position.x) +
                                         binary_operations._encode_double(self.position.y) +
                                         binary_operations._encode_double(self.position.z) +
                                         binary_operations._encode_float(self.look.yaw) +
                                         binary_operations._encode_float(self.look.pitch) +
                                         binary_operations._encode_boolean(self.on_ground))

class BlockChange(ServerPacket): # 0x23
    def __init__(self, position: Position, block_id: int, metadata: bytes, **kwargs):
        super().__init__(**kwargs)
        self.position = position
        self.block_id = block_id
        self.metadata = metadata

    def reply(self, socket_conn):
        super().reply(socket_conn, data=binary_operations._encode_varint(0x23) +
                                         binary_operations._encode_int(self.position.x) +
                                         binary_operations._encode_unsigned_byte(self.position.y) +
                                         binary_operations._encode_int(self.position.z) +
                                         binary_operations._encode_varint(self.block_id) +
                                         binary_operations._encode_unsigned_byte(self.metadata))

class MapChunkBulk(ServerPacket): # 0x26
    def __init__(self, chunk_column_count: int, data_len: int, sky_light: bool, data: bytes, metadata: bytes, **kwargs):
        super().__init__(**kwargs)
        self.chunk_column_count = chunk_column_count
        self.data_len = data_len
        self.sky_light = sky_light
        self.data = data
        self.metadata = metadata

    def reply(self, socket_conn):
        super().reply(socket_conn, data=binary_operations._encode_varint(0x26) +
                                         binary_operations._encode_short(self.chunk_column_count) +
                                         binary_operations._encode_int(self.data_len) +
                                         binary_operations._encode_boolean(self.sky_light) +
                                         self.data +
                                         self.metadata)

class PlayerListItem(ServerPacket): # 0x38
    def __init__(self, player_name: str, online: bool, ping: int, **kwargs):
        super().__init__(**kwargs)
        self.player_name = player_name
        self.online = online
        self.ping = ping

    def reply(self, socket_conn):
        super().reply(socket_conn, data=binary_operations._encode_varint(0x38) +
                                        binary_operations._encode_string(self.player_name) +
                                        binary_operations._encode_boolean(self.online) +
                                        binary_operations._encode_short(self.ping))

class Disconnect(ServerPacket): # 0x40
    def __init__(self, reason: str|dict, **kwargs):
        super().__init__(**kwargs)
        if isinstance(reason, dict):
            self.reason = json.dumps(reason)
        else:
            self.reason = json.dumps({
                "text": reason
            })

    def reply(self, socket_conn):
        super().reply(socket_conn, data=binary_operations._encode_varint(0x40) +
                                        binary_operations._encode_string(self.reason))

class SpawnPlayer(ServerPacket): #0x0C
    def __init__(self, entity_id: int, player_uuid: str, player_name: str, data: bytes, pos: Position, rot: Rotation, current_item: int, metadata: bytes, **kwargs):
        super().__init__(**kwargs)
        self.entity_id = entity_id
        self.player_uuid = player_uuid
        self.player_name = player_name
        self.data = data
        self.pos = pos
        self.rot = rot
        self.current_item = current_item
        self.metadata = metadata

    def reply(self, socket_conn):
        super().reply(socket_conn, data=binary_operations._encode_varint(0x0C) +
                                        binary_operations._encode_varint(self.entity_id) +
                                        binary_operations._encode_string(self.player_uuid) +
                                        binary_operations._encode_string(self.player_name) +
                                        binary_operations._encode_varint(len(self.data)) +
                                        self.data +
                                        binary_operations._encode_int(int(self.pos.x * 32)) + # positions as fixed-point numbers
                                        binary_operations._encode_int(int(self.pos.y * 32)) +
                                        binary_operations._encode_int(int(self.pos.z * 32)) +
                                        binary_operations._encode_byte(self.rot.yaw) +
                                        binary_operations._encode_byte(self.rot.pitch) +
                                        binary_operations._encode_short(self.current_item) +
                                        self.metadata)
