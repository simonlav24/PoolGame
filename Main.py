'''
Main module
'''

import pygame
from pygame.math import Vector2
from random import shuffle
import Physics
from Physics import Ball, Line, Hole, CueBall
from Calc import *
from StateMachine import *
import Cpu
from Cpu import PlayerCpu
import Guide
from Guide import AimGuide

DEBUG = False

if __name__ == '__main__':

    pygame.init()
    win = pygame.display.set_mode((1280, 800))
    clock = pygame.time.Clock()

    font1 = pygame.font.SysFont('Arial', 16)
    font_small = pygame.font.SysFont('Arial', 10)

    Physics.win = win
    Physics.font_small = font_small

    
    # build table
    pool_line = 450
    pool_slit = 29
    pool_d_slit = 36

    left = win.get_width() / 2 - pool_line
    right = win.get_width() / 2 + pool_line
    top = win.get_height() / 2 - pool_line / 2
    bottom = win.get_height() / 2 + pool_line / 2
    center = win.get_width() / 2

    # table lines
    Line(Vector2(left, top + pool_d_slit), Vector2(left, bottom - pool_d_slit))
    Line(Vector2(right, top + pool_d_slit), Vector2(right, bottom - pool_d_slit))
    Line(Vector2(left + pool_d_slit, top), Vector2(center - pool_slit, top))
    Line(Vector2(center + pool_slit, top), Vector2(right - pool_d_slit, top))
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

    # build balls
    types = [BallType.BALL_SOLID] * 7 + [BallType.BALL_STRIPE] * 7
    shuffle(types)
    solid_numbers = [1, 2, 3, 4, 5, 6, 7]
    shuffle(solid_numbers)
    stripe_numbers = [9, 10, 11, 12, 13, 14, 15]
    shuffle(stripe_numbers)
    number_type = {BallType.BALL_SOLID: solid_numbers, BallType.BALL_STRIPE: stripe_numbers}

    offx = win.get_width() / 2 + pool_line * 0.5 - 2 * Ball._radius
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

    cue_ball = CueBall(Vector2(win.get_width() / 2 - pool_line * 0.5, win.get_height() / 2))

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

    bg_sprite = pygame.transform.scale_by(pygame.image.load(r'./tableSprite.png'), 0.6)

    game_state = GameState()
    Cpu.win = win
    Guide.win = win

    # cpu1 = PlayerCpu(game_state, Player.PLAYER_1)
    cpu2 = PlayerCpu(game_state, Player.PLAYER_2, dificulty=1)

    guide = AimGuide(game_state, [cpu.player for cpu in PlayerCpu._reg])

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
                    if event.button == 1:
                        direction, power = guide.get_aim_power()
                        cue_ball.strike(direction, power)
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
        if keys[pygame.K_m]:
            for ball in Ball._reg:
                distance = ball.pos.distance_to(pygame.mouse.get_pos())
                if distance > Ball._radius / 2:
                    force = (pygame.mouse.get_pos() - ball.pos).normalize()
                    ball.set_acc((Ball._radius / distance **2) * force)

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
            if cpu.player == game_state.get_player():
                guide.set_aim(cpu.get_direction())
        
        # draw
        win.fill((0, 150, 0))
        # win.blit(bg_sprite, (win.get_width() / 2 - bg_sprite.get_width() / 2, win.get_height() / 2 - bg_sprite.get_height() / 2))
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
    