from events.event import Event
from entities.entity import Entity

class EventFactory():
    def __init__(self) -> None:
        self._callbacks = {}
    
    def register_callback(self, event_type: type, callback):
        """Add a callback for a given event type"""

        if not isinstance(event_type, type):
            raise TypeError()

        if not issubclass(event_type, Event):
            raise TypeError(f"Tried to register a callback to event type {event_type}, which doesn't derive from {Event}")

        if not event_type in self._callbacks.keys():
            self._callbacks[event_type] = []
        self._callbacks[event_type].append(callback)

    def call(self, caller: Entity, event: Event):
        """Call all callbacks with the caller and event as parameters"""

        for callback in self._callbacks[type(event)]:
            callback(caller, event)
