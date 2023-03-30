import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.iridium_server import IridiumServer
from network import handshake_packets, play_packets, client_packets
from dataclass.player import Player

def keep_alive(server: "IridiumServer", player: Player, conn_info: client_packets.KeepAlivePacket):
    if conn_info.keep_alive_id == player.keepalive[2]:
        player.keepalive[0] = 0
        player.keepalive[1] = server.TPS * 5 # wait for 5 seconds until next keepalive
        player.keepalive[2] = 0
    else:
        player.mcprot.write_packet(play_packets.DisconnectPacket("KeepAliveID is incorrect"))

def chat_message(server: "IridiumServer", player: Player, conn_info: client_packets.KeepAlivePacket):
    logging.info(f"[{player.name}] {conn_info.message}")
    for pl in server.players.values():
        pl.mcprot.write_packet(play_packets.ChatMesagePacket(f"[{player.name}] {conn_info.message}"))
