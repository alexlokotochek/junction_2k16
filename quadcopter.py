class QuadcopterController:
    def set_y_velocity(power):
        assert power >= -100 and power <= 100

    def set_x_velocity(power):
        assert power >= -100 and power <= 100

    def set_z_velocity(power):
        assert power >= -100 and power <= 100

    def land():
        pass

    def set_up():
        pass

class Quadcopter:
    def get_controller():
        pass

    def get_id():
        pass

    def get_x():
        pass

    def get_y():
        pass

    # [0..2pi), counterclockwise
    def get_rotation():
        pass

    

class Human:
    def get_id():
        pass

    def get_x():
        pass

    def get_y():
        pass

    def get_height():
        pass

class Wall:
    # [x, y]
    def get_point1():
        pass

    def get_point2():
        pass

class ChargingStation():
    def get_x():
        pass

    def get_y():
        pass

class Room:
    def get_charging_stations():
        pass

    def get_people():
        pass

    def get_quadcopters():
        pass

    