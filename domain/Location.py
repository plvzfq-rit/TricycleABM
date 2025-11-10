import traci
class Location:
    def __init__(self, location: str, position: float) -> None:
        self.location = location
        self.position = position

    def __eq__(self, value: any):
        if type(self) != type(value):
            return False
        return self.location == value.location and self.position == value.position
    
    def __str__(self):
        return f"Location(loc={self.location},pos={self.position})"
    
    def isNear(self, value: any, threshold: float = 200.0):
        if type(self) != type(value):
            return False
        # return self.location == value.location and abs(self.position - value.position) <= threshold
        try:
            x1, y1 = traci.simulation.convert2D(self.location, self.position)
            x2, y2 = traci.simulation.convert2D(value.location, value.position)
            distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
            return distance <= threshold
        except traci.TraCIException:
            print("Error converting positions for", self, "and", value)
            return False
    
    def distanceTo(self, another_location):
        if another_location == None or another_location.isInvalid():
            return 0.0
        return traci.simulation.getDistanceRoad(self.location, self.position, another_location.location, another_location.position)
    
    def isInvalid(self) -> bool:
        return self.location == '' and self.position == -1073741824.0