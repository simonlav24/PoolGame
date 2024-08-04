from typing import Dict, Any, Optional, Type
from enum import Enum
import json
from pydantic import BaseModel

class EventType(str, Enum):
    MESSAGE = "MESSAGE"
    START_GAME = "START_GAME"
    END_GAME = "END_GAME"
    JOIN = "JOIN"
    LEAVE = "LEAVE"
    WAIT_FOR_JOIN = "WAIT_FOR_JOIN"
    WAIT_FOR_START = "WAIT_FOR_START"
    CONNECTION = "CONNECTION"
    STATUS_RESPONSE = "STATUS_RESPONSE"
    JOIN_RESPONSE = "JOIN_RESPONSE"
    MOVE_STICK = "MOVE_STICK"
    STRIKE = "STRIKE"

class Status(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

class PlayerType(str, Enum):
    PLAYER = "PLAYER"
    SPECTATOR = "SPECTATOR"
    AI = "AI"

class PlayerSpot(str, Enum):
    PLAYER1 = "PLAYER1"
    PLAYER2 = "PLAYER2"

class Payload(BaseModel):
    pass

class Event(BaseModel):
    sender_id: str
    event_type: EventType
    payload: Payload

    class Config:
        use_enum_values = True

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        data['payload'] = self.payload.dict()
        return data

    def model_dump_json(self, **kwargs):
        data = self.model_dump(**kwargs)
        return json.dumps(data)

class EventFactory:
    _payload_map: Dict[EventType, Type[Payload]] = {}

    @classmethod
    def register_payload(cls, event_type: EventType):
        def decorator(payload_class: Type[Payload]):
            cls._payload_map[event_type] = payload_class
            payload_class.event_type = event_type
            return payload_class
        return decorator

    @classmethod
    def get_payload_model(cls, event_type: EventType) -> Type[Payload]:
        if event_type in cls._payload_map:
            return cls._payload_map[event_type]
        raise ValueError(f"Unknown event type: {event_type}")
    
    @classmethod
    def create_event(cls, event_type: EventType, payload: Payload, sender_id: str) -> Event:
        if event_type not in cls._payload_map:
            raise ValueError(f"Unknown event type: {event_type}")
        
        return Event(sender_id=sender_id, event_type=event_type, payload=payload)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Event:
        event_type = EventType(data['event_type'])
        payload_model = cls.get_payload_model(event_type)
        payload = payload_model.model_validate(data['payload'])
        return Event(sender_id=data['sender_id'], event_type=event_type, payload=payload)

    @classmethod
    def register_event(cls, event_type: EventType, payload_class: Type[Payload]) -> None:
        cls._payload_map[event_type] = payload_class

@EventFactory.register_payload(EventType.STATUS_RESPONSE)
class StatusResponsePayload(Payload):
    status: Status
    original_event: Optional[Event] = None
    reason: Optional[str] = None

@EventFactory.register_payload(EventType.JOIN)
class JoinPayload(Payload):
    player_id: str

@EventFactory.register_payload(EventType.JOIN_RESPONSE)
class JoinResponsePayload(Payload):
    player_id: str
    player_type: PlayerType
    spot: PlayerSpot

@EventFactory.register_payload(EventType.LEAVE)
class LeavePayload(Payload):
    player_id: str

@EventFactory.register_payload(EventType.START_GAME)
class StartGamePayload(Payload):
    seed: int

@EventFactory.register_payload(EventType.MOVE_STICK)
class MoveStickPayload(Payload):
    player_id: str
    angle: float

@EventFactory.register_payload(EventType.STRIKE)
class StrikePayload(Payload):
    player_id: str
    x: float
    y: float
    power: float