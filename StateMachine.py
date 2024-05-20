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
    POTTED_ILLEGAL = 2
    POTTED_CUE = 3
    POTTED_BLACK = 4

class BallType(Enum):
    BALL_NONE = 0
    BALL_CUE = 1
    BALL_SOLID = 2
    BALL_STRIPE = 3
    BALL_BLACK = 4

    SNOOKER_RED = 5
    SNOOKER_YELLOW = 6
    SNOOKER_GREEN = 7
    SNOOKER_BROWN = 8
    SNOOKER_BLUE = 9
    SNOOKER_PINK = 10
    SNOOKER_BLACK = 11

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
    
    def smaller_than(self, ball: 'BallType'):
        return ball.value < self.value

snooker_score_table = {
    BallType.SNOOKER_RED: 1,
    BallType.SNOOKER_YELLOW: 2,
    BallType.SNOOKER_GREEN: 3,
    BallType.SNOOKER_BROWN: 4,
    BallType.SNOOKER_BLUE: 5,
    BallType.SNOOKER_PINK: 6,
    BallType.SNOOKER_BLACK: 7,
}

class Player_Type(Enum):
    HUMAN = 0
    CPU = 1

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

class Rules(Enum):
    BALL_8 = 0
    BALL_9 = 1
    SNOOKER = 2
    RUSSIAN = 3

class GameState:
    def __init__(self, table_dims):
        self.current_state: State = State.PLAY
        self.player_turn: Player = Player.PLAYER_1

        self.player_ball_type = {
            Player.PLAYER_1: None,
            Player.PLAYER_2: None
        }
        self.player_determined = False

        self.potted_this_turn: List[BallType] = []
        self.first_touch: BallType = None

        self.score = {
            Player.PLAYER_1: 0,
            Player.PLAYER_2: 0,
        }

        self.player_winner: Player = None
        self.round_count = 0
        self.table_dims = table_dims
    
    def get_state(self) -> State:
        return self.current_state
    
    def get_player(self) -> Player:
        return self.player_turn
    
    def update(self):
        pass

    def update_potted(self, potted: List[BallType]):
        pass

    def is_current_player_finished(self) -> bool:
        pass

    def get_info(self) -> str:
        pass

    def get_respot(self) -> List[BallType]:
        return []

class SnookerInnerState(Enum):
    SNOOKER_RED_ON = 0
    SNOOKER_FREE_BALL = 1
    SNOOKER_LATE_GAME = 2

