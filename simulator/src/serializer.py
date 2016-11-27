import simulator.settings as settings
import numpy as np
import pygame
import pygame.gfxdraw
from models import *

BACKGROUND_COLOR = (126, 130, 177)
STATION_COLOR = (8, 12, 59)
HUMAN_COLOR = (84, 89, 147)
KINECT_MAN_COLOR = (255, 0, 0)
TARGET_COLOR  = (84, 89, 170)
COPTER_COLOR = (8, 12, 59)
WALL_COLOR = (8, 12, 59)

COPTER_RADIUS = 10
ZOOM = 1.5

class Serializer:
   
    @staticmethod
    def cv_point(x, y):
        return [int(x * ZOOM), int((settings.HEIGHT - y) * ZOOM)]
    
    @staticmethod
    def draw_line(screen, p0, p1, color):
        pygame.gfxdraw.line(screen, p0[0], p0[1], p1[0], p1[1], color)

    @staticmethod
    def draw_circle(screen, center, r, color):
        pygame.gfxdraw.filled_circle(screen, center[0], center[1], int(r * ZOOM), color)
        pygame.gfxdraw.aacircle(screen, center[0], center[1], int(r * ZOOM), color)

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
            color = KINECT_MAN_COLOR if isinstance(human, KinectMan) else HUMAN_COLOR
            Serializer.draw_circle(screen, center, Human.RADIUS, color)
            if human.target is not None:
                center = Serializer.cv_point(*human.target)
                Serializer.draw_circle(screen, center, Human.RADIUS / 2, TARGET_COLOR)
        
        for copter in room.get_quadcopters():
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
