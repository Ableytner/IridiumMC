import base64
import logging
import os
import sys
import traceback
from datetime import datetime
from socket import socket
from socketserver import ThreadingTCPServer
from threading import Thread
from time import sleep

from blocks import air
from core import tick_timer, server_provider
from core.worldgen import WorldGenerator
from dataclass import metadata
from dataclass.position import Position
from dataclass.rotation import Rotation
from dataclass.save import World
from entities.player_entity import PlayerEntity
from events.event_factory import EventFactory
from events.block_break_event import BlockBreakEvent
from network import handshake_packets, packet, server_packets
from network.protocol import MinecraftProtocol

TPS = 20
VIEW_DIST = 2

class IridiumServer():
    """The server core"""

    def __init__(self, port: int, path: str) -> None:
        self.port = port
        self.path = path
        self.server = None
        self.world = World(self, 0)
        self.world_gen = WorldGenerator("flat", self.world)
        self.players: dict[str, PlayerEntity] = {}
        server_provider._iridium_server = self

    TPS = TPS
    VIEW_DIST = VIEW_DIST

    def run_server(self):
        """Start the server"""

        logging.info(f"IridiumMC server starting on port {self.port}")
        self.server = ThreadingTCPServer(("0.0.0.0", self.port), self.handle_client_connect)

        logging.info("creating world...")
        self.world_gen.generate_start_region(Position(0, 0, 0))
        logging.info(f"done")

        # register the block break event
        EventFactory.register_callback(BlockBreakEvent, IridiumServer.break_block_callback)

        # start the game loop
        Thread(target=self.mainloop, daemon=True).start()
        self.server.serve_forever()

    def mainloop(self):
        """The game loop"""

        while True:
            start_time = datetime.now()

            for player in self.players.values():
                try:
                    self.handle_keepalive(player)

                    while not player.network_in.empty():
                        conn_info: packet.ClientPacket = player.network_in.get()
                        conn_info.process(player)

                    player.load_chunks(self.world)
                except OSError as oserr:
                    # player disconnected client-side
                    logging.debug(oserr)

            tick_timer.tick()

            sleep_time = (1 / TPS) - (datetime.now() - start_time).total_seconds()
            if sleep_time > 0:
                sleep(sleep_time)
            else:
                logging.warning(f"One tick took {int((datetime.now() - start_time).total_seconds() * 1000)} ms, is the server hanging?")

    @staticmethod
    def handle_client_connect(request: socket, client_address: tuple[str, int], server: ThreadingTCPServer) -> None:
        """Callback when a new client connects"""

        self = server_provider.get()
        logging.debug("Client connected!")

        mcprot = MinecraftProtocol(request)
        conn_info = mcprot.read_packet(handshake_packets.Handshake)

        if conn_info.is_status_next():
            mcprot.handle_status(self.get_status())
            return
        elif conn_info.is_login_next():
            uuid, name = mcprot.handle_login()
            # create a new player object
            player = PlayerEntity(uuid, name, self.VIEW_DIST, mcprot, health=20, position=Position(0, 10, 0), rotation=Rotation(0, 0), on_ground=False)
            logging.info(f"{name} joined the game")

            # send player joined message
            for pl in self.players.values():
                pl.mcprot.write_packet(server_packets.ChatMesage(f"{name} joined the game"))

            # send pos and rot to new player
            player.mcprot.write_packet(server_packets.PlayerPositionAndLook(player.position, player.rotation, player.on_ground))
        else:
            logging.exception(f"unknown next_state {conn_info.next_state}")
            return

        # send currently connected players chat message
        player.mcprot.write_packet(server_packets.ChatMesage("Players: " + ", ".join([item.name for item in self.players.values()] + [player.name])))

        for pl in self.players.values():
            # add new player to tab list
            pl.mcprot.write_packet(server_packets.PlayerListItem(player.name, True, 0))
            # add already connected player to tab list
            player.mcprot.write_packet(server_packets.PlayerListItem(pl.name, True, 0))

            # !!! not yet working !!!
            # should load new player if it is in render distance
            # test_player_data = binary_operations._encode_string("textures") + binary_operations._encode_string(base64.b64encode("textures".encode("ascii")).decode("ascii")) + binary_operations._encode_string(base64.b64encode("textures".encode("ascii")).decode("ascii"))
            # test_player_data2 = binary_operations._encode_string("t") + binary_operations._encode_string("a") + binary_operations._encode_string("s")
            player_metadata = metadata.Human(health=10).to_bytes() + metadata.STOP_BYTE
            if pl.pos.dist_to_horizontal(player.position) < self.VIEW_DIST:
                # pl.mcprot.write_packet(server_packets.SpawnPlayer(-1, str(player.uuid), player.name, test_player_data, player.pos, player.rot, 0, player_metadata)) 
                pass

        # add self to tab list
        player.mcprot.write_packet(server_packets.PlayerListItem(player.name, True, 0))

        self.players[str(uuid)] = player

        # player network loop
        player.network_func()

    def handle_keepalive(self, player: PlayerEntity):
        """Decrease keepalive timer, disconnect if timed out"""

        player.keepalive[1] -= 1
        if player.keepalive[1] <= 0 and player.keepalive[0] == 0:
            # send keepalive to client
            player.keepalive[0] = 1 # switch to SENT_TO_CLIENT
            player.keepalive[1] = TPS * 5 # wait for 5 seconds to receive back keepalive
            ka_packet = server_packets.KeepAlive()
            player.mcprot.write_packet(ka_packet)
            player.keepalive[2] = ka_packet.keep_alive_id # store keepalive_id
        if player.keepalive[1] <= 0 and player.keepalive[0] == 1:
            # player timed out sending back the keepalive
            self.disconnect_player(player, "Timed out waiting for keepalive packet")

    def generate_chunk(self, x: int, z: int) -> None:
        self.world_gen.generate_chunk_column(x, z)

    @staticmethod
    def break_block_callback(event: BlockBreakEvent):
        server_provider.get().world.set_block(event.position, air.Air())

    def disconnect_player(self, player: PlayerEntity, reason: str = None):
        """Cleanly disconnect the given player"""

        def callback(self, player, reason):
            if reason is None:
                reason = "Disconnected"
            player.mcprot.write_packet(server_packets.Disconnect(reason))

            self.players.pop(str(player.uuid))
            logging.info(f"{player.name} left the game")
            for pl in self.players.values():
                pl.mcprot.write_packet(server_packets.ChatMesage(f"{player.name} left the game"))
                pl.mcprot.write_packet(server_packets.PlayerListItem(player.name, False, 0))

        tick_timer.add_event(1, lambda: callback(self, player, reason))

    def get_status(self) -> dict:
        """Return a json-dict for the server list ping"""

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
