import models
import simulator.settings as settings


class RoyalManager:
    def __init__(self):
        self.room = models.Room(settings)

    def run_simulation_tick(self):
        for quadcopter in self.room.get_quadcopters():
            quadcopter.decrease_charge()
            if quadcopter.get_controller().is_landed:
                quadcopter.charge_level = 1.0
        #
