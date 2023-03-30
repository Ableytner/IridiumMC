import logging
import sys
import os
import base64
from datetime import datetime
from time import sleep
from threading import Thread
from socket import socket
from socketserver import ThreadingTCPServer

from packet_handlers import game_handler, player_handler
from network import handshake_packets, play_packets, client_packets
from network.protocol import MinecraftProtocol
from core.worldgen import WorldGenerator
from dataclass.save import World
from dataclass.position import Position
from dataclass.player import Player

TPS = 20

class IridiumServer():
    def __init__(self, port: int, path: str) -> None:
        self.port = port
        self.path = path
        self.server = None
        self.world = World(0)
        self.players: dict[str, Player] = {}
        IridiumServer.inst = self

        self._packet_handlers = {
            client_packets.Player: player_handler.player,
            client_packets.PlayerPosition: player_handler.player_position,
            client_packets.PlayerPositionAndLook: player_handler.player_position_and_look,
            client_packets.KeepAlivePacket: game_handler.keep_alive,
            client_packets.ChatMessagePacket: game_handler.chat_message
        }

    inst = None
    TPS = TPS

    def run_server(self):
        logging.info(f"IridiumMC server starting on port {self.port}")
        self.server = ThreadingTCPServer(("0.0.0.0", self.port), self.handle_client_connect)

        logging.info("creating world...")
        wg = WorldGenerator("flat", self.world)
        wg.generate_start_region(Position(0, 0, 0))
        logging.info(f"done")

        Thread(target=self.mainloop, daemon=True).start()
        self.server.serve_forever()

    def mainloop(self):
        while True:
            start_time = datetime.now()

            for player in self.players.values():
                self.handle_keepalive(player)

                while not player.network_in.empty():
                    conn_info = player.network_in.get()
                    if type(conn_info) in self._packet_handlers.keys():
                        self._packet_handlers[type(conn_info)](self, player, conn_info)

            sleep_time = (1 / TPS) - (datetime.now() - start_time).total_seconds()
            if sleep_time > 0:
                sleep(sleep_time)

    def handle_keepalive(self, player: Player):
        """Decrease keepalive timer, disconnect if timed out"""

        player.keepalive[1] -= 1
        if player.keepalive[1] <= 0 and player.keepalive[0] == 0:
            # send keepalive to client
            player.keepalive[0] = 1
            player.keepalive[1] = TPS * 5 # wait for 5 seconds to receive back keepalive
            ka_packet = play_packets.KeepAlivePacket()
            player.mcprot.write_packet(ka_packet)
            player.keepalive[2] = ka_packet.keep_alive_id
        if player.keepalive[1] <= 0 and player.keepalive[0] == 1:
            # player timed out returning the keepalive
            self.disconnect_player(player, "Timed out waiting for keepalive packet")

    @staticmethod
    def handle_client_connect(request: socket, client_address: tuple[str, int], server: ThreadingTCPServer) -> None:
        self = IridiumServer.inst
        logging.debug("Client connected!")

        mcprot = MinecraftProtocol(request)
        conn_info = mcprot.read_packet(handshake_packets.HandshakePacket)

        if conn_info.is_status_next():
            mcprot.handle_status(self.get_status())
            return
        elif conn_info.is_login_next():
            uuid, name = mcprot.handle_login()
            player = Player(self, uuid, name, Position(0, 10, 0), (0, 0), False, mcprot)
            logging.info(f"{name} joined the game")
            for pl in self.players.values():
                if pl.uuid != uuid:
                    pl.mcprot.write_packet(play_packets.ChatMesagePacket(f"{name} joined the game"))

            player.mcprot.write_packet(play_packets.PlayerPositionAndLook(player.pos, player.rot, player.on_ground))
            logging.debug("Generating chunk data...")
            chunk_gen_start_time = datetime.now()
            for x in range(-1, 2):
                for z in range(-1, 2):
                    chunk_data = self.world.to_packet_data(x, z)
                    player.mcprot.write_packet(play_packets.MapChunkBulkPacket(*chunk_data))
            logging.debug(f"Done, took {round((datetime.now() - chunk_gen_start_time).total_seconds(), 2)}s")
        else:
            logging.exception(f"unknown next_state {conn_info.next_state}")
            return

        self.players[str(uuid)] = player

        player.network_func()

    def disconnect_player(self, player: Player, reason: str = None):
        if reason is not None:
            player.mcprot.write_packet(play_packets.DisconnectPacket(reason))
        self.players.pop(str(player.uuid))
        logging.info(f"{player.name} left the game")
        for pl in self.players.values():
            pl.mcprot.write_packet(play_packets.ChatMesagePacket(f"{player.name} left the game"))

    def get_status(self) -> dict:
        image_path = "server/server-icon.png"
        dataurl = None
        if os.path.isfile(image_path):
            with open(image_path, "rb") as fb:
                binary_fc = fb.read()
            base64_utf8_str = base64.b64encode(binary_fc).decode('utf-8')
            file_ext = image_path.split('.')[-1]
            dataurl = f'data:image/{file_ext};base64,{base64_utf8_str}'

        status = {
            "version": {
                "name": "1.7.10",
                "protocol": handshake_packets.DEFAULT_PROTOCOL_VERSION
            },
            "players": {
                "max": 20,
                "online": len(self.players),
                "sample": []
            },
            "description": {
                "text": f"IridiumMC server! - Running with Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}!"
            },
            "favicon": dataurl or ""
        }
        return status
