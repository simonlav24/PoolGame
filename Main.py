
import pygame
import PoolGame
import PygameGui as pg
from enum import Enum

class Room(Enum):
    EXIT = 0
    MAIN_MENU = 1
    GAME = 2


def main_menu(win) -> Room:
    clock = pygame.time.Clock()

    layout = [
        [pg.Button('Play', '-play-'), pg.Button('Exit', '-exit-')],
    ]

    gui = pg.Gui(win, layout, pos=(100,100))

    result = Room.EXIT

    done = False
    while not done:
        for event in pygame.event.get():
            gui.handle_event(event)
            if event.type == pygame.QUIT:
                done = True
        
        gui.step()

        event, values = gui.read()
        if event:
            if event == '-play-':
                result = Room.GAME
                done = True
            if event == '-exit-':
                result = Room.EXIT
                done = True

        win.fill((0,0,0))
        gui.draw()

        pygame.display.update()
        clock.tick(30)
    
    return result

def game(win) -> Room:
    PoolGame.main(win)
    return Room.MAIN_MENU

def main():
    pygame.init()
    win = pygame.display.set_mode((1280, 800))

    room = Room.MAIN_MENU

    done = False
    while not done:
        match room:
            case Room.MAIN_MENU:
                result = main_menu(win)
                room = result

            case Room.GAME:
                result = game(win)
                room = result
            
            case Room.EXIT:
                done = True
    
    pygame.quit()


if __name__ == '__main__':
    main()