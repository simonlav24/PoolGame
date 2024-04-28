'''
Main module
'''

import pygame
from pygame.math import Vector2
from math import sqrt
from random import shuffle
from typing import List, Tuple
import Physics
from Physics import Ball, Line, Hole, CueBall
from Calc import *
from StateMachine import *

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
                game_state.update_potted(cue_ball.get_potted_this_turn())
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
    