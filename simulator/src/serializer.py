import simulator.settings as settings
import numpy as np
import cv2


class Serializer:
    @staticmethod
    def cv_point(x, y):
        return (x, settings.HEIGHT - y)

    @staticmethod
    def serialize(room, frame):
        frame.fill(0)
        for station in room.get_charging_stations():
            cv2.line(frame, Serializer.cv_point(station.get_x() - 15, station.get_y()),
                     Serializer.cv_point(station.get_x() + 15, station.get_y()), (102, 0, 255))
            cv2.line(frame, Serializer.cv_point(station.get_x(), station.get_y() - 15),
                     Serializer.cv_point(station.get_x(), station.get_y() + 15), (102, 0, 255))
        for wall in room.get_walls():
            cv2.line(frame, Serializer.cv_point(*wall.get_point1()),
                     Serializer.cv_point(*wall.get_point2()), (255, 255, 255))
        for human in room.get_people():
            cv2.circle(frame, Serializer.cv_point(human.get_x(), human.get_y()), 20, (255, 165, 0))
        for copter in room.get_quadcopters():
            charge = copter.get_charge_level()
            cv2.circle(frame, Serializer.cv_point(copter.get_x(), copter.get_y()), 10, (255 * (1-charge), 255*charge, 0))