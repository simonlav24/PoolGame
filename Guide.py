
from StateMachine import GameState, State, Player
from typing import Tuple, List
from Physics import Ball, Line
from Calc import find_collision_centers_on_line, find_collision_position_ball_to_line
import pygame
from pygame.math import Vector2
from math import radians

win = None

class AimGuide:
    def __init__(self, game_state: GameState, cpu_players: List[Player]):
        self.powering = False
        self.aim_vec: Vector2 = None
        self.power_origin: Vector2 = None
        self.power = 0.0
        self.game_state = game_state
        self.cpu_players = cpu_players
        self.cpu_aim: Vector2 = None

        self.draw_points: List[Vector2] = []
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.power_origin = Vector2(pygame.mouse.get_pos())
                self.aim_vec = pygame.mouse.get_pos() - Ball._cue_ball.pos
                self.powering = True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                power_end = pygame.mouse.get_pos()
                self.power = min(self.power_origin.distance_to(power_end), 400.0) / 400.0
                self.powering = False

    def get_aim_power(self) -> Tuple[Vector2, float]:
        result = (self.aim_vec.normalize(), self.power)
        return result
    
    def set_aim(self, aim: Vector2):
        self.cpu_aim = aim

    def draw(self):
        cue_ball = Ball._cue_ball
        target = pygame.mouse.get_pos()
        if self.game_state.get_player() in self.cpu_players:
            # cpu player
            if self.cpu_aim is not None:
                target = cue_ball.pos + self.cpu_aim
        
        if self.powering:
            target = self.power_origin
        vec = target - cue_ball.pos

        try:
            vec_normalized = vec.normalize()
        except ValueError:
            vec_normalized = Vector2(0,0)
        
        # guide points is ghost position
        guide_points = []

        # test guides with balls
        for ball in Ball._reg:
            if ball is cue_ball:
                continue
            
            ghost = find_collision_centers_on_line(ball.pos, cue_ball.pos, vec_normalized, Ball._radius)
            if not ghost:
                continue
            guide_points.append({'pos': ghost, 'ball': ball, 'line': None})

        # test guides with lines
        for line in Line._reg:
            ghost = find_collision_position_ball_to_line(line.start, line.end, cue_ball.pos, cue_ball.pos + vec, Ball._radius, Line._radius)
            if not ghost:
                continue
            guide_points.append({'pos': ghost, 'ball': None, 'line': line})


        # claculate power
        power = 0.0
        if self.powering:
            power = min(target.distance_to(pygame.mouse.get_pos()), 400.0) / 400.0

        if len(guide_points) > 0:
            guide = min(guide_points, key=lambda p: cue_ball.pos.distance_squared_to(p['pos']))
            ghost_pos: Vector2 = guide['pos']
            pygame.draw.circle(win, (255,255,0), ghost_pos, Ball._radius, 1)
            # draw collision guide with line
            pygame.draw.line(win, (255,255,0), cue_ball.pos, ghost_pos)
            if guide['ball'] is not None:
                # draw bounce target ball
                ball: Ball = guide['ball']
                target_bounce_vec = (ball.pos - ghost_pos).normalize()
                target_bounce_strength = (ghost_pos - cue_ball.pos).normalize().dot(target_bounce_vec)
                pygame.draw.line(win, (255,255,0), ball.pos, ghost_pos + target_bounce_vec * 100 * target_bounce_strength)
                ghost_bounce_vec = max([Vector2(-target_bounce_vec.y, target_bounce_vec.x), Vector2(target_bounce_vec.y, -target_bounce_vec.x)], key=lambda x: x.dot(target - cue_ball.pos))
                ghost_bounce_strength = 1 - target_bounce_strength
                pygame.draw.line(win, (255,255,0), ghost_pos, ghost_pos + ghost_bounce_vec * 100 * ghost_bounce_strength)

            elif guide['line'] is not None:
                line: Line = guide['line']
                # todo: reflect the line and draw
        
        # draw cue
        draw_cue(vec_normalized, power)

        # draw points
        for point in self.draw_points:
            pygame.draw.circle(win, (255,0,0), point, 5)
            pygame.draw.circle(win, (255,0,0), point, Ball._radius, 1)
        self.draw_points.clear()

def draw_cue(dir, power):
    # dir should be normalized
    s = Ball._cue_ball.pos - dir * Ball._radius - dir * power * 100
    e = Ball._cue_ball.pos - dir * Ball._radius * 20 - dir * power * 100
    pygame.draw.line(win, (82, 50, 16), s, e, 3)
