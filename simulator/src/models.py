import api.quadcopter as api
from random import randint
from random import random
import simulator.settings as settings
import math
from six.moves import urllib
import threading


def distance(p1, p2):
    d = (p2[0] - p1[0], p2[1] - p1[1])
    return math.sqrt(d[0] * d[0] + d[1] * d[1])


def pseudo_scalar_production(p1, p2):
    return p1[1] * p2[0] - p1[0] * p2[1]


def scalar_production(p1, p2):
    return p1[0] * p2[0] + p1[1] * p2[1]


def sign(x):
    if x > 0:
        return 1
    if x < 0:
        return -1
    return 0


def is_good_human_coord(new_coords):
    is_good_coord = min(new_coords[0], new_coords[1], settings.WIDTH - new_coords[0],
                        settings.HEIGHT - new_coords[1]) > Human.RADIUS
    if is_good_coord:
        for wall in settings.walls:
            v1 = (wall[0][0] - new_coords[0], wall[0][1] - new_coords[1])
            v2 = (wall[1][0] - new_coords[0], wall[1][1] - new_coords[1])
            ln = distance(*wall)
            h = abs(pseudo_scalar_production(v1, v2)) / ln
            if h < Human.RADIUS:
                base = (wall[1][0] - wall[0][0], wall[1][1] - wall[0][1])
                base = (base[0] / ln, base[1] / ln)
                a = scalar_production(v1, base)
                b = scalar_production(v2, base)
                if sign(a) * sign(b) <= 0 or min(distance(new_coords, wall[0]),
                                                 distance(new_coords, wall[1])) < Human.RADIUS:
                    is_good_coord = False
                    break
    return is_good_coord

ALPHA = 0.03
SIN = math.sin(ALPHA)
COS = math.cos(ALPHA)

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

    def turn(self):
        self.x_velocity, self.y_velocity = self.x_velocity * COS - self.y_velocity * SIN, self.x_velocity * SIN + self.y_velocity * COS

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

    def intersects_wall_in_a_tick(self):
        return not is_good_human_coord((self.x + self.controller.x_velocity, self.y + self.controller.y_velocity))

    def move_to_point(self, x, y):
        x_power = Quadcopter.get_power(self.get_controller().x_velocity, x - self.x)
        y_power = Quadcopter.get_power(self.get_controller().y_velocity, y - self.y)
        self.get_controller().set_x_velocity(x_power)
        self.get_controller().set_y_velocity(y_power)
        if self.human_to_move is not None and self.human_to_move.copter is not None and self.intersects_wall_in_a_tick():
            ln = distance((0, 0), (self.controller.x_velocity, self.controller.y_velocity))
            self.controller.x_velocity /= ln / QuadcopterController.MAX_SPEED
            self.controller.y_velocity /= ln / QuadcopterController.MAX_SPEED
            angle = 0
            while self.intersects_wall_in_a_tick():
                self.get_controller().turn()
                angle += ALPHA
                if angle >= 2 * math.pi:
                    break


class Human(api.Human):
    id_counter = 0
    SPEED = 1.5
    RADIUS = 20

    def __init__(self, room, x, y):
        self.room = room
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
        return is_good_human_coord(new_coords)

    def perform_action(self):
        if self.target is None:
            if randint(0, 30) == 0 or not self.is_possible_move(self.move):  # Change move direction
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
            if distance((self.x, self.y), self.target) < Human.RADIUS + 3:
                if self.copter is not None:
                    self.copter.human_to_move = None
                    self.copter = None
                self.ticks_since_last_action += 1
                if self.ticks_since_last_action > 15:
                    self.room.remove_human(self.id)
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
        wall = settings.walls[randint(2, len(settings.walls) - 1)]
        p = random()
        assert 0 <= p <= 1
        n = (wall[1][0] - wall[0][0], wall[1][1] - wall[0][1])
        n = (-sign(n[1]), sign(n[0]))
        if randint(0, 1) == 0:
            n = (-n[0], -n[1])
        self.target = (wall[0][0] * p + wall[1][0] * (1 - p) + n[0] * Human.RADIUS,
                       wall[0][1] * p + wall[1][1] * (1 - p) + n[1] * Human.RADIUS)


class KinectMan(Human):
    def __init__(self, room, x, y):
        Human.__init__(self, room, x, y)
        self.t = threading.Thread(target=self.coords_updater)
        self.t.daemon = False
        self.t.start()
        self._x = 0
        self._y = 0

        # self.min_x = 133423
        # self.max_x = -13345623
        # self.min_y = 342134234
        # self.max_y = -342134234


    def coords_updater(self):
        while True:
            f = urllib.request.urlopen('http://85.188.11.77:12358/last_point')
            s = f.read()
            self._x, _, self._y = map(lambda str : float(str), s.split(','))
            # self.min_x = min(self._x, self.min_x)
            # self.max_x = max(self._x, self.max_x)
            # self.min_y = min(self._y, self.min_y)
            # self.max_y = max(self._y, self.max_y)
            # print self.min_x, self.min_y, self.max_x, self.max_y

    def update_coords(self):
        self.x = (1.16 + self._x) * 230
        self.y = (self._y - 1.25) * 285
        pass

    def perform_action(self):
        pass


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
        self.kinect_man = KinectMan(self, self.enter_point[0], self.enter_point[1])
        self.people.append(self.kinect_man)

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

    def remove_human(self, id):
        for i, human in enumerate(self.people):
            if human.get_id() == id:
                self.people[i] = self.people[-1]
                self.people.pop()
                break

    def create_human(self):
        self.people.append(Human(self, self.enter_point[0], self.enter_point[1]))
