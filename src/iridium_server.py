import asyncio
import logging
import socket
import json
import os

from protocol import MinecraftProtocol, HandshakePacket, StatusRequestPacket, StatusResponsePacket

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

        print(f"IridiumMC server starting on port {self.port}...\n", end="")
        self.server = await asyncio.start_server(handle_client_task, host="192.168.0.154", port=self.port)

    async def _handle_client(self, client_reader: asyncio.StreamReader, client_writer: asyncio.StreamWriter):
        print("Client connected!")

        # print(self._parse_handshake(await client_reader.read()))

        mcprot = MinecraftProtocol(client_reader, client_writer)
        conn_info = await mcprot.read_packet(StatusRequestPacket)
        await conn_info.load()
        
        status = {
            "version": {
                "name": "1.12.2",
                "protocol": 759
            },
        }
        await mcprot.write_packet(StatusResponsePacket(status))

    def _parse_handshake(self, request) -> dict:
        data = {}

        request = bytearray(request)

        packet_len = int(request[0])

        protocol_version = request[2:4]
        protocol_version = int.from_bytes(protocol_version)
        print(protocol_version)

        address = request[5:packet_len-2]
        data["address"] = address.decode()

        port = request[packet_len-2:packet_len]
        data["port"] = int.from_bytes(port)

        data["next_state"] = int(request[packet_len])

        return data

    def _build_status(self) -> bytes:
        data = binary_helpers._encode_varint(0)

        status = {
            "version": {
                "name": "1.19",
                "protocol": 759
            },
        }
        status = json.dumps(status)
        data += binary_helpers._encode_string(status)

        return binary_helpers._encode_varint(len(data)) + data

    def _build_disconnect(self) -> bytes:
        data = binary_helpers._encode_varint(0)

        message = {
            "text": "Server starting. Try again in a few minutes",
            "bold": True,
            "color": "dark_green",
        }
        message = json.dumps(message)
        data += binary_helpers._encode_string(message)

        return binary_helpers._encode_varint(len(data)) + data