class GameStateSnooker(GameState):
    def __init__(self, table_dims):
        super().__init__(table_dims)
        self.reds_are_on = True
        self.red_count = 0
        self.inner_state = SnookerInnerState.SNOOKER_RED_ON
        self.current_ball = BallType.SNOOKER_RED
    
    def get_info(self) -> str:
        text_1 = f'Player 1: score: {self.score[Player.PLAYER_1]}'
        text_2 = f'Player 2: score: {self.score[Player.PLAYER_2]}'

        # TODO: target must be current ball or colored in late game
        if self.reds_are_on:
            target = 'Red'
        else:
            target = 'Colored'

        if self.get_player() == Player.PLAYER_1:
            text_1 += f' <- target {target}'
        else:
            text_2 += f' <- target {target}'

        return text_1 + '        ' + text_2

    def update_potted(self, potted: List[BallType]):
        ''' update this of balls potted this turn before update '''
        self.potted_this_turn = potted

    def is_red_done(self):
        return self.red_count == 15

    def get_respot(self) -> List[BallType]:
        colored_potted = [i for i in self.potted_this_turn if i != BallType.SNOOKER_RED]
        respot = []
        match self.inner_state:
            case SnookerInnerState.SNOOKER_RED_ON:
                respot = colored_potted
            case SnookerInnerState.SNOOKER_FREE_BALL:
                respot = colored_potted
            case SnookerInnerState.SNOOKER_LATE_GAME:
                for potted in colored_potted:
                    if potted.value > self.current_ball.value:
                        respot.append(potted)

        return respot

    def update(self):
        next_state: State = None

        match self.current_state:
            case State.PLAY:
                next_state = State.WAIT_FOR_STABLE

            case State.WAIT_FOR_STABLE:
                next_state = State.PLAY
                advance_turn = True
                foul = Foul.NONE

                print(f'{self.first_touch=}')
                print(f'{self.potted_this_turn=}')

                # inner state cases
                self.inner_state = SnookerInnerState.SNOOKER_RED_ON
                if not self.is_red_done():
                    if self.reds_are_on:
                        self.inner_state = SnookerInnerState.SNOOKER_RED_ON
                    else:
                        self.inner_state = SnookerInnerState.SNOOKER_FREE_BALL
                else:
                    self.inner_state = SnookerInnerState.SNOOKER_LATE_GAME

                match self.inner_state:
                    case SnookerInnerState.SNOOKER_RED_ON:
                        balls_on = [BallType.SNOOKER_RED]
                        if not self.first_touch in balls_on:
                            # foul: touched illegal ball
                            foul = Foul.TOUCHED_ILLEGAL_BALL

                        score_this_turn = 0
                        # check potted: check if only red are potted
                        for t in self.potted_this_turn:
                            if t == BallType.SNOOKER_RED:
                                score_this_turn += snooker_score_table[t]
                                self.red_count += 1
                                self.reds_are_on = False
                            else:
                                # foul: potted illegal ball
                                foul = Foul.POTTED_ILLEGAL

                    case SnookerInnerState.SNOOKER_FREE_BALL:
                        balls_on = [BallType.SNOOKER_YELLOW, BallType.SNOOKER_GREEN, 
                                    BallType.SNOOKER_BROWN, BallType.SNOOKER_BLUE, 
                                    BallType.SNOOKER_PINK, BallType.SNOOKER_BLACK]
                        if not self.first_touch in balls_on:
                            # foul: touched illegal ball
                            foul = Foul.TOUCHED_ILLEGAL_BALL

                        score_this_turn = 0
                        # check potted: check if potted single colored ball
                        if len(self.potted_this_turn) == 1:
                            potted = self.potted_this_turn[0]
                            if potted == BallType.SNOOKER_RED:
                                # foul: potted illegal
                                foul = Foul.POTTED_ILLEGAL
                            else:
                                score_this_turn += snooker_score_table[potted]
                                advance_turn = False
                        else:
                            # foul: potted illegal
                            foul = Foul.POTTED_ILLEGAL
                        
                        self.reds_are_on = True
                        # check for late game
                        if self.is_red_done():
                            self.reds_are_on = False
                            self.current_ball = BallType.SNOOKER_YELLOW

                    case SnookerInnerState.SNOOKER_LATE_GAME:
                        # TODO: continue here
                        pass 

                # common
                if BallType.BALL_CUE in self.potted_this_turn:
                    # foul: potted cue ball
                    self.reds_are_on = True
                    foul = Foul.POTTED_CUE

                # resolve foul
                if foul != Foul.NONE:
                    print(f'{self.get_player()}, foul:{foul}')
                match foul:
                    case Foul.POTTED_CUE:
                        next_state = State.MOVING_CUE_BALL
                    case Foul.POTTED_ILLEGAL:
                        next_state = State.PLAY
                    case Foul.TOUCHED_ILLEGAL_BALL:
                        next_state = State.PLAY
                    case Foul.NONE:
                        self.score[self.get_player()] += score_this_turn
                        if len(self.potted_this_turn) > 0:
                            advance_turn = False

                if advance_turn:
                    self.player_turn = self.player_turn.next()
                print(f'State: {next_state}, turn: {self.player_turn}, score: {self.score}')
                self.round_count += 1

            case State.MOVING_CUE_BALL:
                next_state = State.PLAY

            case State.GAME_OVER:
                next_state = State.GAME_OVER
        
        self.current_state = next_state



class GameStateEightBall(GameState):
    def update_potted(self, potted: List[BallType]):
        ''' update this of balls potted this turn before update '''
        self.potted_this_turn = potted
        for ball_tpye in self.potted_this_turn:
            if ball_tpye in [BallType.BALL_CUE, BallType.BALL_BLACK]:
                continue
            self.score[self.get_player()] += 1

    def get_info(self) -> str:
        if self.get_state() != State.GAME_OVER:
            text = f'{str(self.get_player())}: {self.player_ball_type[self.get_player()]}'
        else:
            text = f'Game Over, {self.player_winner} Won'
        return text

    def is_current_player_finished(self) -> bool:
        if not self.player_determined:
            return False
        return self.score[self.get_player()] == 7

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
                        foul = Foul.NONE
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
                print(f'State: {next_state}, score: {self.score}')
                self.round_count += 1

            case State.MOVING_CUE_BALL:
                next_state = State.PLAY

            case State.GAME_OVER:
                next_state = State.GAME_OVER
        
        self.current_state = next_state
