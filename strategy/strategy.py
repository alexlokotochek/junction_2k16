import collections
from simulator.src.models import *


class Strategy:
    def __init__(self, room):
        self.room = room
        self.human_id_to_copter = {}
        self.human_id_queue = collections.deque()
        self.last_human_id = -1
        self.free_copters = []
        for quadcopter in self.room.get_quadcopters():
            self.free_copters.append(quadcopter)

    def run_tick(self):
        if len(self.room.get_people()) > 0 and self.room.get_people()[-1].get_id() > self.last_human_id:
            # TODO: more than 1 man in a tick
            self.human_id_queue.append(self.room.get_people()[-1].get_id())
            self.last_human_id = self.room.get_people()[-1].get_id()
        while len(self.free_copters) > 0 and len(self.human_id_queue) > 0:
            self.human_id_to_copter[self.human_id_queue[0]] = self.free_copters[-1]
            self.free_copters[-1].human_to_move = self.room.get_human(self.human_id_queue[0])
            self.free_copters[-1].ticks_next_to_human = 0
            self.free_copters[-1].get_controller().take_off()
            self.free_copters.pop()
            self.human_id_queue.popleft()
        for quadcopter in self.room.get_quadcopters():
            if quadcopter.human_to_move is None:
                if distance((quadcopter.get_x(), quadcopter.get_y()), settings.charging_stations[0]) < 15:
                    quadcopter.get_controller().land()
                    self.free_copters.append(quadcopter)
                else:
                    quadcopter.move_to_point(*settings.charging_stations[0])
            else:
                dx = quadcopter.human_to_move.get_x() - quadcopter.get_x()
                dy = quadcopter.human_to_move.get_y() - quadcopter.get_y()
                ln = distance((0,0), (dx,dy))
                if quadcopter.human_to_move.target is None:
                    if ln < Human.RADIUS + 15:
                        quadcopter.ticks_next_to_human += 1
                    if quadcopter.ticks_next_to_human > 10:
                        quadcopter.human_to_move.assign_to_copter(quadcopter)
                    ddx = - dx / ln
                    ddy = - dy / ln
                    ddx *= Human.RADIUS + 10
                    ddy *= Human.RADIUS + 10
                    dx += ddx
                    dy += ddy
                    quadcopter.move_to_point(quadcopter.get_x() + dx, quadcopter.get_y() + dy)
                else:
                    if ln > Human.RADIUS + 20:
                        quadcopter.get_controller().x_velocity = 0
                        quadcopter.get_controller().y_velocity = 0
                    quadcopter.move_to_point(*quadcopter.human_to_move.target)
