
from enum import Enum
from typing import List

class State(Enum):
    PLAY = 0
    WAIT_FOR_STABLE = 1
    MOVING_CUE_BALL = 2
    GAME_OVER = 3

class BallType(Enum):
    BALL_NONE = 0
    BALL_CUE = 1
    BALL_SOLID = 2
    BALL_STRIPE = 3
    BALL_BLACK = 4

    def get_color(self):
        return [
            (0,0,0), 
            (255,255,255),
            (255,255,0),
            (255,0,0),
            (0,0,0)
        ].__getitem__(self.value)

    def opposite(self) -> 'BallType':
        if self == BallType.BALL_SOLID:
            return BallType.BALL_STRIPE
        if self == BallType.BALL_STRIPE:
            return BallType.BALL_SOLID
        return BallType.BALL_NONE

class Player(Enum):
    PLAYER_1 = 0
    PLAYER_2 = 1

    def next(self):
        members = list(self.__class__)
        index = members.index(self)
        next_index = (index + 1) % len(members)
        return members[next_index]

    def __str__(self):
        if self == Player.PLAYER_1:
            return 'Player One'
        return 'Player Two'
    
    def __repr__(self):
        return str(self)


class GameState:
    def __init__(self):
        self.current_state: State = State.PLAY
        self.player_turn: Player = Player.PLAYER_1

        self.player_ball_type = {
            Player.PLAYER_1: None,
            Player.PLAYER_2: None
        }
        self.player_determined = False

        self.potted_this_turn: List[BallType] = []
        self.first_touch: BallType = None

    def get_state(self) -> State:
        return self.current_state
    
    def get_player(self) -> Player:
        return self.player_turn

    def update(self):
        next_state: State = None

        match self.current_state:
            case State.PLAY:
                next_state = State.WAIT_FOR_STABLE

            case State.WAIT_FOR_STABLE:
                next_state = State.PLAY
                advance_turn = True
                foul = False
                # determine players turn
                ## player turn shall change if
                ## 1. player didnt touch any of his balls first
                ## 2. player potted cue or black
                print(f'{self.first_touch=}')
                print(f'{self.potted_this_turn=}')

                if self.player_determined:
                    if self.first_touch != self.player_ball_type[self.get_player()]:
                        # foul: touched illegal ball
                        foul = True

                if len(self.potted_this_turn) != 0:
                    # check if players not yet determined their ball type
                    if not self.player_determined:
                        first_potted = self.potted_this_turn[0]
                        if first_potted in [BallType.BALL_SOLID, BallType.BALL_STRIPE]:
                            self.player_ball_type[self.get_player()] = first_potted
                            self.player_ball_type[self.get_player().next()] = first_potted.opposite()
                            self.player_determined = True
                    
                    all_potted_players = True
                    for type in self.potted_this_turn:
                        if self.player_ball_type[self.get_player()] != type:
                            all_potted_players = False
                    if all_potted_players:
                        advance_turn = False

                    if BallType.BALL_CUE in self.potted_this_turn:
                        # foul: potted cue ball
                        foul = True
                    
                    if BallType.BALL_BLACK in self.potted_this_turn:
                        next_state = State.GAME_OVER
                
                if foul:
                    next_state = State.MOVING_CUE_BALL
                    advance_turn = True
                if advance_turn:
                    self.player_turn = self.player_turn.next()
                print(f'State: {next_state}')

            case State.MOVING_CUE_BALL:
                next_state = State.PLAY

            case State.GAME_OVER:
                next_state = State.GAME_OVER
        
        self.current_state = next_state
