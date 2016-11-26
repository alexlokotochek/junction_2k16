import models
import simulator.settings as settings


class RoyalManager:
    def __init__(self):
        self.current_tick = -1
        self.room = models.Room(settings)

    def run_simulation_tick(self):
        self.current_tick += 1
        for quadcopter in self.room.get_quadcopters():
            quadcopter.decrease_charge()
            if quadcopter.get_controller().is_landed:
                quadcopter.charge_level = 1.0
            quadcopter.x += quadcopter.get_controller().x_velocity
            quadcopter.y += quadcopter.get_controller().y_velocity
        if self.current_tick % 500 == 0:
            self.room.create_human()
        for human in self.room.get_people():
            human.perform_action()