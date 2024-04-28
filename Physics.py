
import pygame
from pygame.math import Vector2
from typing import List, Tuple
from StateMachine import BallType

font_small = None
win = None

ball_color = {
    0: (197, 171, 144),
    1: (229, 160, 31),
    2: (55, 57, 106),
    3: (235, 53, 49),
    4: (76, 51, 81),
    5: (253, 88, 43),
    6: (65, 119, 105),
    7: (141, 50, 59),
    8: (44, 42, 47),
    9: (229, 160, 31),
    10: (55, 57, 106),
    11: (235, 53, 49),
    12: (76, 51, 81),
    13: (253, 88, 43),
    14: (65, 119, 105),
    15: (141, 50, 59),
}

class Ball:
    _radius = 10
    _reg: List['Ball'] = []
    _fakes: List['Ball'] = []
    _collisions: Tuple['Ball', 'Ball'] = []
    _ball_to_remove: List['Ball'] = []
    _entered_balls: List['Ball'] = []
    _first_cue_touch: BallType = None
    _potted_this_turn: List[BallType] = []
    def __init__(self, pos=Vector2(0,0), fake=False, type=BallType.BALL_NONE, number=0):
        self.pos = pos
        self.vel = Vector2(0,0)
        self.acc = Vector2(0,0)
        self.stable = False
        self.is_fake = fake
        if fake:
            Ball._fakes.append(self)
        else:
            Ball._reg.append(self)
        self.type = type
        self.number = number
        self.create_surf()
        
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
    
    def potted(self):
        Ball._entered_balls.append(self)
        Ball._potted_this_turn.append(self.type)
        Ball._reg.remove(self)

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
                if distance == 0:
                    distance = 0.01
                if distance < Ball._radius * 2:
                    overlap = 0.5 * (distance - Ball._radius * 2)
                    
                    ball.pos -= overlap * (ball.pos - target.pos) / distance
                    target.pos += overlap * (ball.pos - target.pos) / distance
                    
                    Ball._collisions.append((ball, target))
        
        for ball, target in Ball._collisions:
            # check for first cue touch
            if all([Ball._first_cue_touch is None,
                    not ball.is_fake and not target.is_fake,
                    (ball.type == BallType.BALL_CUE or target.type == BallType.BALL_CUE)]):
                Ball._first_cue_touch = target.type if target.type != BallType.BALL_CUE else ball.type

            distance = ball.pos.distance_to(target.pos)
            if distance == 0:
                distance = 0.01

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

    def create_surf(self):
        color = ball_color[self.number]
        self.surf = pygame.Surface((Ball._radius * 2, Ball._radius * 2), pygame.SRCALPHA)
        if self.number > 8:
            # stripe
            self.surf.fill(ball_color[0])
            self.surf.fill(color, ((0, Ball._radius * 0.5), (self.surf.get_width(), self.surf.get_height() - Ball._radius)))
        else:
            # solid
            self.surf.fill(color)
        
        pygame.draw.circle(self.surf, ball_color[0], (Ball._radius, Ball._radius), Ball._radius * 0.5)

        if self.number != 0:
            text = font_small.render(str(self.number), True, (0,0,0))
            self.surf.blit(text, (Ball._radius - text.get_width() / 2, Ball._radius - text.get_height() / 2))

        mask = pygame.Surface((Ball._radius * 2, Ball._radius * 2), pygame.SRCALPHA)
        mask.fill((255,255,255,255))
        pygame.draw.circle(mask, (0,0,0,0), (Ball._radius, Ball._radius), Ball._radius)
        self.surf.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_SUB)

    def draw(self):
        win.blit(self.surf, self.pos - Vector2(Ball._radius, Ball._radius))

        if False:
            pygame.draw.circle(win, (0,255,0), self.pos, Ball._radius - 1, 1)

    def step_balls():
        for i in range(5):
            for ball in Ball._reg:
                ball.step()

            Ball.resolve_line_collision()
            Ball.resolve_ball_collisions()
        
        for ball in Ball._ball_to_remove:
            ball.potted()
        Ball._ball_to_remove.clear()

    def check_stability():
        for ball in Ball._reg:
            if not ball.stable:
                return False
        return True

    def draw_balls():
        for ball in Ball._reg:
            ball.draw()

class CueBall(Ball):
    def __init__(self, pos=Vector2(0,0)):
        super().__init__(pos, type=BallType.BALL_CUE)
        self.is_out = False

    def new_turn(self):
        Ball._first_cue_touch = None
        Ball._potted_this_turn = []
    
    def get_first_touch(self):
        return Ball._first_cue_touch

    def get_potted_this_turn(self):
        return Ball._potted_this_turn

    def set_pos(self, pos):
        self.pos = Vector2(pos)
    
    def potted(self):
        self.is_out = True
        Ball._potted_this_turn.append(self.type)
        Ball._reg.remove(self)

class Line:
    _reg: List['Line'] = []
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
    _reg: List['Hole'] = []
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