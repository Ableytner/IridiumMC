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

    def __init__(self, request: socket):
        self.socket = request

    def read_packet(self, packet_class=None) -> packet.Packet | int:
        packet_length = binary_operations._decode_varint(self.socket)
        packet_data = self.socket.recv(packet_length)
        packet_stream = ReadableBuffer(packet_data)
        packet_id = binary_operations._decode_varint(packet_stream)

        if packet_class is None:
            if packet_id not in client_packets.packet_id_map.keys():
                return packet_id
            packet_class = client_packets.packet_id_map[packet_id]

        if not issubclass(packet_class, packet.ClientPacket):
            raise TypeError(f"Tried to read packet of type {packet_class} which doesn't derive from {packet.ClientPacket}")

        logging.debug(f"Reading packet: {packet_class}")
        constr_packet = packet_class(data=packet_data, stream=packet_stream)
        constr_packet.load()
        return constr_packet

    def write_packet(self, constr_packet: packet.ServerPacket):
        if not isinstance(constr_packet, packet.ServerPacket):
            raise TypeError(f"Tried to write packet of type {type(constr_packet)} which doesn't derive from {packet.ServerPacket}")

        logging.debug(f"Writing packet: {type(constr_packet)}")
        constr_packet.reply(self.socket)

    def get_status(self, address, port):
        conn = handshake_packets.Handshake(address=address,
                               port=port,
                               next_state=STATUS_STATE)
        self.write_packet(conn)
        self.write_packet(status_packets.StatusRequest())
        status_response = self.read_packet(status_packets.StatusResponse)
        return status_response.json

    def handle_status(self, status_json: dict):
        self.read_packet(status_packets.StatusRequest)
        self.write_packet(status_packets.StatusResponse(status_json))
        conn_info = self.read_packet(status_packets.PingRequest)
        self.write_packet(status_packets.PingResponse(time=conn_info.time))

    def handle_login(self):
        conn_info = self.read_packet(login_packets.LoginStart)
        player_uuid = uuid.uuid4()
        self.write_packet(login_packets.LoginSuccess(conn_info.name, player_uuid))
        self.write_packet(server_packets.JoinGame())
        return (player_uuid, conn_info.name)

    def handle_server_keepalive(self): # !!! Needs rework !!!
        rand_int = random.randint(1, 1000)
        self.write_packet(server_packets.KeepAlive(rand_int))
        conn_info = self.read_packet(server_packets.KeepAlive)
        if rand_int != conn_info.rand_number:
            self.write_packet(server_packets.Disconnect("Timed out"))
