import traci
import difflib
class Location:
    """A location identified by a position in a lane of a Sumo edge.

    Attributes:
        INVALID_POSITION_VALUE: constant representing an invalid value for 
            position.
        edge: the ID of a Sumo edge.
        position: the position along the Sumo edge.
        lane: ID of the lane in a particular edge
    """
    INVALID_POSITION_VALUE = -1073741824.0

    def __init__(self, edge: str, position: float, lane: int) -> None:
        """Initializes an instance given a edge, position, and lane.
        
        Args:
            edge: the ID of a Sumo edge.
            position: the position along the Sumo edge.
            lane: ID of the lane in a particular edge
        """
        self.edge = edge
        self.position = position
        self.lane = lane

    def __eq__(self, value: any) -> bool:
        """Detects equality between this instance and another object.
        
        Args:
            value: any object
            
        Returns:
            True, if the objects are equal. False, otherwise.
        """

        # check for same type
        if type(self) != type(value):
            return False
        
        # check for same values
        return self.edge == value.edge and \
            self.position == value.position and \
            self.lane == self.lane
    
    def getEdge(self) -> str:
        """Get the edge of the location.
        
        Returns:
            Edge ID of location.
        """
        return self.edge
    
    def getPosition(self) -> float:
        """Get the position of the location.
        
        Returns:
            Position of location.
        """
        return self.position
    
    def getLane(self) -> int:
        """Get the lane of the location.
        
        Returns:
            Lane of location.
        """
        return self.lane

    def isNear(self, another_location: 'Location',
               threshold: float = 1.0) -> bool:
        """Shows if a location object is 'near' to another location object.
        
        Args:
            another_location: another location within the simulation.
            threshold: amount of tolerance before saying that two locations are
                near enough.

        Returns:
            True, if the Euclidean distance is not more than the threshold.
            False, otherwise.
        """
        # Check if the types of self and value match
        if type(self) != type(another_location):
            return False

        # Get Euclidean distance
        distance = getEuclideanDistance(self, another_location)

        # Return whether the distance is within the threshold
        return distance <= threshold
    
    def isInvalid(self) -> bool:
        """Shows if the Location object holds an invalid value.
        
        Returns:
            True, if the object is invalid. False, otherwise."""
        return self.edge == '' and self.position == self.INVALID_POSITION_VALUE

# Helper functions
def get2DCoordinates(location: Location) -> tuple:
    """Gets the 2D coordinates of a location.
    
    Args:
        location: a location within the simulation.
        
    Returns:
        A tuple with coordinates as related to the Cartesian plane.
    """

    def getJunctionIds() -> tuple[str]:
        """Gets the junction ID's within the simulation.
        
        Returns:
            A list of junction IDs as strings.
        """
        return traci.junction.getIDList()
    
    def getJunctionCoordinates(junction_id: str) -> tuple:
        """Gets the coordinates of the center of a junction, given its ID.

        Args:
            junction_id: ID of a junction.
        
        Returns:
            A tuple containing the Cartesian coordinates of a junction's center.
        """
        return traci.junction.getPosition(junction_id) 
    
    def getEdgeCoordinates(location: Location) -> tuple:
        """Gets the location of a coordinate.
        
        Args:
            location: A location of a (presumed) edge.
            
        Returns:
            The coordinates of an edge location.
        """
        edge = location.getEdge()
        position = location.getPosition()
        lane = location.getLane()
        return traci.simulation.convert2D(edge, position, lane)

    try:
        # if, the location is a junction...
        if "J" in location.getEdge():
            junctions = list(getJunctionIds())
            closest_junction = difflib.get_close_matches(location.getEdge(), junctions, n=1)[0]
            return getJunctionCoordinates(closest_junction)
        
        # else, return the coordinates of an edge.
        return getEdgeCoordinates(location)
    
    # everything fails
    except traci.TraCIException:
        print("Didn't work")
        return None

def getManhattanDistance(location: Location, 
                         another_Location: Location) -> float:
    """Gets the Manhattan distance between two locations within the 
    simulation.
    
    Args:
        location: a location within the simulation.
        another_location: another location within the simulation.
        
    Returns:
        the Manhattan distance between the two locations. If the location
        is invalid, 0 is returned.
    """

    # Unpacks values
    location_edge = location.getEdge()
    location_position = location.getPosition()
    another_location_edge = another_Location.getEdge()
    another_Location_position = another_Location.getPosition()
    is_manhattan_distance = True

    # Computes Manhattan distance
    return traci.simulation.getDistanceRoad(location_edge, 
                                            location_position, 
                                            another_location_edge, 
                                            another_Location_position, 
                                            is_manhattan_distance)

def getEuclideanDistance(location: Location, 
                         another_location: Location) -> float:
    """Gets the Euclidean distance between two locations within the 
    simulation.
    
    Args:
        location: a location within the simulation.
        another_location: another location within the simulation.
        
    Returns:
        the Euclidean distance between the two locations. If the location
        is invalid, 0 is returned.
    """
    # Get coordinates for location
    coordinates_self = get2DCoordinates(location)
    if coordinates_self is None:
        return -1  # Invalid location, can't proceed

    # Get coordinates for value
    coordinates_value = get2DCoordinates(another_location)
    if coordinates_value is None:
        return -1  # Invalid location, can't proceed

    # Unpack the coordinates
    x1, y1 = coordinates_self
    x2, y2 = coordinates_value

    # Calculate the Euclidean distance between the two points
    distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    return distance