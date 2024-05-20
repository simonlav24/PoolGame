
import pygame
from pygame.math import Vector2
from typing import List, Tuple
from StateMachine import BallType

ball_numbers_font = None
win: pygame.Surface = None
draw_solids = False

BALL_RADIUS = 13
texture_mult = 64
loaded_textures = True
try:
    reflection_map = pygame.image.load(r'Assets/ReflectionMap.png')
    reflection_map = pygame.transform.smoothscale(reflection_map, (BALL_RADIUS * 2, BALL_RADIUS * 2))
    shadow_map = pygame.image.load(r'Assets/ShadowMap.png')
    shadow_map = pygame.transform.smoothscale_by(shadow_map, 36.4 / shadow_map.get_width())
except Exception:
    loaded_textures = False

def initialize():
    global ball_numbers_font
    ball_numbers_font = pygame.font.SysFont('Arial', 24)

ball_color = {
    0: (230, 230, 230),
    1: (250, 185, 37),
    2: (25, 108, 227),
    3: (243, 6, 21),
    4: (82, 14, 156),
    5: (235, 95, 2),
    6: (39, 207, 68),
    7: (127, 28, 9),
    8: (14, 14, 14),
    9: (250, 185, 37),
    10: (25, 108, 227),
    11: (243, 6, 21),
    12: (82, 14, 156),
    13: (235, 95, 2),
    14: (39, 207, 68),
    15: (127, 28, 9),
    101: (214, 38, 16),
    102: (250, 185, 37),
    103: (19, 84, 47),
    104: (130, 61, 22),
    105: (25, 108, 227),
    106: (229, 119, 165),
    107: (14, 14, 14),
}

class Ball:
    _radius = BALL_RADIUS
    _reg: List['Ball'] = []
    _fakes: List['Ball'] = []
    _collisions: Tuple['Ball', 'Ball'] = []
    _ball_to_remove: List['Ball'] = []
    _entered_balls: List['Ball'] = []
    _first_cue_touch: BallType = None
    _potted_this_turn: List[BallType] = []
    _cue_ball: 'CueBall' = None
    def __init__(self, pos=Vector2(0,0), fake=False, number=0):
        
        self.pos = pos
        self.vel = Vector2(0,0)
        self.acc = Vector2(0,0)
        self.stable = False
        self.is_fake = fake
        if fake:
            Ball._fakes.append(self)
        else:
            Ball._reg.append(self)
        self.number = number
        self.create_surf()
        if not self.is_fake: print(f'--- placing ball {self.get_type()} in position {self.pos}')
    
    def __str__(self):
        if self.is_fake:
            return f'Fake_Ball'
        elif self.number == 0:
            return 'Cue_Ball'
        return f'Ball_{self.number}'

    def __repr__(self):
        return str(self)

    def get_type(self) -> BallType:
        if self.number == 0:
            return BallType.BALL_CUE
        if self.number == 8:
            return BallType.BALL_BLACK
        if self.number < 8:
            return BallType.BALL_SOLID
        elif self.number < 100:
            return BallType.BALL_STRIPE
        else:
            match self.number:
                case 101:
                    return BallType.SNOOKER_RED
                case 102:
                    return BallType.SNOOKER_YELLOW
                case 103:
                    return BallType.SNOOKER_GREEN
                case 104:
                    return BallType.SNOOKER_BROWN
                case 105:
                    return BallType.SNOOKER_BLUE
                case 106:
                    return BallType.SNOOKER_PINK
                case 107:
                    return BallType.SNOOKER_BLACK

    def set_vel(self, vel):
        self.vel = vel
        if self.vel != Vector2(0,0):
            self.stable = False
    
    def set_acc(self, acc):
        self.acc = acc

    def step(self):
        self.vel += self.acc
        self.vel *= 0.9975
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
        Ball._potted_this_turn.append(self.get_type())
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
                if distance <= Ball._radius + Line._radius:
                    b = Ball(closest, fake=True)
                    b.vel = -ball.vel

                    overlap = 1.0 * (distance - (Ball._radius + Line._radius))
                    ball.pos -= overlap * (ball.pos - b.pos) / distance
                    Ball._collisions.append((ball, b))

    def resolve_ball_collisions():
        for ball in Ball._reg:
            for target in Ball._reg:
                if ball is target:
                    continue
                distance = ball.pos.distance_to(target.pos)
                if distance == 0:
                    distance = 0.01
                second_radius = Ball._radius
                if ball.is_fake or target.is_fake:
                    second_radius = Line._radius
                if distance < Ball._radius * 2:
                    if True:
                        # resolve static collision by overlap
                        overlap = 0.5 * (distance - Ball._radius - second_radius)
                        ball.pos -= overlap * (ball.pos - target.pos) / distance
                        target.pos += overlap * (ball.pos - target.pos) / distance
                    
                    Ball._collisions.append((ball, target))
        
        for ball, target in Ball._collisions:
            # check for first cue touch
            if all([Ball._first_cue_touch is None,
                    not ball.is_fake and not target.is_fake,
                    (ball.get_type() == BallType.BALL_CUE or target.get_type() == BallType.BALL_CUE)]):
                Ball._first_cue_touch = target.get_type() if target.get_type() != BallType.BALL_CUE else ball.get_type()

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
        size_multiplied = texture_mult
        self.surf = pygame.Surface((size_multiplied, size_multiplied), pygame.SRCALPHA)
        if self.number > 8 and self.number < 100:
            # stripe
            self.surf.fill(ball_color[0])
            self.surf.fill(color, ((0, size_multiplied * 0.25), (self.surf.get_width(), self.surf.get_height() - size_multiplied / 2)))
        else:
            # solid
            self.surf.fill(color)
        
        draw_number = True
        if self.number > 100:
            draw_number = False
        
        if draw_number:
            pygame.draw.circle(self.surf, ball_color[0], (size_multiplied / 2, size_multiplied / 2), size_multiplied * 0.25)

            if self.number != 0:
                text = ball_numbers_font.render(str(self.number), True, (0,0,0))
                self.surf.blit(text, (self.surf.get_width() / 2 - text.get_width() / 2, self.surf.get_height() / 2 - text.get_height() / 2))

        # apply mask
        mask = pygame.Surface((size_multiplied, size_multiplied), pygame.SRCALPHA)
        mask.fill((255,255,255,255))
        pygame.draw.circle(mask, (0,0,0,0), (size_multiplied / 2, size_multiplied / 2), size_multiplied / 2)
        self.surf.blit(mask, (0,0), special_flags=pygame.BLEND_RGBA_SUB)

        # scale
        self.surf = pygame.transform.smoothscale_by(self.surf, (2 * Ball._radius) / size_multiplied)

    def draw(self):
        win.blit(self.surf, self.pos - Vector2(Ball._radius, Ball._radius))
        if loaded_textures:
            pos = self.pos - Vector2(reflection_map.get_width() / 2, reflection_map.get_height() / 2)
            win.blit(reflection_map, pos)

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
        if loaded_textures:
            for ball in Ball._reg:
                pos = ball.pos - Vector2(shadow_map.get_width() / 2, shadow_map.get_height() / 2)
                win.blit(shadow_map, pos)
        for ball in Ball._reg:
            ball.draw()
        

