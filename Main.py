'''
Main module
'''

import pygame
from pygame.math import Vector2
import os
import asyncio
import random
from random import shuffle, choice
from typing import Dict, Tuple, List
import Physics
from Physics import Ball, Line, Hole, CueBall
from Calc import *
from StateMachine import *
import Cpu
import Guide
from Guide import AimGuide
from network.client import GameClient
from network.events import (
    EventFactory,
    EventType, 
    StrikePayload,
    Event)
from Models import *

DEBUG = False

class PoolGame:
    def __init__(self, rules: Rules, cpu_config: Dict[PlayerSpot, Tuple[Player_Type, int]], win: pygame.Surface, clock: pygame.time.Clock, online: bool=False):
        self.win = win
        self.clock = clock

        self.cpu_config = cpu_config
        self.pool_line = 450
        self.table_dims = None
        self.game_state = None
        self.cpus: List[Cpu.PlayerCpu] = []
        self.rules = rules

        self.table_center = Vector2(win.get_width() / 2, win.get_height() / 2)
        Ball._lamps = [
            self.table_center + Vector2(300, 0),
            self.table_center + Vector2(-300, 0),
            ]
    
        self.online = online
        self.online_player: PlayerSpot = PlayerSpot.PLAYER1

    def initialize(self):
        self.build_table()
        self.build_balls()
        
        match self.rules:
            case Rules.EIGHT_BALL:
                self.game_state = GameStateEightBall(self.table_dims)
            case Rules.SNOOKER:
                self.game_state = GameStateSnooker(self.table_dims)

        for key in self.cpu_config:
            player_type, dificulty = self.cpu_config[key]
            if player_type == Player_Type.CPU:
                match self.rules:
                    case Rules.EIGHT_BALL:
                        cpu_player = Cpu.PlayerCpuEightBall(self.game_state, key, dificulty=dificulty)
                    case Rules.SNOOKER:
                        cpu_player = Cpu.PlayerCpuSnooker(self.game_state, key, dificulty=dificulty)
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
        
        if not self.sprites_loaded:
            Physics.draw_solids = True

    def build_table(self):
        # build table
        pool_line = self.pool_line
        pool_slit = 29
        pool_d_slit = 36

        left = self.table_center[0] - pool_line
        right = self.table_center[0] + pool_line
        top = self.table_center[1] - pool_line / 2
        bottom = self.table_center[1] + pool_line / 2
        center = self.table_center[0]

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
        match self.rules:
            case Rules.EIGHT_BALL:
                numbers = [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15]
                shuffle(numbers)

                offx = self.table_center[0] + self.pool_line * 0.5 - 2 * Ball._radius
                offy = self.table_center[1] + Ball._radius

                ball_count = 0
                for i in range(6):
                    for j in range(-i, i, 2):
                        number = numbers.pop()
                        if ball_count == 4:
                            numbers.append(number)
                            number = 8
                        ball_pos = Vector2(Ball._radius * i * sqrt(3) + offx, Ball._radius * j + offy)
                        Ball(ball_pos, number=number)
                        ball_count += 1

                ball_pos = Vector2(self.table_center[0] - self.pool_line * 0.5, self.table_center[1])
                CueBall(ball_pos)

            case Rules.NINE_BALL:
                numbers = [2, 3, 4, 5, 6, 7, 8]
                shuffle(numbers)

                offx = self.table_center[0] + self.pool_line * 0.5 - 2 * Ball._radius
                offy = self.table_center[1] + Ball._radius

                ball_count = 0
                for i in range(5):
                    balls_in_col = - abs(i - 2) + 3
                    for j in range(-balls_in_col, balls_in_col, 2):
                        number = numbers.pop()
                        if ball_count == 0:
                            numbers.append(number)
                            number = 1
                        if ball_count == 4:
                            numbers.append(number)
                            number = 9
                        ball_pos = Vector2(Ball._radius * i * sqrt(3) + offx, Ball._radius * j + offy)
                        Ball(ball_pos, number=number)
                        ball_count += 1
                
                ball_pos = Vector2(self.table_center[0] - self.pool_line * 0.5, self.table_center[1])
                CueBall(ball_pos)
            
            case Rules.SNOOKER:
                offx = self.table_center[0] + self.pool_line * 0.5 - 2 * Ball._radius
                offy = self.table_center[1] + Ball._radius

                self.table_zero_pos = None
                self.table_last_pos = None

                ball_count = 0
                for i in range(6):
                    for j in range(-i, i, 2):
                        number = 101
                        ball_pos = Vector2(Ball._radius * i * sqrt(3) + offx, Ball._radius * j + offy)
                        if ball_count == 0:
                            self.table_zero_pos = ball_pos.copy()
                        if ball_count == 12:
                            self.table_last_pos = ball_pos.copy()
                        Ball(ball_pos, number=number)
                        ball_count += 1
                
                Ball(self.table_center - (self.pool_line * 0.5, -self.pool_line * 0.25), number=102)
                Ball(self.table_center - (self.pool_line * 0.5, self.pool_line * 0.25), number=103)
                Ball(self.table_center - (self.pool_line * 0.5, 0), number=104)
                Ball(Vector2(self.table_center), number=105)
                Ball(self.table_zero_pos + Vector2(-Ball._radius * 2, 0), number=106)
                Ball(self.table_last_pos + Vector2(Ball._radius * 4, 0), number=107)

                ball_pos = Vector2(self.table_center[0] - self.pool_line * 0.5 - Ball._radius * 4, self.table_center[1])
                CueBall(ball_pos)

    def respot_balls(self):
        respot_balls = self.game_state.get_respot()
        for ball in respot_balls:
            match ball:
                case BallType.SNOOKER_YELLOW:
                    Ball(self.table_center - (self.pool_line * 0.5, -self.pool_line * 0.25), number=102)
                case BallType.SNOOKER_GREEN:
                    Ball(self.table_center - (self.pool_line * 0.5, self.pool_line * 0.25), number=103)
                case BallType.SNOOKER_BROWN:
                    Ball(self.table_center - (self.pool_line * 0.5, 0), number=104)
                case BallType.SNOOKER_BLUE:
                    Ball(Vector2(self.table_center), number=105)
                case BallType.SNOOKER_PINK:
                    Ball(self.table_zero_pos + Vector2(-Ball._radius * 2, 0), number=106)
                case BallType.SNOOKER_BLACK:
                    Ball(self.table_last_pos + Vector2(Ball._radius * 4, 0), number=107)

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
                    if event.key == pygame.K_DELETE:
                        mouse_pos = Vector2(pygame.mouse.get_pos())
                        for ball in Ball._reg:
                            if ball.pos.distance_to(mouse_pos) < Ball._radius:
                                ball.potted()
                if event.type == pygame.KEYUP:
                    debug_move_ball = None
                if self.game_state.get_state() == State.PLAY:
                    if event.type == pygame.MOUSEBUTTONUP:
                        if event.button == 1:
                            
                            direction, power = self.guide.get_aim_power()

                            # data for sending
                            message = {
                                'action': 'strike',
                                'direction': {
                                    'x': direction.x,
                                    'y': direction.y
                                },
                                'power': power
                            }

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
                    # game stable, determine next turn
                    self.game_state.update_potted(Ball._cue_ball.get_potted_this_turn())
                    self.game_state.first_touch = Ball._cue_ball.get_first_touch()
                    self.game_state.update()
                    self.respot_balls()
                    Ball._cue_ball.new_turn()
            
            for cpu in self.cpus:
                cpu.step()
                if cpu.player == self.game_state.get_player():
                    self.guide.set_aim(cpu.get_direction())
            
            # draw
            win.fill((30, 30, 30))
            if self.sprites_loaded:
                win.blit(self.table_border_sprite, (self.table_center[0] - self.table_border_sprite.get_width() / 2, self.table_center[1] - self.table_border_sprite.get_height() / 2))
                win.blit(self.table_top_sprite, (self.table_center[0] - self.table_top_sprite.get_width() / 2, self.table_center[1] - self.table_top_sprite.get_height() / 2))

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
            text = self.game_state.get_info()
            player_turn_surf = font1.render(text, True, (255,255,255))
            win.blit(player_turn_surf, (10,10))

            pygame.display.update()
            clock.tick(60)

    def prepare_message(self, event_type: EventType, payload_data: Optional[Dict[str, Any]]=None) -> Event:
        if not payload_data:
            payload_data = {}

        payload_class = EventFactory.get_payload_model(event_type)
        payload = payload_class(**payload_data)
        event = EventFactory.create_event(event_type, payload, sender_id=self.client.player_id)
        return event

    async def main_loop_online(self):

        win = self.win
        clock = self.clock
        debug_move_ball = None

        done = False
        while not done:
            # handle message queue
            event = await self.client.get_event(0.01)

            if event is not None:
                print('handling event')
                if event.event_type == EventType.STRIKE:
                    print('Strike event received')
                    payload: StrikePayload = event.payload
                    direction = Vector2(payload.x, payload.y)
                    Ball._cue_ball.strike(direction, payload.power)
                    self.game_state.update()


            # handle pygame events
            for event in pygame.event.get():
                self.guide.handle_event(event)
                if event.type == pygame.QUIT:
                    done = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        # cpu debug
                        for cpu in self.cpus:
                            cpu.debug = not cpu.debug
                    if event.key == pygame.K_s:
                        # darw solids for debug
                        Physics.draw_solids = not Physics.draw_solids
                    if event.key == pygame.K_DELETE:
                        # delete ball for debug
                        mouse_pos = Vector2(pygame.mouse.get_pos())
                        for ball in Ball._reg:
                            if ball.pos.distance_to(mouse_pos) < Ball._radius:
                                ball.potted()
                if event.type == pygame.KEYUP:
                    debug_move_ball = None
                if self.game_state.get_state() == State.PLAY:
                    if self.game_state.get_player() == self.online_player:

                        if event.type == pygame.MOUSEBUTTONUP:
                            if event.button == 1:
                                
                                direction, power = self.guide.get_aim_power()
                                # prepare message strike
                                
                                payload_data = {
                                    'x': direction.x,
                                    'y': direction.y,
                                    'power': power,
                                    'player_id': self.client.player_id
                                }
                                
                                event = self.prepare_message(EventType.STRIKE, payload_data)

                                print('Striking')
                                # send message
                                await self.client.send_event(event)

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
                    # game stable, determine next turn
                    self.game_state.update_potted(Ball._cue_ball.get_potted_this_turn())
                    self.game_state.first_touch = Ball._cue_ball.get_first_touch()
                    self.game_state.update()
                    self.respot_balls()
                    Ball._cue_ball.new_turn()
            
            for cpu in self.cpus:
                cpu.step()
                if cpu.player == self.game_state.get_player():
                    self.guide.set_aim(cpu.get_direction())
            
            # draw
            win.fill((30, 30, 30))
            if self.sprites_loaded:
                win.blit(self.table_border_sprite, (self.table_center[0] - self.table_border_sprite.get_width() / 2, self.table_center[1] - self.table_border_sprite.get_height() / 2))
                win.blit(self.table_top_sprite, (self.table_center[0] - self.table_top_sprite.get_width() / 2, self.table_center[1] - self.table_top_sprite.get_height() / 2))

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
            text = f'{self.online_player}          ' + self.game_state.get_info()
            player_turn_surf = font1.render(text, True, (255,255,255))
            win.blit(player_turn_surf, (10,10))

            pygame.display.update()
            clock.tick(60)

    def start_game(self):
        if not self.online:
            self.initialize()
            self.main_loop()
        
        else:
            asyncio.run(self.start_online_game())


    async def start_online_game(self):
        self.client = GameClient()
        try:
            spot, seed = self.client.run()
            print(f"Joined as {spot} with seed {seed}")
        except Exception as e:
            print(e)
        finally:
            asyncio.get_event_loop().run_until_complete(self.client.close())   

        # create client
        # self.client = GameClient()
        # spot, seed = self.client.run()
        
        # call server to determine my spot
        self.online_player: PlayerSpot = spot
        print('im player', self.online_player)

        random.seed(seed)
        self.initialize()
        await self.main_loop_online()


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
        PlayerSpot.PLAYER1: (Player_Type.HUMAN, 3),
        PlayerSpot.PLAYER2: (Player_Type.HUMAN, 3),
    }

    online = True

    game = PoolGame(Rules.EIGHT_BALL, cpu_config=cpu_config, win=win, clock=clock, online=online)
    game.start_game()

    pygame.quit()
    