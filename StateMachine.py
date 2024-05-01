'''
State machine module and rules enforecement
'''

from enum import Enum
from typing import List

class State(Enum):
    PLAY = 0
    WAIT_FOR_STABLE = 1
    MOVING_CUE_BALL = 2
    GAME_OVER = 3

class Foul(Enum):
    NONE = 0
    TOUCHED_ILLEGAL_BALL = 1
    POTTED_CUE = 2
    POTTED_BLACK = 3

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

        self.type_potted = {
            BallType.BALL_SOLID: 0,
            BallType.BALL_STRIPE: 0
        }
        self.player_winner: Player = None
        self.round_count = 0

    def update_potted(self, potted: List[BallType]):
        self.potted_this_turn = potted
        for ball_tpye in self.potted_this_turn:
            if ball_tpye in [BallType.BALL_CUE, BallType.BALL_BLACK]:
                continue
            self.type_potted[ball_tpye] += 1

    def get_state(self) -> State:
        return self.current_state
    
    def get_player(self) -> Player:
        return self.player_turn

    def is_current_player_finished(self) -> bool:
        if not self.player_determined:
            return False
        return self.type_potted[self.player_ball_type[self.get_player()]] == 7

    def update(self):
        next_state: State = None

        match self.current_state:
            case State.PLAY:
                next_state = State.WAIT_FOR_STABLE

            case State.WAIT_FOR_STABLE:
                next_state = State.PLAY
                advance_turn = True
                foul = Foul.NONE
                # determine players turn
                ## player turn shall change if
                ## 1. player didnt touch any of his balls first
                ## 2. player potted cue or black
                print(f'{self.first_touch=}')
                print(f'{self.potted_this_turn=}')

                # check first touch
                if self.player_determined:
                    allowed_first_touch = [self.player_ball_type[self.get_player()]]
                    if self.is_current_player_finished():
                        # player potted all his balls 
                        allowed_first_touch.append(BallType.BALL_BLACK)

                    if self.first_touch not in allowed_first_touch:
                        # foul: touched illegal ball
                        print('foul, touched illegal ball')
                        foul = Foul.TOUCHED_ILLEGAL_BALL

                if len(self.potted_this_turn) != 0:
                    # check if players not yet determined their ball type
                    if not self.player_determined:
                        first_potted = self.potted_this_turn[0]
                        if first_potted in [BallType.BALL_SOLID, BallType.BALL_STRIPE]:
                            self.player_ball_type[self.get_player()] = first_potted
                            self.player_ball_type[self.get_player().next()] = first_potted.opposite()
                            self.player_determined = True
                    
                    # check for potted balls
                    first_potted = self.potted_this_turn[0]
                    if self.player_ball_type[self.get_player()] == first_potted:
                        advance_turn = False

                    if BallType.BALL_CUE in self.potted_this_turn:
                        # foul: potted cue ball
                        print('foul, potted cue ball')
                        foul = Foul.POTTED_CUE
                    
                    if BallType.BALL_BLACK in self.potted_this_turn:
                        next_state = State.GAME_OVER
                        if self.is_current_player_finished():
                            # player finished, check if white also entered
                            if BallType.BALL_CUE in self.potted_this_turn:
                                # white entered, other player won
                                self.player_winner = self.get_player().next()
                            else:
                                # current player won
                                self.player_winner = self.get_player()
                        else:
                            # foul black potted, other player won 
                            self.player_winner = self.get_player().next()
                            foul = Foul.POTTED_BLACK
                        print(f'{self.player_winner} Wins')
                
                if foul != Foul.NONE:
                    next_state = State.MOVING_CUE_BALL
                    advance_turn = True
                    if foul == Foul.POTTED_BLACK:
                        next_state = State.GAME_OVER
                if advance_turn:
                    self.player_turn = self.player_turn.next()
                print(f'State: {next_state}, score: {self.type_potted}')
                self.round_count += 1

            case State.MOVING_CUE_BALL:
                next_state = State.PLAY

            case State.GAME_OVER:
                next_state = State.GAME_OVER
        
        self.current_state = next_state
