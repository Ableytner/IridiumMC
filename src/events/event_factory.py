import logging

from events.event import Event

class EventFactory():
    _callbacks = {}

    @classmethod
    def register_callback(cls, event_type: type, callback):
        """Add a callback for a given event type"""

        if not isinstance(event_type, type):
            raise TypeError()

        if not issubclass(event_type, Event):
            raise TypeError(f"Tried to register a callback to event type {event_type}, which doesn't derive from {Event}")

        if not event_type in cls._callbacks.keys():
            cls._callbacks[event_type] = []
        cls._callbacks[event_type].append(callback)

    @classmethod
    def call(cls, event: Event):
        """Call all callbacks with the event as the parameter"""

        logging.info(f"Called event {type(event)}")

        if type(event) not in cls._callbacks.keys():
            logging.warning(f"Event {type(event)} was raised, but has no associated callbacks")
            return

        for callback in cls._callbacks[type(event)]:
            callback(event)
