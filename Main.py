'''
Main module
'''

import pygame
from pygame.math import Vector2
from random import shuffle
import Physics
from Physics import Ball, Line, Hole, CueBall, Guide
from Calc import *
from StateMachine import *
import Cpu
from Cpu import PlayerCpu

DEBUG = False

if __name__ == '__main__':

    pygame.init()
    win = pygame.display.set_mode((1280, 800))
    clock = pygame.time.Clock()

    font1 = pygame.font.SysFont('Arial', 16)
    font_small = pygame.font.SysFont('Arial', 10)

    Physics.win = win
    Physics.font_small = font_small

    types = [BallType.BALL_SOLID] * 7 + [BallType.BALL_STRIPE] * 7
    shuffle(types)
    solid_numbers = [1, 2, 3, 4, 5, 6, 7]
    shuffle(solid_numbers)
    stripe_numbers = [9, 10, 11, 12, 13, 14, 15]
    shuffle(stripe_numbers)
    number_type = {BallType.BALL_SOLID: solid_numbers, BallType.BALL_STRIPE: stripe_numbers}

    offx = win.get_width() / 2
    offy = win.get_height() / 2 + 150

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
            Ball(Vector2(10 * j + offx, 10 * i * sqrt(3) + offy), type=type, number=number)
            ball_count += 1

    # Ball(Vector2(offx, offy), type=type, number=1)
    cue_ball = CueBall(Vector2(win.get_width() / 2, 200))

    pool_line = 350
    pool_slit = 25
    pool_d_slit = 35

    left = win.get_width() / 2 - pool_line / 2
    right = win.get_width() / 2 + pool_line / 2
    top = win.get_height() / 2 - pool_line
    bottom = win.get_height() / 2 + pool_line
    center = win.get_height() / 2

    # table lines
    Line(Vector2(left, top + pool_d_slit), Vector2(left, center - pool_slit))
    Line(Vector2(left, bottom - pool_d_slit), Vector2(left, center + pool_slit))
    Line(Vector2(left + pool_d_slit, bottom), Vector2(right - pool_d_slit, bottom))
    Line(Vector2(right, bottom - pool_d_slit), Vector2(right, center + pool_slit))
    Line(Vector2(right, center - pool_slit), Vector2(right, top + pool_d_slit))
    Line(Vector2(left + pool_d_slit, top), Vector2(right - pool_d_slit, top))

    # pot lines
    d_offset = 40 
    Line(Vector2(left, top + pool_d_slit), Vector2(left - d_offset, top + pool_d_slit - d_offset))
    Line(Vector2(left + pool_d_slit, top), Vector2(left + pool_d_slit - d_offset, top - d_offset))
    Line(Vector2(left - d_offset, top + pool_d_slit - d_offset), Vector2(left + pool_d_slit - d_offset, top - d_offset))

    Line(Vector2(right - pool_d_slit, top), Vector2(right - pool_d_slit + d_offset, top - d_offset))
    Line(Vector2(right, top + pool_d_slit), Vector2(right + d_offset, top + pool_d_slit - d_offset))
    Line(Vector2(right - pool_d_slit + d_offset, top - d_offset), Vector2(right + d_offset, top + pool_d_slit - d_offset))

    Line(Vector2(left + pool_d_slit, bottom), Vector2(left + pool_d_slit - d_offset, bottom + d_offset))
    Line(Vector2(left, bottom - pool_d_slit), Vector2(left - d_offset, bottom - pool_d_slit + d_offset))
    Line(Vector2(left + pool_d_slit - d_offset, bottom + d_offset), Vector2(left - d_offset, bottom - pool_d_slit + d_offset))

    Line(Vector2(right, bottom - pool_d_slit), Vector2(right + d_offset, bottom - pool_d_slit + d_offset))
    Line(Vector2(right - pool_d_slit, bottom), Vector2(right - pool_d_slit + d_offset, bottom + d_offset))
    Line(Vector2(right + d_offset, bottom - pool_d_slit + d_offset), Vector2(right - pool_d_slit + d_offset, bottom + d_offset))

    s_offset = 25
    Line(Vector2(right, center - pool_slit), Vector2(right + s_offset, center - pool_slit))
    Line(Vector2(right, center + pool_slit), Vector2(right + s_offset, center + pool_slit))
    Line(Vector2(right + s_offset, center - pool_slit), Vector2(right + s_offset, center + pool_slit))

    Line(Vector2(left, center + pool_slit), Vector2(left - s_offset, center + pool_slit))
    Line(Vector2(left, center - pool_slit), Vector2(left - s_offset, center - pool_slit))
    Line(Vector2(left - s_offset, center + pool_slit), Vector2(left - s_offset, center - pool_slit))
    
    hole_diagonal_offset = 20
    hole_horizontal_offset = 10
    Hole(Vector2(left, center), Vector2(hole_horizontal_offset, 0))
    Hole(Vector2(right, center), Vector2(-hole_horizontal_offset, 0))
    Hole(Vector2(left, top), Vector2(hole_diagonal_offset, hole_diagonal_offset))
    Hole(Vector2(right, top), Vector2(-hole_diagonal_offset, hole_diagonal_offset))
    Hole(Vector2(left, bottom), Vector2(hole_diagonal_offset, -hole_diagonal_offset))
    Hole(Vector2(right, bottom), Vector2(-hole_diagonal_offset, -hole_diagonal_offset))

    guide = Guide()
    game_state = GameState()
    Cpu.win = win

    # cpu1 = PlayerCpu(game_state, Player.PLAYER_1)
    cpu2 = PlayerCpu(game_state, Player.PLAYER_2)

    done = False
    while not done:
        # --- Main event loop
        for event in pygame.event.get():
            guide.handle_event(event)
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    for cpu in PlayerCpu._reg:
                        cpu.debug = not cpu.debug
            if game_state.get_state() == State.PLAY:
                if event.type == pygame.MOUSEBUTTONUP:
                    direction, power = guide.get_aim_power()
                    cue_ball.set_vel(direction * power * 0.05)
                    game_state.update()
            elif game_state.get_state() == State.MOVING_CUE_BALL:
                if event.type == pygame.MOUSEBUTTONUP:
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
                game_state.update_potted(cue_ball.get_potted_this_turn())
                game_state.first_touch = cue_ball.get_first_touch()
                game_state.update()
                cue_ball.new_turn()
        
        for cpu in PlayerCpu._reg:
            cpu.step()
        
        # draw
        win.fill((0, 150, 0))
        for hole in Hole._reg:
            hole.draw()
        Ball.draw_balls()
        Line.draw_lines()

        for cpu in PlayerCpu._reg:
            cpu.draw()

        # draw guides
        if game_state.get_state() == State.PLAY:
            guide.draw()
        
        if game_state.get_state() == State.MOVING_CUE_BALL:
            pygame.draw.circle(win, (255,255,255), pygame.mouse.get_pos(), Ball._radius, 1)

        # draw entered balls
        for i, ball in enumerate(Ball._entered_balls):
            pos = Vector2(right + Ball._radius * 8, Ball._radius + i * 2 * Ball._radius)
            win.blit(ball.surf, pos)

        # temporarily display info
        if game_state.get_state() != State.GAME_OVER:
            text = f'{str(game_state.get_player())}: {game_state.player_ball_type[game_state.get_player()]}'
        else:
            text = f'Game Over, {game_state.player_winner} Won'
        player_turn_surf = font1.render(text, True, (0,0,0))
        win.blit(player_turn_surf, (10,10))

        pygame.display.update()
        clock.tick(60)

    pygame.quit()
    