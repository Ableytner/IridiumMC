"""Packets sent by the client"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.iridium_server import IridiumServer

from core import server_provider
from entities.player_entity import PlayerEntity
from dataclass.position import Position
from network import handshake_packets, client_packets, server_packets
from core import binary_operations
from events.event_factory import EventFactory
from events import block_break_event
from network.packet import ClientPacket
from events.block_break_event import BlockBreakEvent
from blocks import air

class KeepAlive(ClientPacket): # 0x00
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.keep_alive_id = binary_operations._decode_int(self.stream)

    def process(self, player: PlayerEntity):
        if self.keep_alive_id == player.keepalive[2]:
            player.keepalive[0] = 0 # switch to WAITING
            player.keepalive[1] = server_provider.get().TPS * 5 # wait for 5 seconds until next keepalive
            player.keepalive[2] = 0
        else:
            # client sent back the wrong keepalive_id
            server_provider.get().disconnect_player(player, "KeepAliveID is incorrect")

class ChatMessage(ClientPacket): # 0x01
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.message = binary_operations._decode_string(self.stream)

    def process(self, player: PlayerEntity):
        logging.info(f"[{player.name}] {self.message}")
        for pl in server_provider.get().players.values():
            pl.mcprot.write_packet(server_packets.ChatMesage(f"[{player.name}] {self.message}"))

class PlayerP(ClientPacket):  # 0x03 PlayerOnGround
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.on_ground = binary_operations._decode_boolean(self.stream)

    def process(self, player: PlayerEntity):
        player.on_ground = self.on_ground

class PlayerPosition(ClientPacket): # 0x04
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.x = binary_operations._decode_double(self.stream)
        self.feety = binary_operations._decode_double(self.stream)
        self.heady = binary_operations._decode_double(self.stream)
        self.z = binary_operations._decode_double(self.stream)
        self.on_ground = binary_operations._decode_boolean(self.stream)

    def process(self, player: PlayerEntity):
        player.pos = Position(self.x, self.heady, self.z)
        player.on_ground = self.on_ground

class PlayerLook(ClientPacket): # 0x05
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.yaw = binary_operations._decode_float(self.stream)
        self.pitch = binary_operations._decode_float(self.stream)
        self.on_ground = binary_operations._decode_boolean(self.stream)

    def process(self, player: PlayerEntity):
        player.rot = (self.yaw, self.pitch)
        player.on_ground = self.on_ground

class PlayerPositionAndLook(ClientPacket): # 0x06
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.x = binary_operations._decode_double(self.stream)
        self.feety = binary_operations._decode_double(self.stream)
        self.heady = binary_operations._decode_double(self.stream)
        self.z = binary_operations._decode_double(self.stream)
        self.yaw = binary_operations._decode_float(self.stream)
        self.pitch = binary_operations._decode_float(self.stream)
        self.on_ground = binary_operations._decode_boolean(self.stream)

    def process(self, player: PlayerEntity):
        player.pos = Position(self.x, self.heady, self.z)
        player.rot = (self.yaw, self.pitch)
        player.on_ground = self.on_ground

class PlayerDigging(ClientPacket): # 0x07
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        # 0: Started digging
        # 1: Cancelled digging
        # 2: Finished digging
        # 3: Drop item stack
        # 4: Drop item
        # 5: Shoot arrow / finish eating
        self.status = binary_operations._decode_byte(self.stream)
        self.x = binary_operations._decode_int(self.stream)
        self.y = binary_operations._decode_unsigned_byte(self.stream)
        self.z = binary_operations._decode_int(self.stream)
        self.face = binary_operations._decode_byte(self.stream)

    def process(self, player: PlayerEntity):
        if self.status == 2:
            block_pos = Position(self.x, self.y, self.z)
            block = server_provider.get().world.get_block(block_pos)
            EventFactory.call(block_break_event.BlockBreakEvent(player, block, block_pos))

    @staticmethod
    def break_block_callback(event: BlockBreakEvent):
        self = server_provider.get()
        self.world.set_block(event.position, air.Air())
        for uuid, player in self.players.items():
            if uuid != str(event.player.uuid) and player.position.dist_to_horizontal(event.player.position) <= player.view_dist:
                player.mcprot.write_packet(server_packets.BlockChange(event.position, air.Air.block_id, 0x00000000))

class ClientSettings(ClientPacket): # 0x15
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.locale = binary_operations._decode_string(self.stream)
        self.view_distance = binary_operations._decode_byte(self.stream)
        self.chat_flags = binary_operations._decode_byte(self.stream)
        self.chat_colors = binary_operations._decode_boolean(self.stream)
        self.difficulty = binary_operations._decode_byte(self.stream)
        self.show_cape = binary_operations._decode_boolean(self.stream)

    def process(self, player: PlayerEntity):
        if self.view_distance <= server_provider.get().VIEW_DIST:
            player.view_dist = self.view_distance
        else:
            player.view_dist = server_provider.get().VIEW_DIST

class PluginMessage(ClientPacket): # 0x17
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.channel = binary_operations._decode_string(self.stream)
        self.length = binary_operations._decode_short(self.stream)
        self.data = binary_operations._decode_bytearray(self.stream, self.length)

    def process(self, player: PlayerEntity):
        pass

class Animation(ClientPacket): # 0x0A
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.entity_id = binary_operations._decode_int(self.stream)
        self.animation_id = binary_operations._decode_byte(self.stream)
        # 0: No animation
        # 1: Swing arm
        # 2: Damage animation
        # 3: Leave bed
        # 5: Eat food
        # 6: Critical effect
        # 7: Magic critical effect
        # 102: (unknown)
        # 104: Crouch
        # 105: Uncrouch

    def process(self, player: PlayerEntity):
        pass

class EntityAction(ClientPacket): # 0x0B
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def load(self):
        self.entity_id = binary_operations._decode_int(self.stream)
        self.action_id = binary_operations._decode_byte(self.stream)
        self.jump_boost = binary_operations._decode_int(self.stream)

    def process(self, player: PlayerEntity):
        pass

packet_id_map = {
    0x00: KeepAlive,
    0x01: ChatMessage,
    0x03: PlayerP,
    0x04: PlayerPosition,
    0x05: PlayerLook,
    0x06: PlayerPositionAndLook,
    0x07: PlayerDigging,
    0x15: ClientSettings,
    0x17: PluginMessage,
    0x0A: Animation,
    0x0B: EntityAction
}
