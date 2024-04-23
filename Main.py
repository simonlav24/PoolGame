
import pygame
from pygame.math import Vector2
from math import sqrt
from random import shuffle
from Calc import *
from typing import List

BALL_NONE = 0
BALL_CUE = 1
BALL_TEAM1 = 2
BALL_TEAM2 = 3
BALL_BLACK = 4

ball_color = [
    (0,0,0), 
    (255,255,255),
    (255,255,0),
    (255,0,0),
    (0,0,0)
]

class Ball:
    _radius = 10
    _overlapping = []
    _reg: List['Ball'] = []
    _fakes: List['Ball'] = []
    _collisions = []
    _ball_to_remove: List['Ball'] = []
    _entered_balls: List['Ball'] = []
    def __init__(self, pos=Vector2(0,0), fake=False, type=BALL_NONE):
        self.pos = pos
        self.vel = Vector2(0,0)
        self.acc = Vector2(0,0)
        self.stable = False
        if fake:
            Ball._fakes.append(self)
        else:
            Ball._reg.append(self)
        self.type = type
        
    def set_vel(self, vel):
        self.vel = vel
        self.stable = False
    
    def set_acc(self, acc):
        self.acc = acc

    def step(self):
        self.vel += self.acc
        self.vel *= 0.997
        self.pos += self.vel

        if abs(self.vel[0]) < 0.01:
            self.vel[0] = 0
        if abs(self.vel[1]) < 0.01:
            self.vel[1] = 0
        
        if self.vel == Vector2(0,0):
            self.stable = True
        
        self.acc *= 0
    
    def resolve_line_collision():
        for ball in Ball._reg:
            for line in Line._reg:
                l1 = line.end - line.start
                l2 = ball.pos - line.start

                edge_length = l1.length_squared()
                t = max(0, min(edge_length, (l1[0] * l2[0] + l1[1] * l2[1]))) / edge_length
                closest = line.start + t * l1
                distance = ball.pos.distance_to(closest)
                if distance <= Ball._radius * 2:
                    b = Ball(closest, fake=True)
                    b.vel = -ball.vel

                    overlap = 1.0 * (distance - Ball._radius * 2)
                    ball.pos -= overlap * (ball.pos - b.pos) / distance
                    Ball._collisions.append((ball, b))


    def resolve_ball_collisions():
        for ball in Ball._reg + Ball._fakes:
            for target in Ball._reg + Ball._fakes:
                if ball is target:
                    continue
                distance = ball.pos.distance_to(target.pos)
                if distance < Ball._radius * 2:
                    overlap = 0.5 * (distance - Ball._radius * 2)
                    ball.pos -= overlap * (ball.pos - target.pos) / distance
                    target.pos += overlap * (ball.pos - target.pos) / distance
                    
                    Ball._collisions.append((ball, target))
        
        for ball, target in Ball._collisions:
            distance = ball.pos.distance_to(target.pos)

            normal = (target.pos - ball.pos) / distance
            tangent = Vector2(-normal[1], normal[0])

            dot_tangent1 = ball.vel[0] * tangent[0] + ball.vel[1] * tangent[1]
            dot_tangent2 = target.vel[0] * tangent[0] + target.vel[1] * tangent[1]

            dot_normal1 = ball.vel[0] * normal[0] + ball.vel[1] * normal[1]
            dot_normal2 = target.vel[0] * normal[0] + target.vel[1] * normal[1]

            ball.set_vel(tangent * dot_tangent1 + normal * dot_normal2)
            target.set_vel(tangent * dot_tangent2 + normal * dot_normal1)
        
        Ball._fakes = []
        Ball._collisions = []

    def draw(self):
        pygame.draw.circle(win, ball_color[self.type], self.pos, Ball._radius)
        if self.stable:
            pygame.draw.circle(win, (0,255,0), self.pos, Ball._radius - 1, 1)

    def step_balls():
        for i in range(5):
            for ball in Ball._reg:
                ball.step()

            Ball.resolve_line_collision()
            Ball.resolve_ball_collisions()
        
        for ball in Ball._ball_to_remove:
            Ball._entered_balls.append(ball)
            Ball._reg.remove(ball)
        Ball._ball_to_remove.clear()

    def draw_balls():
        for ball in Ball._reg:
            ball.draw()

class Line:
    _reg = []
    def __init__(self, start: Vector2, end: Vector2):
        Line._reg.append(self)
        self.start = start
        self.end = end

    def draw(self):
        pygame.draw.line(win, (0,0,0), self.start, self.end, Ball._radius * 2)
        pygame.draw.circle(win, (0,0,0), self.start, Ball._radius)
        pygame.draw.circle(win, (0,0,0), self.end, Ball._radius)

    def draw_lines():
        for line in Line._reg:
            line.draw()

