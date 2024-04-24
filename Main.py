
import pygame
from pygame.math import Vector2
from math import sqrt
from random import shuffle
from typing import List, Tuple
from enum import Enum
from Calc import *
from StateMachine import *



class Ball:
    _radius = 10
    _reg: List['Ball'] = []
    _fakes: List['Ball'] = []
    _collisions: Tuple['Ball', 'Ball'] = []
    _ball_to_remove: List['Ball'] = []
    _entered_balls: List['Ball'] = []
    _first_cue_touch: BallType = None
    _potted_this_turn: List[BallType] = []
    def __init__(self, pos=Vector2(0,0), fake=False, type=BallType.BALL_NONE):
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
        pygame.draw.circle(win, self.type.get_color(), self.pos, Ball._radius)
        if self.stable:
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

if __name__ == '__main__':

    pygame.init()
    win = pygame.display.set_mode((1280, 800))
    clock = pygame.time.Clock()

    font1 = pygame.font.SysFont('Arial', 16)

    types = [BallType.BALL_SOLID] * 7 + [BallType.BALL_STRIPE] * 7
    shuffle(types)
    offx = win.get_width() / 2
    offy = win.get_height() / 2 + 150

    ball_count = 0
    for i in range(6):
        for j in range(-i, i, 2):
            type = types.pop()
            if ball_count == 4:
                types.append(type)
                type = BallType.BALL_BLACK
            Ball(Vector2(10 * j + offx, 10 * i * sqrt(3) + offy), type=type)
            ball_count += 1

    cue_ball = CueBall(Vector2(win.get_width() / 2, 200))
    cue_selected = False
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

    game_state = GameState()

    done = False
    while not done:
        # --- Main event loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if game_state.get_state() == State.PLAY:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if cue_ball.pos.distance_squared_to(pygame.mouse.get_pos()) < Ball._radius **2:
                            cue_selected = True
                if event.type == pygame.MOUSEBUTTONUP:
                    if cue_selected:
                        power = cue_ball.pos.distance_to(pygame.mouse.get_pos())
                        direction = (cue_ball.pos - pygame.mouse.get_pos()).normalize()
                        power = min(power, 150.0)
                        cue_ball.set_vel(direction * power * 0.05)
                        game_state.update()
                    cue_selected = False
            elif game_state.get_state() == State.MOVING_CUE_BALL:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if cue_ball.is_out:
                            cue_ball = CueBall(pygame.mouse.get_pos())
                        else:
                            cue_ball.set_pos(pygame.mouse.get_pos())
                        game_state.update()
        
        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            done = True

        # step
        Ball.step_balls()
        for hole in Hole._reg:
            hole.step()
        if game_state.get_state() == State.WAIT_FOR_STABLE:
            if Ball.check_stability():
                # determine next turn
                game_state.potted_this_turn = cue_ball.get_potted_this_turn()
                game_state.first_touch = cue_ball.get_first_touch()
                game_state.update()
                cue_ball.new_turn()
        
        # draw
        win.fill((0, 150, 0))
        for hole in Hole._reg:
            hole.draw()
        Ball.draw_balls()
        Line.draw_lines()

        # draw guides
        if cue_selected:
            mouse = pygame.mouse.get_pos()
            vec = cue_ball.pos - mouse
            pygame.draw.line(win, (255,255,0), cue_ball.pos, cue_ball.pos + vec * 3)

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
                mouse_to_cue = cue_ball.pos - mouse
                cue_to_guide = point - cue_ball.pos
                if mouse_to_cue.dot(cue_to_guide) > 0:
                    guide_points.append((point, ball))

            if len(guide_points) > 0:
                point, ball = min(guide_points, key=lambda p: cue_ball.pos.distance_squared_to(p[0]))
                pygame.draw.circle(win, (255,255,0), point, Ball._radius, 1)
                bounce_vec = ball.pos - point
                pygame.draw.line(win, (255,255,0), point, point + bounce_vec * 4)
        
        if game_state.get_state() == State.MOVING_CUE_BALL:
            pygame.draw.circle(win, (255,255,255), pygame.mouse.get_pos(), Ball._radius, 1)

        # draw entered balls
        for i, ball in enumerate(Ball._entered_balls):
            pos = Vector2(right + Ball._radius * 4, Ball._radius + i * 2 * Ball._radius)
            pygame.draw.circle(win, ball.type.get_color(), pos, Ball._radius)

        # temporarily display info
        player_turn_surf = font1.render(f'{str(game_state.get_player())}: {game_state.player_ball_type[game_state.get_player()]}', True, (0,0,0))
        win.blit(player_turn_surf, (10,10))

        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    