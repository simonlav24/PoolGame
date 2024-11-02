
from enum import Enum

class PlayerSpot(str, Enum):
    PLAYER1 = "PLAYER1"
    PLAYER2 = "PLAYER2"

    def next(self):
        members = list(self.__class__)
        index = members.index(self)
        next_index = (index + 1) % len(members)
        return members[next_index]




