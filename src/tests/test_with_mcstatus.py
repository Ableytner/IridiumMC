import mcstatus

def test_server_ping(server):
    mcserver = mcstatus.JavaServer(server.split(":")[0], int(server.split(":")[1]))
    assert mcserver.ping()

def test_server_status(server):
    mcserver = mcstatus.JavaServer(server.split(":")[0], int(server.split(":")[1]))
    status = mcserver.status()
    assert status.latency
    assert status.version.name == "1.7.10"
