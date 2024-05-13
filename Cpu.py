import pygame
from pygame.math import Vector2
from StateMachine import GameState, BallType, Player, State
from Physics import Ball, CueBall, Hole
from Calc import check_line_circle_collision, closest_point_on_line
from typing import List, Tuple
from random import uniform, randint, choice

# Todo:
### a function that calculates the angle to force a target ball in target angle

win: pygame.surface.Surface = None
brake_random = Vector2(uniform(-10, 10),100)

class PlayerCpu:
    def __init__(self, game_state: GameState, player: Player, dificulty = 3):
        self.game_state = game_state
        self.ball_type = BallType.BALL_NONE

        self.targets = []
        self.best_target = []
        self.timer = 0
        self.determined = False
        self.player = player
        self.debug = True
        self.dificulty = dificulty # range = [1, 2, 3]
        self.shot_type: str = None

        self.direction: Vector2 = None
        self.power = 1

    def get_closest_holes_to_ball(self, ball: Ball, amount=2) -> Hole:
        distances = []
        for hole in Hole._reg:
            distances.append((hole, hole.pos.distance_squared_to(ball.pos)))
        distances = sorted(distances, key=lambda x: x[1])
        result = []
        for i in range(amount):
            result.append(distances[i][0])
        return result

    def get_ghost_position(self, ball: Ball, hole: Hole) -> Vector2:
        dir_to_hole = (hole.target_pos - ball.pos).normalize()
        ghost_pos = ball.pos - dir_to_hole * Ball._radius * 2
        return ghost_pos

    def can_pot_ball_in_hole(self, ball: Ball, hole: Hole, cue_pos: Vector2) -> bool:

        # calculate ghost position
        dir_to_hole = (hole.target_pos - ball.pos).normalize()
        ghost_pos = self.get_ghost_position(ball, hole)

        # check dot
        dir_cue_to_ball = ball.pos - cue_pos
        if dir_to_hole.dot(dir_cue_to_ball) <= 0:
            return False

        # check if cue to ghost positon is clear
        cue_to_ghost_clear = True
        for other_ball in Ball._reg:
            if other_ball.get_type() == BallType.BALL_CUE or other_ball is ball:
                continue
            if check_line_circle_collision(cue_pos, ghost_pos, other_ball.pos, Ball._radius, Ball._radius):
                cue_to_ghost_clear = False
                break
        if not cue_to_ghost_clear:
            return False
        
        # check if ball to hole is clear
        ball_to_hole_clear = True
        for other_ball in Ball._reg:
            if other_ball.get_type() == BallType.BALL_CUE or other_ball is ball:
                continue
            if check_line_circle_collision(ball.pos, hole.target_pos, other_ball.pos, Ball._radius, Ball._radius):
                ball_to_hole_clear = False
                break
        if not ball_to_hole_clear:
            return False
        return True

    def get_direction(self) -> Vector2:
        return self.direction
    
    def check_ball_validity(self, ball: Ball) -> bool:
        if self.determined and self.game_state.is_current_player_finished():
            self.ball_type = BallType.BALL_BLACK
        
        if self.determined:
            if self.ball_type != ball.get_type():
                return False
        else:
            if ball.get_type() == BallType.BALL_BLACK:
                return False
        if ball is Ball._cue_ball:
            return False
        return True

    def step_shoot_ball(self) -> bool:
        available_balls_holes = []
        
        for ball in Ball._reg:
            if not self.check_ball_validity(ball):
                continue
            for hole in Hole._reg:
                if self.can_pot_ball_in_hole(ball, hole, Ball._cue_ball.pos):
                    self.targets.append((ball.pos, hole.target_pos))

                    # calculate score
                    dir_cue_to_ball = (ball.pos - Ball._cue_ball.pos).normalize()
                    dir_ball_to_hole = (hole.target_pos - ball.pos).normalize()
                    score = dir_cue_to_ball.dot(dir_ball_to_hole)
                    
                    available_balls_holes.append((ball, hole, score))
        
        if len(available_balls_holes) > 0:
            self.best_target = max(available_balls_holes, key=lambda x: x[2])
        
        if self.best_target:
            ball = self.best_target[0]
            hole = self.best_target[1]
            ghost_pos = self.get_ghost_position(ball, hole)
            self.direction = (ghost_pos - Ball._cue_ball.pos).normalize()
            self.power = 0.4
            return True
        return False

    def step_brake_shoot(self) -> bool:
        if not self.game_state.round_count == 0:
            return False
        
        self.shot_type = 'brake shot'
        self.direction = brake_random
        self.power = 1.0
        return True
    
    def step_touch(self) -> bool:
        ball_options = []
        for ball in Ball._reg:
            if not self.check_ball_validity(ball):
                continue
            # check if ball is accessible
            ball_accessible = True
            for other_ball in Ball._reg:
                if other_ball is ball or other_ball is Ball._cue_ball:
                    continue
                # get closest point of other ball on line
                other_ball_on_line_pos = closest_point_on_line(Ball._cue_ball.pos, ball.pos, other_ball.pos)
                if other_ball_on_line_pos:
                    if other_ball.pos.distance_to(other_ball_on_line_pos) < 2 * Ball._radius:
                        ball_accessible = False
                        break
            
            if ball_accessible:
                ball_options.append(ball)
        
        if len(ball_options) == 0:
            return False
        
        # pick a ball to hit
        self.shot_type = 'touch shot'
        target = choice(ball_options)
        self.direction = (target.pos - Ball._cue_ball.pos).normalize()
        self.power = 0.3
        return True

    def is_pos_free(self, pos: Vector2) -> bool:
        # check if no ball around
        for ball in Ball._reg:
            if pos.distance_to(ball.pos) < Ball._radius * 2:
                return False
        
        # check if inside talbe
        dims = self.game_state.table_dims
        if (pos.x < dims['left'] or
            pos.x > dims['right'] or
            pos.y < dims['top'] or
            pos.y > dims['bottom']):
            return False

        # check for no line around
        # todo

        return True

    def step_mouse_in_hand(self):
        cue_new_pos = Vector2()
        available_positions: List[Tuple[Ball, Hole, Vector2]] = []
        for ball in Ball._reg:
            if not self.check_ball_validity(ball):
                continue

            # check if ball is free to hole and position before ball is free to ball
            for hole in Hole._reg:
                # check for free cue position 
                vec_to_hole = (hole.target_pos - ball.pos).normalize()
                pos = ball.pos - vec_to_hole * Ball._radius * 5

                if not self.is_pos_free(pos):
                    continue
                # check if ball can be potted
                if not self.can_pot_ball_in_hole(ball, hole, pos):
                    continue
                
                available_positions.append((ball, hole, pos))

        # choose from available positions
        if len(available_positions) == 0:
            return

        cue_new_pos = choice(available_positions)[2]

        self.shot_type = 'ball in hand'

        cue_ball = Ball._cue_ball
        if cue_ball.is_out:
            cue_ball = CueBall(cue_new_pos)
        else:
            cue_ball.set_pos(cue_new_pos)
        self.game_state.update()

    def step(self): 
        self.targets = []
        self.best_target = None

        if not self.determined and self.game_state.player_determined:
            self.ball_type = self.game_state.player_ball_type[self.player]
            self.determined = True

        # check for current turn
        if not self.game_state.get_player() == self.player:
            return
        
        if not (self.game_state.get_state() in [State.PLAY, State.MOVING_CUE_BALL]):
            return

        # check for mouse in hand turn
        if self.game_state.get_state() == State.MOVING_CUE_BALL:
            self.step_mouse_in_hand()
            return

        # try to break shot
        if self.step_brake_shoot():
            self.play_turn()
            return

        # try a regular shot
        if self.step_shoot_ball():
            self.play_turn()
            return
        
        # try to bank shot
        # todo

        # try to touch ball
        if self.step_touch():
            self.play_turn()
            return

        self.direction = None
        self.play_turn()

    def adjust_dificulty(self):
        if not randint(1, 3) <= self.dificulty:
            # bad shot
            adj = 0.1
            adjust_vec = Vector2(uniform(-adj, adj), uniform(-adj, adj))
            self.direction += adjust_vec
            print('bad shot')

    def play_turn(self):
        self.timer += 1
        if self.timer >= 60 * 3:
            self.timer = 0
            if self.shot_type:
                print(f'[CPU] {self.shot_type}')
                self.shot_type = None
            if self.direction == None:
                print('cant play')
                return
            self.adjust_dificulty()
            Ball._cue_ball.strike(self.direction, self.power)
            self.game_state.update()

    def draw(self):
        if not self.debug:
            return
        for target in self.targets:
            pygame.draw.circle(win, (0,255,0), target[0], 4)
            pygame.draw.circle(win, (0,255,0), target[1], 4)
            pygame.draw.line(win, (0,255,0), target[0], target[1])
        if self.best_target:
            pygame.draw.circle(win, (0,0,255), self.best_target[0].pos, 4)
            pygame.draw.circle(win, (0,0,255), self.best_target[1].target_pos, 4)
            pygame.draw.line(win, (0,0,255), self.best_target[0].pos, self.best_target[1].target_pos)


    
