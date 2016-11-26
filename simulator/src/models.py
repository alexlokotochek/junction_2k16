import api.quadcopter as api
from random import randint


class QuadcopterController(api.QuadcopterController):
    POWER_TO_VELOCITY = 0.01

    def __init__(self, quadcopter):
        self.quadcopter = quadcopter
        self.x_velocity = 0
        self.y_velocity = 0
        self.is_landed = True

    def set_y_velocity(self, power):
        assert power >= -100 and power <= 100
        self.y_velocity += power * QuadcopterController.POWER_TO_VELOCITY

    def set_x_velocity(self, power):
        assert power >= -100 and power <= 100
        self.x_velocity += power * QuadcopterController.POWER_TO_VELOCITY

    def land(self):
        self.is_landed = True

    def take_off(self):
        self.is_landed = False


class Quadcopter:
    id_counter = 0
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.controller = QuadcopterController(self)
        self.id = Quadcopter.id_counter
        Quadcopter.id_counter += 1

    def get_controller(self):
        return self.controller

    def get_id(self):
        return self.id

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y


class Human(api.Human):
    id_counter = 0
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.id = Human.id_counter
        Human.id_counter += 1

    def get_id(self):
        return self.id

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y


class ChargingStation(api.ChargingStation):
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y


class Wall:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    # (x, y)
    def get_point1(self):
        return self.p1

    def get_point2(self):
        return self.p2

class Room(api.Room):
    def __init__(self, settings):
        self.walls = []
        for wall in settings.wals:
            self.walls.append(Wall(wall[0], wall[1]))
        self.charging_stations = []
        for charging_station in settings.charging_stations:
            self.charging_stations.append(ChargingStation(charging_station[0], charging_station[1]))
        self.enter_point = settings.enter_point
        self.people = []
        self.quadcopters = []
        for _ in range(settings.copters_count):
            station = self.charging_stations[randint(0, len(self.charging_stations))]
            self.quadcopters.append(Quadcopter(station.get_x(), station.get_y()))

    def get_walls(self):
        return self.walls

    def get_charging_stations(self):
        return self.charging_stations

    def get_people(self):
        return self.people

    def get_quadcopters(self):
        return self.quadcopters

