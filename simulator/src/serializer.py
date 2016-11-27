import simulator.settings as settings
import numpy as np
import pygame
import pygame.gfxdraw
from models import *

BACKGROUND_COLOR = (126, 130, 177)
STATION_COLOR = (8, 12, 59)
HUMAN_COLOR = (84, 89, 147)
TARGET_COLOR  = (84, 89, 170)
COPTER_COLOR = (8, 12, 59)
WALL_COLOR = (8, 12, 59)

COPTER_RADIUS = 10
ZOOM = 1

class Serializer:
   
    @staticmethod
    def cv_point(x, y):
        return [int(x * ZOOM), int((settings.HEIGHT - y) * ZOOM)]
    
    @staticmethod
    def draw_line(screen, p0, p1, color):
        pygame.gfxdraw.line(screen, p0[0], p0[1], p1[0], p1[1], color)

    @staticmethod
    def draw_circle(screen, center, r, color):
        pygame.gfxdraw.filled_circle(screen, center[0], center[1], r * ZOOM, color)
        pygame.gfxdraw.aacircle(screen, center[0], center[1], r * ZOOM, color)

    @staticmethod
    def serialize(room, screen):
        screen.fill(BACKGROUND_COLOR)

        for station in room.get_charging_stations():
            p0 = Serializer.cv_point(station.get_x() - 15, station.get_y())
            p1 = Serializer.cv_point(station.get_x() + 15, station.get_y())
            Serializer.draw_line(screen, p0, p1, STATION_COLOR)
            p0 = Serializer.cv_point(station.get_x(), station.get_y() - 15)
            p1 = Serializer.cv_point(station.get_x(), station.get_y() + 15)
            Serializer.draw_line(screen, p0, p1, STATION_COLOR)
       
        
        for wall in room.get_walls():
            p0 = Serializer.cv_point(*wall.get_point1())
            p1 = Serializer.cv_point(*wall.get_point2())
            Serializer.draw_line(screen, p0, p1, WALL_COLOR)

        for human in room.get_people():
            center = Serializer.cv_point(human.get_x(), human.get_y())
            Serializer.draw_circle(screen, center, Human.RADIUS, HUMAN_COLOR)
            if human.target is not None:
                center = Serializer.cv_point(*human.target)
                Serializer.draw_circle(screen, center, Human.RADIUS / 2, TARGET_COLOR)
        
        for copter in room.get_quadcopters():
            charge = max(0, copter.get_charge_level())

            center = Serializer.cv_point(copter.get_x(), copter.get_y())
            p0 = [center[0] - COPTER_RADIUS / 2, center[1] - COPTER_RADIUS / 2]
            p1 = [center[0] - COPTER_RADIUS / 2, center[1] + COPTER_RADIUS / 2]
            p2 = [center[0] + COPTER_RADIUS / 2, center[1] - COPTER_RADIUS / 2]
            p3 = [center[0] + COPTER_RADIUS / 2, center[1] + COPTER_RADIUS / 2]

            Serializer.draw_circle(screen, p0, COPTER_RADIUS / 4, COPTER_COLOR)
            Serializer.draw_circle(screen, p1, COPTER_RADIUS / 4, COPTER_COLOR)
            Serializer.draw_circle(screen, p2, COPTER_RADIUS / 4, COPTER_COLOR)
            Serializer.draw_circle(screen, p3, COPTER_RADIUS / 4, COPTER_COLOR)
        pygame.display.flip()
        
        """
        for station in room.get_charging_stations():
            cv2.line(frame, Serializer.cv_point(station.get_x() - 15, station.get_y()),
                     Serializer.cv_point(station.get_x() + 15, station.get_y()), (102, 0, 255))
            cv2.line(frame, Serializer.cv_point(station.get_x(), station.get_y() - 15),
                     Serializer.cv_point(station.get_x(), station.get_y() + 15), (102, 0, 255))
        for wall in room.get_walls():
            cv2.line(frame, Serializer.cv_point(*wall.get_point1()),
                     Serializer.cv_point(*wall.get_point2()), (255, 255, 255))
        for human in room.get_people():
            cv2.circle(frame, Serializer.cv_point(human.get_x(), human.get_y()), Human.RADIUS, (165, 0, 255))
            if human.target is not None:
                cv2.circle(frame, Serializer.cv_point(*human.target), Human.RADIUS / 4, (165, 0, 255))
        for copter in room.get_quadcopters():
            charge = max(0, copter.get_charge_level())
            cv2.circle(frame, Serializer.cv_point(copter.get_x(), copter.get_y()), 10,
                       (0, 255*charge, 255*(1.-charge)))
        """