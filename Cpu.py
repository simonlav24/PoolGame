import pygame
from pygame.math import Vector2
from StateMachine import GameState, BallType, Player, State
from Physics import Ball, Hole
from Calc import check_line_circle_collision

# Todo:
### a function that calculates the angle to force a target ball in target angle

win: pygame.surface.Surface = None

class PlayerCpu:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.ball_type = BallType.BALL_NONE

        self.targets = []
        self.best_target = []
        self.timer = 0
        self.determined = False

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

    def can_pot_ball_in_hole(self, ball: Ball, hole: Hole) -> bool:
        cue_ball = Ball._cue_ball

        # calculate ghost position
        dir_to_hole = (hole.target_pos - ball.pos).normalize()
        ghost_pos = self.get_ghost_position(ball, hole)

        # check dot
        dir_cue_to_ball = ball.pos - cue_ball.pos
        if dir_to_hole.dot(dir_cue_to_ball) <= 0:
            return False

        # check if cue to ghost positon is clear
        cue_to_ghost_clear = True
        for other_ball in Ball._reg:
            if other_ball.type == BallType.BALL_CUE or other_ball is ball:
                continue
            if check_line_circle_collision(cue_ball.pos, ghost_pos, other_ball.pos, Ball._radius, Ball._radius):
                cue_to_ghost_clear = False
                break
        if not cue_to_ghost_clear:
            return False
        
        # check if ball to hole is clear
        ball_to_hole_clear = True
        for other_ball in Ball._reg:
            if other_ball.type == BallType.BALL_CUE or other_ball is ball:
                continue
            if check_line_circle_collision(ball.pos, hole.target_pos, other_ball.pos, Ball._radius, Ball._radius):
                ball_to_hole_clear = False
                break
        if not ball_to_hole_clear:
            return False
        return True

    def step(self): 
        self.targets = []
        available_balls_holes = []
        self.best_target = None

        if not self.determined and self.game_state.player_determined:
            self.ball_type = self.game_state.player_ball_type[Player.PLAYER_2]
            self.determined = True

        # check for current turn
        if not (self.game_state.get_state() == State.PLAY and self.game_state.get_player() == Player.PLAYER_2):
            return
        
        if self.determined and self.game_state.is_current_player_finished():
            self.ball_type = BallType.BALL_BLACK
        
        for ball in Ball._reg:
            if self.determined:
                if self.ball_type != ball.type:
                    continue
            if ball is Ball._cue_ball:
                continue
            for hole in Hole._reg:
                if self.can_pot_ball_in_hole(ball, hole):
                    self.targets.append((ball.pos, hole.target_pos))

                    # calculate score
                    dir_cue_to_ball = (ball.pos - Ball._cue_ball.pos).normalize()
                    dir_ball_to_hole = (hole.target_pos - ball.pos).normalize()
                    score = dir_cue_to_ball.dot(dir_ball_to_hole)
                    
                    available_balls_holes.append((ball, hole, score))
        
        if len(available_balls_holes) > 0:
            self.best_target = max(available_balls_holes, key=lambda x: x[2])

        # play turn
        self.timer += 1
        if self.timer >= 60 * 3:
            self.timer = 0
            if self.best_target:
                ball = self.best_target[0]
                hole = self.best_target[1]

                ghost_pos = self.get_ghost_position(ball, hole)
                direction = (ghost_pos - Ball._cue_ball.pos).normalize()
                power = 50
                Ball._cue_ball.set_vel(direction * power * 0.05)
                self.game_state.update()
            else:
                print('cant play')

    def draw(self):
        return
        for target in self.targets:
            pygame.draw.circle(win, (0,255,0), target[0], 4)
            pygame.draw.circle(win, (0,255,0), target[1], 4)
            pygame.draw.line(win, (0,255,0), target[0], target[1])
        if self.best_target:
            pygame.draw.circle(win, (0,0,255), self.best_target[0].pos, 4)
            pygame.draw.circle(win, (0,0,255), self.best_target[1].pos, 4)
            pygame.draw.line(win, (0,0,255), self.best_target[0].pos, self.best_target[1].pos)


    
