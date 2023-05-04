class ReadableBuffer():
    def __init__(self, data: bytes) -> None:
        self.data = data
    
    def recv(self, buffsize: int) -> bytes:
        slice = self.data[0:buffsize]
        self.data = self.data[buffsize:]
        return slice
