"""A module containing the ReadableBuffer class"""

# pylint: disable=R0903

class ReadableBuffer():
    """A class for reading a bytes object bit by bit"""

    def __init__(self, data: bytes) -> None:
        self.data = data

    def recv(self, buffsize: int) -> bytes:
        """Slice off and return the requestet amount ob bytes"""

        sliced_data = self.data[0:buffsize]
        self.data = self.data[buffsize:]
        return sliced_data
