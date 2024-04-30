
from StateMachine import GameState, State, Player
from typing import Tuple, List
from Physics import Ball
from Calc import find_collision_centers_on_line
import pygame
from pygame.math import Vector2

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

        guide_points = []
        for ball in Ball._reg:
            if ball is cue_ball:
                continue
            try:
                vec_normalized = vec.normalize()
            except ValueError as e:
                vec_normalized = Vector2(0,0)
            
            point = find_collision_centers_on_line(ball.pos, cue_ball.pos, vec_normalized, Ball._radius)
            if not point:
                continue
            cue_to_mouse = target - cue_ball.pos
            cue_to_guide = point - cue_ball.pos
            if cue_to_mouse.dot(cue_to_guide) > 0:
                guide_points.append((point, ball))

        power = 0.0
        if self.powering:
            power = min(target.distance_to(pygame.mouse.get_pos()), 400.0) / 400.0

        draw_cue(vec_normalized, power)

        if len(guide_points) > 0:
            point, ball = min(guide_points, key=lambda p: cue_ball.pos.distance_squared_to(p[0]))
            pygame.draw.circle(win, (255,255,0), point, Ball._radius, 1)
            bounce_vec = ball.pos - point
            pygame.draw.line(win, (255,255,0), point, point + bounce_vec * 4)
        
            pygame.draw.line(win, (255,255,0), cue_ball.pos, point)

def draw_cue(dir, power):
    # dir should be normalized
    s = Ball._cue_ball.pos - dir * Ball._radius - dir * power * 100
    e = Ball._cue_ball.pos - dir * Ball._radius * 20 - dir * power * 100
    pygame.draw.line(win, (82, 50, 16), s, e, 3)