class CueBall(Ball):
    def __init__(self, pos=Vector2(0,0)):
        super().__init__(pos)
        Ball._cue_ball = self
        self.is_out = False

    def new_turn(self):
        Ball._first_cue_touch = None
        Ball._potted_this_turn = []
    
    def get_first_touch(self):
        return Ball._first_cue_touch

    def get_potted_this_turn(self) -> List[BallType]:
        return Ball._potted_this_turn

    def set_pos(self, pos):
        self.pos = Vector2(pos)
    
    def strike(self, direction: Vector2, power: float):
        self.set_vel(direction.normalize() * power * 7.5)

    def potted(self):
        self.is_out = True
        Ball._potted_this_turn.append(self.get_type())
        Ball._reg.remove(self)

class Line:
    _reg: List['Line'] = []
    _radius = 5
    def __init__(self, start: Vector2, end: Vector2):
        Line._reg.append(self)
        self.start = start
        self.end = end

    def draw(self):
        color = (255,255,255)
        pygame.draw.line(win, color, self.start, self.end, Line._radius * 2)
        pygame.draw.circle(win, color, self.start, Line._radius)
        pygame.draw.circle(win, color, self.end, Line._radius)
        pygame.draw.line(win, (255,0,0), self.start, self.end)

    def draw_lines():
        if not draw_solids:
            return
        for line in Line._reg:
            line.draw()

class Hole:
    _reg: List['Hole'] = []
    def __init__(self, pos: Vector2, target_offset: Vector2, radius: float):
        Hole._reg.append(self)
        self.radius = radius
        self.pos = pos
        self.target_pos = pos + target_offset

    def step(self):
        for ball in Ball._reg:
            distance = ball.pos.distance_to(self.pos)
            if distance > self.radius + 0.5 * Ball._radius:
                continue

            # apply force
            force = (self.pos - ball.pos).normalize()
            ball.set_acc((self.radius / distance **2) * force)

            if distance < self.radius * 0.8:
                Ball._ball_to_remove.append(ball)
    
    def draw(self):
        if not draw_solids:
            return
        pygame.draw.circle(win, (0,0,0), self.pos, self.radius)
        pygame.draw.circle(win, (255,0,0), self.pos, self.radius, 1)
        draw_target = False
        if draw_target:
            pygame.draw.circle(win, (0,255,0), self.target_pos, 5)

