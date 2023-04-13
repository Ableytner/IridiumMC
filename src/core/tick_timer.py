import uuid

_events = []

def add_event(ticks_remaining: int, callback) -> str:
    event_id = str(uuid.uuid4())
    _events.append([ticks_remaining, callback, event_id])
    return event_id

def remove_event(event_id: str) -> bool:
    c = 0
    while c < len(_events):
        if _events[c][2] == event_id:
            _events.pop(c)
            return True
        c += 1
    return False

def tick() -> None:
    c = 0
    while c < len(_events):
        _events[c][0] -= 1
        if _events[c][0] <= 0:
            _events[c][1]()
            _events.pop(c)
            c -= 1
        
        c += 1
