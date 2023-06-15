import logging
import os

from core.iridium_server import IridiumServer

LOGGING_LEVEL = logging.INFO

def run():
    logging.basicConfig(level=LOGGING_LEVEL)

    if not os.path.isdir("server"):
        os.mkdir("server")

    server = IridiumServer(20003, "server")
    server.run_server()

if __name__ == '__main__':
    run()
