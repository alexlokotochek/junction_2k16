import simulator.settings as settings
import cv2
import numpy as np
import models
from royal_manager import RoyalManager
from serializer import Serializer
from strategy.strategy import Strategy

def main():
    royal_manager = RoyalManager()
    room = royal_manager.room
    strategy = Strategy(room)
    frame = np.ndarray([settings.HEIGHT, settings.WIDTH, 3])
    while True:
        strategy.run_tick()
        royal_manager.run_simulation_tick()
        Serializer.serialize(room, frame)
        cv2.imshow('simulator', frame)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
