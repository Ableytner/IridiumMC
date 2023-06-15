from threading import Thread
from time import sleep

import pytest

@pytest.fixture
def server():
    import main
    Thread(target=main.run, daemon=True).start()
    sleep(0.5)
    yield "localhost:20003"
