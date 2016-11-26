import collections
import math
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
        # TODO: more than 1 man in a tick
        if len(self.room.get_people()) > 0 and self.room.get_people()[-1].get_id() > self.last_human_id:
            self.human_id_queue.append(self.room.get_people()[-1].get_id())
            self.last_human_id = self.room.get_people()[-1].get_id()
        while len(self.free_copters) > 0 and len(self.human_id_queue) > 0:
            self.human_id_to_copter[self.human_id_queue[0]] = self.free_copters[-1]
            self.free_copters[-1].human_to_move = self.room.get_human(self.human_id_queue[0])
            self.free_copters[-1].get_controller().take_off()
            self.free_copters.pop()
            self.human_id_queue.popleft()
        for quadcopter in self.room.get_quadcopters():
            if quadcopter.human_to_move is not None:
                dx = quadcopter.human_to_move.get_x() - quadcopter.get_x()
                dy = quadcopter.human_to_move.get_y() - quadcopter.get_y()
                ln = math.sqrt(dx*dx + dy*dy)
                ddx = - dx / ln
                ddy = - dy / ln
                ddx *= Human.RADIUS + 10
                ddy *= Human.RADIUS + 10
                dx += ddx
                dy += ddy
                quadcopter.move_to_point(quadcopter.get_x() + dx, quadcopter.get_y() + dy)
