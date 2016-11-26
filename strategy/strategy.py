class Strategy:
    def __init__(self, room):
        self.room = room

    def run_tick(self):
        for quadcopter in self.room.get_quadcopters():
            quadcopter.get_controller().take_off()
            quadcopter.get_controller().set_x_velocity(100)
            quadcopter.get_controller().set_y_velocity(100)