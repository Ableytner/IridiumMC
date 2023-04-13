import logging
import random
from time import sleep
import uuid
from socket import socket

from core import binary_operations
from core.readable_buffer import ReadableBuffer
from network import packet, handshake_packets, server_packets, status_packets, login_packets, client_packets

STATUS_STATE = 1
LOGIN_STATE = 2

class MinecraftProtocol():
    _transport = None

    def __init__(self, request: socket) -> None:
        self.socket = request

    def read_packet(self, packet_class=None) -> packet.Packet | int:
        """Read, load and return a packet"""

        packet_length = binary_operations._decode_varint(self.socket)
        packet_data = self.socket.recv(packet_length)
        packet_stream = ReadableBuffer(packet_data)
        packet_id = binary_operations._decode_varint(packet_stream)

        if packet_class is None:
            if packet_id not in client_packets.packet_id_map.keys():
                # the packet wasn't found, return its id
                return packet_id
            packet_class = client_packets.packet_id_map[packet_id]

        if not issubclass(packet_class, packet.ClientPacket):
            raise TypeError(f"Tried to read packet of type {packet_class} which doesn't derive from {packet.ClientPacket}")

        logging.debug(f"Reading packet: {packet_class}")
        constr_packet = packet_class(data=packet_data, stream=packet_stream)
        constr_packet.load()
        return constr_packet

    def write_packet(self, constr_packet: packet.ServerPacket) -> None:
        """Write a packet to the client"""

        if not isinstance(constr_packet, packet.ServerPacket):
            raise TypeError(f"Tried to write packet of type {type(constr_packet)} which doesn't derive from {packet.ServerPacket}")

        logging.debug(f"Writing packet: {type(constr_packet)}")
        constr_packet.reply(self.socket)

    def handle_status(self, status_json: dict) -> None:
        """Handle the server list ping"""

        self.read_packet(status_packets.StatusRequest)
        self.write_packet(status_packets.StatusResponse(status_json))
        conn_info = self.read_packet(status_packets.PingRequest)
        self.write_packet(status_packets.PingResponse(time=conn_info.time))

    def handle_login(self) -> tuple[uuid.UUID, str]:
        """Handle client login"""

        conn_info = self.read_packet(login_packets.LoginStart)
        player_uuid = uuid.uuid4()
        self.write_packet(login_packets.LoginSuccess(conn_info.name, player_uuid))
        self.write_packet(server_packets.JoinGame())
        return (player_uuid, conn_info.name)
