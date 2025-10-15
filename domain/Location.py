import traci
class Location:
    def __init__(self, location: str, position: float) -> None:
        self.location = location
        self.position = position

    def __eq__(self, value: any):
        if type(self) != type(value):
            return False
        return self.location == value.location and self.position == value.position
    
    def isNear(self, value: any, threshold: float = 70.0):
        if type(self) != type(value):
            return False
        return self.location == value.location and abs(self.position - value.position) <= threshold
    
    def distanceTo(self, another_location):
        if another_location == None:
            return 0.0
        return traci.simulation.getDistanceRoad(self.location, self.position, another_location.location, another_location.position)