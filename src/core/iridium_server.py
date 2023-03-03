import asyncio
import logging
import time
import json
import os
import traceback
from time import sleep

from network.protocol import MinecraftProtocol
from network.packets import HandshakePacket, ChunkDataPacket
from core.worldgen import WorldGenerator
from dataclass.save import World
from dataclass.position import Position

BUFFER_SIZE = 65536

class IridiumServer():
    def __init__(self, port: int, path: str) -> None:
        self.port = port
        self.path = path
        self.server = None
        self.exit = False

    async def run_server(self):
        def handle_client_task(client_reader, client_writer):
            asyncio.run_coroutine_threadsafe(self._handle_client(client_reader=client_reader,
                                             client_writer=client_writer), asyncio.get_event_loop())

        logging.info(f"IridiumMC server starting on port {self.port}")
        self.server = await asyncio.start_server(handle_client_task, host="192.168.0.154", port=self.port)

    async def _handle_client(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter):
        logging.debug("Client connected!")

        mcprot = MinecraftProtocol(client_reader, client_writer)
        conn_info = await mcprot.read_packet(HandshakePacket)

        if conn_info.is_status_next():
            await mcprot.handle_status(self.get_status())
            return
        elif conn_info.is_login_next():
            logging.debug("Login...")
            await mcprot.handle_login()
            logging.debug("finished login")

            logging.info("creating world...")
            try:
                w = World(0)
                wg = WorldGenerator("flat", w)
                wg.generate_start_region(Position(0, 0, 0))
                await mcprot.write_packet(ChunkDataPacket(*wg.world.chunks[0][0].to_packet_data()))
            except Exception:
                print(traceback.format_exc())
            logging.info(f"done, created {len(wg.world.chunks)} chunks")
            logging.info(f"player spawn block: {wg.world.chunks[-32][16].blocks[14][10][3]}")
        else:
            logging.exception(f"unknown next_state {conn_info.next_state}")

    def get_status(self):
        retr_time = time.time()
        status = {
            "online": False,
            "host": "ableytner.ddns.net",
            "port": self.port,
            "eula_blocked": False,
            "retrieved_at": int(retr_time),
            "expires_at": int(retr_time) + 6000,
            "version": {
                "name_raw": "1.7.10",
                "name_clean": "1.7.10",
                "name_html": "<span><span style=\"color: #ffffff;\">1.7.10</span></span>",
                "protocol": 5
            },
            "players": {
                "online": 0,
                "max": 20,
                "list": []
            },
            "motd": {
                "raw": "IridiumMC server!",
                "clean": "IridiumMC server!",
                "html": "<span><span style=\"color: #ffffff;\">IridiumMC server! </span>"
            },
            "icon": None,
            "mods": [],
        }
        return status
