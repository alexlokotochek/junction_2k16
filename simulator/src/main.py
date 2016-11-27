import simulator.settings as settings
import numpy as np
import models
from royal_manager import RoyalManager
from serializer import Serializer
from serializer import ZOOM
from strategy.strategy import Strategy
import pygame

def main():
    pygame.init()
 
    # Set the width and height of the screen [width, height]
    size = (int(settings.WIDTH * ZOOM), int(settings.HEIGHT * ZOOM))
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Simulator")

    royal_manager = RoyalManager()
    room = royal_manager.room
    strategy = Strategy(room)
    done = False
    clock = pygame.time.Clock()
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
        strategy.run_tick()
        royal_manager.run_simulation_tick()
        Serializer.serialize(room, screen)
        clock.tick(60)

pygame.quit()

if __name__ == '__main__':
    main()
