from abc import ABC, abstractmethod
from datetime import datetime
import uuid

class BaseEvent(ABC):
    def __init__(self, timestamp: datetime, event_type: str):
        if not isinstance(timestamp, datetime):
            raise TypeError("timestamp must be a datetime object")
        if not event_type or not isinstance(event_type, str):
            raise ValueError("event_type must be a non-empty string")
        self.timestamp = timestamp
        self.event_type = event_type.upper()
        self.event_id = uuid.uuid4()

    @abstractmethod
    def validate(self) -> bool:
        """Validate event data - must be implemented by subclasses"""
        pass

    def __str__(self):
        return f"<{self.__class__.__name__} {self.event_type} @ {self.timestamp} id={self.event_id}>"

    def __repr__(self):
        return (f"{self.__class__.__name__}(timestamp={self.timestamp!r}, "
                f"event_type={self.event_type!r}, event_id={self.event_id!r})") 