class Hole:
    _reg = []
    def __init__(self, pos: Vector2):
        Hole._reg.append(self)
        self.pos = pos

    def step(self):
        for ball in Ball._reg:
            distance = ball.pos.distance_to(self.pos)
            if distance > 2 * Ball._radius:
                continue

            # apply force
            force = (self.pos - ball.pos).normalize()
            ball.set_acc((Ball._radius / distance **2) * force)

            if distance < Ball._radius:
                Ball._ball_to_remove.append(ball)
    
    def draw(self):
        pygame.draw.circle(win, (0,0,0), self.pos, Ball._radius * 1.3)

if __name__ == '__main__':

    pygame.init()
    win = pygame.display.set_mode((1280, 720))
    clock = pygame.time.Clock()

    types = [BALL_TEAM1] * 7 + [BALL_TEAM2] * 7 + [BALL_BLACK]
    shuffle(types)
    offx = win.get_width() / 2
    offy = win.get_height() / 2 + 150
    for i in range(6):
        for j in range(-i, i, 2):
            type = types.pop()
            Ball(Vector2(10 * j + offx, 10 * i * sqrt(3) + offy), type=type)

    Ball(Vector2(win.get_width() / 2, 200), type=BALL_CUE)
    # Ball(Vector2(win.get_width() / 2, 400), type=BALL_TEAM1)

    pool_line = 350
    pool_slit = 25
    pool_d_slit = 35

    left = win.get_width() / 2 - pool_line / 2
    right = win.get_width() / 2 + pool_line / 2
    top = win.get_height() / 2 - pool_line
    bottom = win.get_height() / 2 + pool_line
    center = win.get_height() / 2

    Line(Vector2(left, top + pool_d_slit), Vector2(left, center - pool_slit))
    Line(Vector2(left, bottom - pool_d_slit), Vector2(left, center + pool_slit))

    Line(Vector2(left + pool_d_slit, bottom), Vector2(right - pool_d_slit, bottom))

    Line(Vector2(right, bottom - pool_d_slit), Vector2(right, center + pool_slit))
    Line(Vector2(right, center - pool_slit), Vector2(right, top + pool_d_slit))

    Line(Vector2(left + pool_d_slit, top), Vector2(right - pool_d_slit, top))

    Hole(Vector2(left, center))
    Hole(Vector2(right, center))
    Hole(Vector2(left, top))
    Hole(Vector2(right, top))
    Hole(Vector2(left, bottom))
    Hole(Vector2(right, bottom))

    selected_ball: Ball = None

    done = False
    while not done:
        # --- Main event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for b in Ball._reg:
                        if b.pos.distance_squared_to(pygame.mouse.get_pos()) < Ball._radius **2:
                            selected_ball = b
            if event.type == pygame.MOUSEBUTTONUP:
                if selected_ball:
                    power = selected_ball.pos.distance_to(pygame.mouse.get_pos())
                    direction = (selected_ball.pos - pygame.mouse.get_pos()).normalize()
                    power = min(power, 150.0)
                    selected_ball.set_vel(direction * power * 0.05)
                selected_ball = None
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            done = True

        win.fill((0, 150, 0))

        Ball.step_balls()
        for hole in Hole._reg:
            hole.step()
        
        for hole in Hole._reg:
            hole.draw()
        Ball.draw_balls()
        Line.draw_lines()

        # draw guides
        if selected_ball:
            mouse = pygame.mouse.get_pos()
            vec = selected_ball.pos - mouse
            pygame.draw.line(win, (255,255,0), selected_ball.pos, selected_ball.pos + vec * 3)

            guide_points = []
            for ball in Ball._reg:
                if ball is selected_ball:
                    continue
                if vec.length == 0:
                    continue
                point = find_collision_centers_on_line(ball.pos, selected_ball.pos, vec.normalize(), Ball._radius)
                if not point:
                    continue
                mouse_to_cue = selected_ball.pos - mouse
                cue_to_guide = point - selected_ball.pos
                if mouse_to_cue.dot(cue_to_guide) > 0:
                    guide_points.append((point, ball))

            if len(guide_points) > 0:
                point, ball = min(guide_points, key=lambda p: selected_ball.pos.distance_squared_to(p[0]))
                pygame.draw.circle(win, (255,255,0), point, Ball._radius, 1)
                bounce_vec = ball.pos - point
                pygame.draw.line(win, (255,255,0), point, point + bounce_vec * 4)

        # draw entered balls
        for i, ball in enumerate(Ball._entered_balls):
            pos = Vector2(right + Ball._radius * 4, Ball._radius + i * 2 * Ball._radius)
            pygame.draw.circle(win, ball_color[ball.type], pos, Ball._radius)

        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    