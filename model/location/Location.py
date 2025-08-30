class Location:
    def __init__(self, location: str, position: float) -> None:
        self.location = location
        self.position = position

    def __init__(self, location_tuple: tuple[str, float]) -> None:
        self.location = location_tuple[0]
        self.position = location_tuple[1]

    def __eq__(self, value: any):
        if type(self) != type(value):
            return False
        return self.location == value.location and self.position == value.position
    
    def isNear(self, value: any, threshold: float = 5.0):
        if type(self) != type(value):
            return False
        return self.location == value.location and abs(self.position - value.position) <= threshold