
from __future__ import annotations
from pydantic import BaseModel
from StateMachine import Player, Player_Type
from enum import Enum
from typing import Any, Optional, DefaultDict, Type
from collections import defaultdict

ACTION_TO_MESSAGE: DefaultDict[Action, Type[Message]] = defaultdict(lambda: Message)

class Action(Enum):
    JOIN = 0
    GAME_START = 1
    STRIKE = 2
    HOLD_CUE = 3
    PLAYER_SPOT = 4

class Message(BaseModel):
    id: Optional[str] = 'Server'
    action: Action
    message: Optional[Any] = None

class PlayerSpotMessage(Message):
    message: Player
    player_type: Player_Type
    action: Optional[Action] = Action.PLAYER_SPOT

class StrikeData(BaseModel):
    x: float
    y: float
    power: float

class StrikeMessage(Message):
    action: Optional[Action] = Action.STRIKE
    message: StrikeData

ACTION_TO_MESSAGE[Action.PLAYER_SPOT] = PlayerSpotMessage
ACTION_TO_MESSAGE[Action.STRIKE] = StrikeMessage

