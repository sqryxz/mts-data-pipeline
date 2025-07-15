import heapq
from itertools import count

class EventManager:
    def __init__(self):
        self._event_queue = []
        self._counter = count()

    def add_event(self, event):
        if event is None:
            raise ValueError("Event cannot be None")
        if not hasattr(event, 'timestamp'):
            raise ValueError("Event must have timestamp attribute")
        timestamp = event.timestamp
        if timestamp is None:
            raise ValueError("Event timestamp cannot be None")
        # Test actual comparability with different types
        try:
            _ = timestamp < 0
            _ = timestamp <= timestamp
            _ = timestamp == timestamp
        except TypeError:
            raise ValueError("Event timestamp must be comparable (numeric or datetime)")
        heapq.heappush(self._event_queue, (timestamp, next(self._counter), event))

    def get_next_event(self):
        if not self._event_queue:
            return None
        return heapq.heappop(self._event_queue)[2] 