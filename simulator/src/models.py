import api.quadcopter as api
from random import randint
import simulator.settings as settings
import math


def distance(p1, p2):
    d = (p2[0] - p1[0], p2[1] - p1[1])
    return math.sqrt(d[0] * d[0] + d[1] * d[1])


def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


class QuadcopterController(api.QuadcopterController):
    POWER_TO_VELOCITY = 0.0005
    MAX_SPEED = 2

    @staticmethod
    def validate_velocity(velocity):
        if abs(velocity) > QuadcopterController.MAX_SPEED:
            velocity = QuadcopterController.MAX_SPEED * sign(velocity)
        return velocity

    def __init__(self, quadcopter):
        self.quadcopter = quadcopter
        self.x_velocity = 0.0
        self.y_velocity = 0.0
        self.is_landed = True

    def set_y_velocity(self, power):
        assert power >= -100 and power <= 100 and not self.is_landed
        self.y_velocity = QuadcopterController.validate_velocity(self.y_velocity +
            power * QuadcopterController.POWER_TO_VELOCITY)

    def set_x_velocity(self, power):
        assert power >= -100 and power <= 100 and not self.is_landed
        self.x_velocity = QuadcopterController.validate_velocity(self.x_velocity +
            power * QuadcopterController.POWER_TO_VELOCITY)

    def land(self):
        self.is_landed = True
        self.x_velocity = 0
        self.y_velocity = 0

    def take_off(self):
        self.is_landed = False


class Quadcopter:
    id_counter = 0
    CHARGE_DECREASE_PER_TICK = 0.001

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.controller = QuadcopterController(self)
        self.charge_level = 1.0
        self.human_to_move = None
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

    def get_charge_level(self):
        return self.charge_level

    def decrease_charge(self):
        self.charge_level -= Quadcopter.CHARGE_DECREASE_PER_TICK

    @staticmethod
    def get_power_one_move(velocity, place):
        power = (place - velocity) / QuadcopterController.POWER_TO_VELOCITY
        if -100 <= power <= 100:
            return power
        return None

    @staticmethod
    def braking_distance(velocity):
        n = int(velocity / (100 * QuadcopterController.POWER_TO_VELOCITY))
        return 50 * QuadcopterController.POWER_TO_VELOCITY * n * (n + 1)

    @staticmethod
    def get_power(velocity, place):
        one_move = Quadcopter.get_power_one_move(velocity, place)
        if one_move is not None:
            return one_move
        if sign(velocity) * sign(place) == -1:
            return sign(place) * 100
        multiplier = 1
        if velocity < 0:
            velocity *= -1
            place *= -1
            multiplier = -1

        if velocity + Quadcopter.braking_distance(velocity) > place:
            return -100 * multiplier
        if velocity + 100 * QuadcopterController.POWER_TO_VELOCITY + \
                Quadcopter.braking_distance(velocity + 100 * QuadcopterController.POWER_TO_VELOCITY) <= place:
            return 100 * multiplier
        return 0

    def move_to_point(self, x, y):
        x_power = Quadcopter.get_power(self.get_controller().x_velocity, x - self.x)
        y_power = Quadcopter.get_power(self.get_controller().y_velocity, y - self.y)
        self.get_controller().set_x_velocity(x_power)
        self.get_controller().set_y_velocity(y_power)

class Human(api.Human):
    id_counter = 0
    SPEED = 1.5
    RADIUS = 20

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.id = Human.id_counter
        self.copter = None
        self.target = None
        self.move = None
        self.ticks_since_last_action = 0
        Human.id_counter += 1

    def get_id(self):
        return self.id

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    def is_possible_move(self, move):
        if move is None:
            return False
        new_coords = (self.x + Human.SPEED * move[0], self.y + Human.SPEED * move[1])
        is_good_coord = min(new_coords[0], new_coords[1], settings.WIDTH - new_coords[0],
                            settings.HEIGHT - new_coords[1]) > \
                        Human.RADIUS
        if is_good_coord:
            # for wall in settings.walls:
            # TODO: check intersection with walls
            pass
        return is_good_coord

    def perform_action(self):
        if self.target is None:
            if randint(0, 30) == 0 or not self.is_possible_move(self.move): # Change move direction
                possible_moves = []
                for x in range(-1, 2):
                    for y in range(-1, 2):
                        possible_moves.append((x, y))
                i = 0
                while i < len(possible_moves):
                    move = possible_moves[i]
                    if not self.is_possible_move(move):
                        possible_moves[i] = possible_moves[-1]
                        possible_moves.pop()
                    else:
                        i += 1
                assert len(possible_moves) > 0
                self.move = possible_moves[randint(0, len(possible_moves) - 1)]
            self.x, self.y = self.x + Human.SPEED * self.move[0], self.y + Human.SPEED * self.move[1]
        else:
            if distance((self.x, self.y), self.target) < Human.RADIUS and self.copter is not None:
                self.copter.human_to_move = None
                self.copter = None
            if self.copter is not None:
                if abs(self.copter.get_x() - self.x) < Human.SPEED:
                    self.x = self.copter.get_x()
                else:
                    self.x += sign(self.copter.get_x() - self.x) * Human.SPEED

                if abs(self.copter.get_y() - self.y) < Human.SPEED:
                    self.y = self.copter.get_y()
                else:
                    self.y += sign(self.copter.get_y() - self.y) * Human.SPEED

    def assign_to_copter(self, copter):
        self.copter = copter
        self.target = (randint(2 * Human.RADIUS, settings.WIDTH - 2 * Human.RADIUS),
                       randint(2 * Human.RADIUS, settings.HEIGHT - 2 * Human.RADIUS))


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
        for wall in settings.walls:
            self.walls.append(Wall(wall[0], wall[1]))
        self.charging_stations = []
        for charging_station in settings.charging_stations:
            self.charging_stations.append(ChargingStation(charging_station[0], charging_station[1]))
        self.enter_point = settings.enter_point
        self.people = []
        self.quadcopters = []
        for _ in range(settings.copter_count):
            station = self.charging_stations[randint(0, len(self.charging_stations) - 1)]
            self.quadcopters.append(Quadcopter(station.get_x(), station.get_y()))

    def get_walls(self):
        return self.walls

    def get_charging_stations(self):
        return self.charging_stations

    def get_people(self):
        return self.people

    def get_quadcopters(self):
        return self.quadcopters

    def get_human(self, id):
        for human in self.people:
            if human.get_id() == id:
                return human

    def create_human(self):
        self.people.append(Human(self.enter_point[0], self.enter_point[1]))
