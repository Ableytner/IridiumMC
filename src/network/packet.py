from core import binary_operations

class Packet:
    def __init__(self, data=None, stream=None):
        self.data = data
        self.stream = stream

    def load(self):
        # raise NotImplementedError()
        pass

    def reply(self, socket, data=None):
        if data is None:
            data = self.data

        socket.send(binary_operations._encode_varint(len(data)))
        socket.send(data)
        # writer.drain()
