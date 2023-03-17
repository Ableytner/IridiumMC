from core import binary_operations

class Packet:
    def __init__(self, data=None, stream=None):
        self.data = data
        self.stream = stream

    async def load(self):
        raise NotImplementedError()

    async def reply(self, writer, data=None):
        if data is None:
            data = self.data

        writer.write(binary_operations._encode_varint(len(data)))
        writer.write(data)
        await writer.drain()
