'''
Main module
'''

import pygame
from pygame.math import Vector2
import os
from random import shuffle, choice
from typing import Dict, Tuple, List
import Physics
from Physics import Ball, Line, Hole, CueBall
from Calc import *
from StateMachine import *
import Cpu
from Cpu import PlayerCpu
import Guide
from Guide import AimGuide

DEBUG = False

class PoolGame:
    def __init__(self, rules: Rules, cpu_config: Dict[Player, Tuple[Player_Type, int]], win: pygame.Surface, clock: pygame.time.Clock):
        self.win = win
        self.clock = clock

        self.cpu_config = cpu_config
        self.pool_line = 450
        self.table_dims = None
        self.game_state = None
        self.cpus: List[PlayerCpu] = []
        self.rules = rules

    def initialize(self):
        self.build_table()
        self.build_balls()
        
        self.game_state = GameState(self.table_dims)

        for key in self.cpu_config:
            player_type, dificulty = self.cpu_config[key]
            if player_type == Player_Type.CPU:
                cpu_player = PlayerCpu(self.game_state, key, dificulty=dificulty)
                self.cpus.append(cpu_player)

        self.guide = AimGuide(self.game_state, [cpu.player for cpu in self.cpus])

        self.load_sprites()

    def load_sprites(self):
        # load sprites
        self.sprites_loaded = True
        try:
            self.table_border_sprite = pygame.transform.smoothscale_by(pygame.image.load(r'Assets/Border.png'), 0.6)
            table_colors = []
            for path in os.listdir('Assets'):
                if path.startswith('Table') and path.endswith('.png'):
                    table_colors.append(os.path.join('Assets', path))
            table_path = choice(table_colors)
            self.table_top_sprite = pygame.transform.smoothscale_by(pygame.image.load(table_path), 0.6)
        except Exception:
            self.sprites_loaded = False
            Physics.draw_solids = True

    def build_table(self):
        # build table
        pool_line = self.pool_line
        pool_slit = 29
        pool_d_slit = 36

        left = win.get_width() / 2 - pool_line
        right = win.get_width() / 2 + pool_line
        top = win.get_height() / 2 - pool_line / 2
        bottom = win.get_height() / 2 + pool_line / 2
        center = win.get_width() / 2

        self.table_dims = {
            'left': left,
            'right': right,
            'top': top,
            'bottom': bottom,
            'center': center,
        }

        # table lines
        Line(Vector2(left, top + pool_d_slit), Vector2(left, bottom - pool_d_slit))
        Line(Vector2(right, bottom - pool_d_slit), Vector2(right, top + pool_d_slit))
        Line(Vector2(center - pool_slit, top), Vector2(left + pool_d_slit, top))
        Line(Vector2(right - pool_d_slit, top), Vector2(center + pool_slit, top))
        Line(Vector2(left + pool_d_slit, bottom), Vector2(center - pool_slit, bottom))
        Line(Vector2(center + pool_slit, bottom), Vector2(right - pool_d_slit, bottom))

        slit_offset = 45
        slit_d_offset = 50
        slit_center_offset = 10
        Line(Vector2(left, top + pool_d_slit), Vector2(left - slit_d_offset, top + pool_d_slit - slit_d_offset))
        Line(Vector2(left + pool_d_slit, top), Vector2(left + pool_d_slit - slit_d_offset, top - slit_d_offset))
        Line(Vector2(right, top + pool_d_slit), Vector2(right + slit_d_offset, top + pool_d_slit - slit_d_offset))
        Line(Vector2(right - pool_d_slit, top), Vector2(right - pool_d_slit + slit_d_offset, top - slit_d_offset))

        Line(Vector2(left, bottom - pool_d_slit), Vector2(left - slit_d_offset, bottom - pool_d_slit + slit_d_offset))
        Line(Vector2(left + pool_d_slit, bottom), Vector2(left + pool_d_slit - slit_d_offset, bottom + slit_d_offset))
        Line(Vector2(right, bottom - pool_d_slit), Vector2(right + slit_d_offset, bottom - pool_d_slit + slit_d_offset))
        Line(Vector2(right - pool_d_slit, bottom), Vector2(right - pool_d_slit + slit_d_offset, bottom + slit_d_offset))

        Line(Vector2(center - pool_slit, top), Vector2(center - pool_slit + slit_center_offset, top - slit_offset))
        Line(Vector2(center + pool_slit, top), Vector2(center + pool_slit - slit_center_offset, top - slit_offset))
        Line(Vector2(center - pool_slit, bottom), Vector2(center - pool_slit + slit_center_offset, bottom + slit_offset))
        Line(Vector2(center + pool_slit, bottom), Vector2(center + pool_slit - slit_center_offset, bottom + slit_offset))
        Line._reg.reverse()

        # build holes
        hole_diagonal_offset = 30
        hole_vertical_offset = 25
        hole_radius = Ball._radius * 1.75
        hole_d_radius = Ball._radius * 2
        diagonal_adjust = 10
        vertical_adjust = 23
        Hole(Vector2(left - diagonal_adjust, top - diagonal_adjust), Vector2(hole_diagonal_offset, hole_diagonal_offset), hole_d_radius)
        Hole(Vector2(left - diagonal_adjust, bottom + diagonal_adjust), Vector2(hole_diagonal_offset, -hole_diagonal_offset), hole_d_radius)
        Hole(Vector2(right + diagonal_adjust, top - diagonal_adjust), Vector2(-hole_diagonal_offset, hole_diagonal_offset), hole_d_radius)
        Hole(Vector2(right + diagonal_adjust, bottom + diagonal_adjust), Vector2(-hole_diagonal_offset, -hole_diagonal_offset), hole_d_radius)
        Hole(Vector2(center, top - vertical_adjust), Vector2(0, hole_vertical_offset), hole_radius)
        Hole(Vector2(center, bottom + vertical_adjust), Vector2(0, -hole_vertical_offset), hole_radius)
    

    def build_balls(self):
        # build balls
        types = [BallType.BALL_SOLID] * 7 + [BallType.BALL_STRIPE] * 7
        shuffle(types)
        solid_numbers = [1, 2, 3, 4, 5, 6, 7]
        shuffle(solid_numbers)
        stripe_numbers = [9, 10, 11, 12, 13, 14, 15]
        shuffle(stripe_numbers)
        number_type = {BallType.BALL_SOLID: solid_numbers, BallType.BALL_STRIPE: stripe_numbers}

        offx = win.get_width() / 2 + self.pool_line * 0.5 - 2 * Ball._radius
        offy = win.get_height() / 2 + Ball._radius

        ball_count = 0
        for i in range(6):
            for j in range(-i, i, 2):
                type = types.pop()
                number = number_type[type].pop()
                if ball_count == 4:
                    types.append(type)
                    number_type[type].append(number)
                    type = BallType.BALL_BLACK
                    number = 8
                Ball(Vector2(Ball._radius * i * sqrt(3) + offx, Ball._radius * j + offy), type=type, number=number)
                ball_count += 1

        CueBall(Vector2(win.get_width() / 2 - self.pool_line * 0.5, win.get_height() / 2))

    def main_loop(self):
        win = self.win
        clock = self.clock
        debug_move_ball = None

        done = False
        while not done:
            # --- Main event loop
            for event in pygame.event.get():
                self.guide.handle_event(event)
                if event.type == pygame.QUIT:
                    done = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        for cpu in self.cpus:
                            cpu.debug = not cpu.debug
                    if event.key == pygame.K_s:
                        Physics.draw_solids = not Physics.draw_solids
                if event.type == pygame.KEYUP:
                    debug_move_ball = None
                if self.game_state.get_state() == State.PLAY:
                    if event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:
                            direction, power = self.guide.get_aim_power()
                            Ball._cue_ball.strike(direction, power)
                            self.game_state.update()
                elif self.game_state.get_state() == State.MOVING_CUE_BALL:
                    if event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:
                            if Ball._cue_ball.is_out:
                                Ball._cue_ball = CueBall(pygame.mouse.get_pos())
                            else:
                                Ball._cue_ball.set_pos(pygame.mouse.get_pos())
                            self.game_state.update()
            
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                done = True

            if keys[pygame.K_m]:
                mouse_pos = Vector2(pygame.mouse.get_pos())
                if debug_move_ball:
                    debug_move_ball.pos = mouse_pos
                else:
                    for ball in Ball._reg:
                        if ball.pos.distance_to(mouse_pos) < Ball._radius:
                            debug_move_ball = ball

            # step
            Ball.step_balls()
            for hole in Hole._reg:
                hole.step()
            if self.game_state.get_state() == State.WAIT_FOR_STABLE:
                if Ball.check_stability():
                    # determine next turn
                    self.game_state.update_potted(Ball._cue_ball.get_potted_this_turn())
                    self.game_state.first_touch = Ball._cue_ball.get_first_touch()
                    self.game_state.update()
                    Ball._cue_ball.new_turn()
            
            for cpu in self.cpus:
                cpu.step()
                if cpu.player == self.game_state.get_player():
                    self.guide.set_aim(cpu.get_direction())
            
            # draw
            win.fill((30, 30, 30))
            if self.sprites_loaded:
                win.blit(self.table_border_sprite, (win.get_width() / 2 - self.table_border_sprite.get_width() / 2, win.get_height() / 2 - self.table_border_sprite.get_height() / 2))
                win.blit(self.table_top_sprite, (win.get_width() / 2 - self.table_top_sprite.get_width() / 2, win.get_height() / 2 - self.table_top_sprite.get_height() / 2))

            for hole in Hole._reg:
                hole.draw()
            Ball.draw_balls()
            Line.draw_lines()

            for cpu in self.cpus:
                cpu.draw()

            # draw guides
            if self.game_state.get_state() == State.PLAY:
                self.guide.draw()
            
            if self.game_state.get_state() == State.MOVING_CUE_BALL:
                pygame.draw.circle(win, (255,255,255), pygame.mouse.get_pos(), Ball._radius, 1)

            # draw entered balls
            for i, ball in enumerate(Ball._entered_balls):
                pos = Vector2(self.table_dims['right'] + Ball._radius * 8, Ball._radius + i * 2 * Ball._radius)
                win.blit(ball.surf, pos)

            # temporarily display info
            if self.game_state.get_state() != State.GAME_OVER:
                text = f'{str(self.game_state.get_player())}: {self.game_state.player_ball_type[self.game_state.get_player()]}'
            else:
                text = f'Game Over, {self.game_state.player_winner} Won'
            player_turn_surf = font1.render(text, True, (255,255,255))
            win.blit(player_turn_surf, (10,10))

            pygame.display.update()
            clock.tick(60)

if __name__ == '__main__':

    pygame.init()
    win = pygame.display.set_mode((1280, 800))
    clock = pygame.time.Clock()

    font1 = pygame.font.SysFont('Arial', 16)

    Physics.win = win
    Physics.initialize()
    Cpu.win = win
    Guide.win = win

    cpu_config = {
        Player.PLAYER_1: (Player_Type.HUMAN, 3),
        Player.PLAYER_2: (Player_Type.CPU, 2),
    }

    game = PoolGame(Rules.BALL_8, cpu_config=cpu_config, win=win, clock=clock)
    game.initialize()
    game.main_loop()

    pygame.quit()
    