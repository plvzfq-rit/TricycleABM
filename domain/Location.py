import traci
import difflib
class Location:
    """Data class that details a location within the simulation.

    Attributes:
        location: string containing the ID of a Traci edge.
        position: float containing the position along the Traci edge.
    """

    def __init__(self, location: str, position: float) -> None:
        """Initializes an instance given a location and position.
        
        Args:
            location: string containing the ID of a Traci edge.
            position: float containing the position along the Traci edge.
        """

        # TODO: Should put in whether it goes in which lane.
        self.location = location
        self.position = position

    def __eq__(self, value: any) -> bool:
        if type(self) != type(value):
            return False
        return self.location == value.location and self.position == value.position
    
    def __str__(self):
        return f"Location(loc={self.location},pos={self.position})"
    
    def isNear(self, value: any, threshold: float = 200.0):
        # Check if the types of self and value match
        if type(self) != type(value):
            return False

        # Get coordinates for self
        coordinates_self = get_coordinates(self.location, self.position)
        if coordinates_self is None:
            return False  # Invalid location, can't proceed

        # Get coordinates for value
        coordinates_value = get_coordinates(value.location, value.position)
        if coordinates_value is None:
            return False  # Invalid location, can't proceed

        # Unpack the coordinates
        x1, y1 = coordinates_self
        x2, y2 = coordinates_value

        # Calculate the Euclidean distance between the two points
        distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

        # Return whether the distance is within the threshold
        return distance <= threshold
    def distanceTo(self, another_location):
        if another_location == None or another_location.isInvalid():
            return 0.0
        return traci.simulation.getDistanceRoad(self.location, self.position, another_location.location, another_location.position)
    
    def isInvalid(self) -> bool:
        return self.location == '' and self.position == -1073741824.0
    

def get_coordinates(location, position):
    """Helper function to extract coordinates, handling cluster logic and junctions."""
    try:
        # Lazy way, whole day trying to figure this out
        if "J" in location:
            junctions = list(traci.junction.getIDList())
            closest_junction = difflib.get_close_matches(location, junctions, n=1)[0]
            return traci.junction.getPosition(closest_junction) 
        return traci.simulation.convert2D(location, position)
    except traci.TraCIException:
        print("Didn't work")
        return None