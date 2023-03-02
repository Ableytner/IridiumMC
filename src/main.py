import asyncio
import logging
import os

from iridium_server import IridiumServer

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("asyncio").setLevel(logging.WARN)
    if os.name == 'nt':
        main_loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(main_loop)
    else:
        main_loop = asyncio.get_event_loop()

    if not os.path.isdir("server"):
        os.mkdir("server")

    server = IridiumServer(20003, "server")
    main_loop.run_until_complete(server.run_server())
    main_loop.run_forever()
