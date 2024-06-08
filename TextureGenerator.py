



import pygame
from pygame.math import Vector2
from Physics import ball_color
from SpinTextureGenerator import create_spin_texture

TEX_SIZE = (1600, 800)

def create_texture(font):
    white = ball_color[0]
    font = pygame.font.SysFont(font, int(TEX_SIZE[1] * 0.15))
    # font.bold = True
    for ball_number in range(16):
        color = ball_color[ball_number]
        surface = pygame.Surface(TEX_SIZE)
        if ball_number > 8:
            surface.fill(white)
            stripe_width = TEX_SIZE[1] * 0.45
            surface.fill(color, (0, TEX_SIZE[1] / 2 - stripe_width / 2, TEX_SIZE[0], stripe_width))
        else:
            surface.fill(color)
        radius = TEX_SIZE[1] * 0.25 * 0.5
        if ball_number == 0:
            pygame.draw.circle(surface, ball_color[3], (TEX_SIZE[0] * 0, TEX_SIZE[1] * 0.5), radius * 0.25)
            pygame.draw.circle(surface, ball_color[3], (TEX_SIZE[0] * 0.25, TEX_SIZE[1] * 0.5), radius * 0.25)
            pygame.draw.circle(surface, ball_color[3], (TEX_SIZE[0] * 0.5, TEX_SIZE[1] * 0.5), radius * 0.25)
            pygame.draw.circle(surface, ball_color[3], (TEX_SIZE[0] * 0.75, TEX_SIZE[1] * 0.5), radius * 0.25)
            pygame.draw.circle(surface, ball_color[3], (TEX_SIZE[0] * 1, TEX_SIZE[1] * 0.5), radius * 0.25)
        else:
            pygame.draw.circle(surface, white, (TEX_SIZE[0] * 0.25, TEX_SIZE[1] * 0.5), radius)
            pygame.draw.circle(surface, white, (TEX_SIZE[0] * 0.75, TEX_SIZE[1] * 0.5), radius)
            text = font.render(str(ball_number), True, ball_color[8])
            surface.blit(text, (TEX_SIZE[0] * 0.25 - text.get_width() / 2, TEX_SIZE[1] * 0.5 - text.get_height() / 2))
            surface.blit(text, (TEX_SIZE[0] * 0.75 - text.get_width() / 2, TEX_SIZE[1] * 0.5 - text.get_height() / 2))

        pygame.image.save(surface, f'Assets/ball_{ball_number}.png')

def key_spin_textures():
    pygame.init()
    for ball_number in range(16):
        path = f'Assets/ball_{ball_number}_spin.png'
        loaded = pygame.image.load(path)
        output = pygame.Surface(loaded.get_size(), pygame.SRCALPHA)
        loaded.set_colorkey((0,0,0))
        output.blit(loaded, (0,0))
        pygame.image.save(output, path)
    pygame.quit()

if __name__ == '__main__':
    pygame.init()
    pygame.font.init()

    create_texture('Impact')
    create_spin_texture()
    key_spin_textures()
    