"""Module for representing and manipulating locations within the SUMO application.

This module provides the Location class which represents a specific position
within the SUMO application, which is identified by an edge ID, position along
the edge, and lane index. It also includes utility functions for calculating 
distances and converting between coordinate systems.
"""

import traci
import difflib


class Location:
    """A location identified by a position in a lane of a SUMO edge.
    
    :ivar INVALID_POSITION_VALUE: Constant representing an invalid position value.
    :ivar edge: The ID of a SUMO edge.
    :ivar position: The position along the SUMO edge in meters.
    :ivar lane: The ID of the lane in the particular edge.
    """
    INVALID_POSITION_VALUE = -1073741824.0

    def __init__(self, edge: str, position: float, lane: int) -> None:
        """Initialize a location with edge, position, and lane.
        
        :param edge: The ID of a SUMO edge.
        :type edge: str
        :param position: The position along the SUMO edge in meters.
        :type position: float
        :param lane: The ID of the lane in the particular edge.
        :type lane: int
        """
        self.edge = edge
        self.position = position
        self.lane = lane

    def __eq__(self, value: any) -> bool:
        """Check equality between this location and another object.
        
        :param value: Any object to compare for equality.
        :type value: any
        :return: True if both objects are Location instances with identical attributes, False otherwise.
        :rtype: bool
        """
        # check for same type
        if type(self) != type(value):
            return False
        
        # check for same values
        return self.edge == value.edge and \
            self.position == value.position and \
            self.lane == self.lane
    
    def getEdge(self) -> str:
        """Retrieve the edge ID of this location.
        
        :return: The edge ID, as a string.
        :rtype: str
        """
        return self.edge
    
    def getPosition(self) -> float:
        """Retrieve the position of the location along the edge.
        
        :return: The position in meters as a float.
        :rtype: float
        """
        return self.position
    
    def getLane(self) -> int:
        """Get the lane number of the current location respective of edge.
        
        :return: The lane ID as an integer.
        :rtype: int
        """
        return self.lane

    def isNear(self, another_location: 'Location',
               threshold: float = 1.0) -> bool:
        """Check if this location is near another location within a threshold.
        
        :param another_location: Another Location object within the simulation.
        :type another_location: Location
        :param threshold: Distance tolerance in meters. Defaults to 1.0 meter.
        :type threshold: float
        :return: True if the Euclidean distance is within the threshold, False otherwise.
        :rtype: bool
        """
        # Check if the types match
        if type(self) != type(another_location):
            return False

        # Get Euclidean distance
        distance = getEuclideanDistance(self, another_location)

        # Return whether the distance is within the threshold
        return distance <= threshold
    
    def isInvalid(self) -> bool:
        """Shows if the Location object holds an invalid value.
        
        :return: True if the location is invalid, False otherwise.
        :rtype: bool
        """
        return self.edge == '' and self.position == self.INVALID_POSITION_VALUE

# Helper functions
def get2DCoordinates(location: Location) -> tuple:
    """Converts a location to 2D Cartesian coordinates.
    
    :param location: A Location instance within the simulation.
    :type location: Location
    :return: A tuple (x, y) with Cartesian coordinates, or None if conversion fails.
    :rtype: tuple or None
    """
    def getJunctionIds() -> tuple[str]:
        """Gets all junction IDs within the simulation.
        
        :return: A tuple of junction ID strings.
        :rtype: tuple
        """
        return traci.junction.getIDList()
    
    def getJunctionCoordinates(junction_id: str) -> tuple:
        """Get the coordinates of a junction center given its ID.
        
        :param junction_id: The ID of a junction. Junction edges start with a 'J'
        :type junction_id: str
        :return: A tuple (x, y) containing the Cartesian coordinates.
        :rtype: tuple
        """
        return traci.junction.getPosition(junction_id) 
    
    def getEdgeCoordinates(location: Location) -> tuple:
        """Get the coordinates of an edge location. In SUMO, map edges start with an 'E'.
        
        :param location: A Location instance on a presumed edge.
        :type location: Location
        :return: A tuple (x, y) containing the Cartesian coordinates.
        :rtype: tuple
        """
        edge = location.getEdge()
        position = location.getPosition()
        return traci.simulation.convert2D(edge, position)

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
    """Calculate the Manhattan distance between two Location objects.
    
    :param location: A location within the simulation.
    :type location: Location
    :param another_Location: Another location within the simulation.
    :type another_Location: Location
    :return: The Manhattan distance in meters. Returns 0 if either location is invalid.
    :rtype: float
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
    """Calculate the Euclidean distance between two Location objects.
    
    :param location: A location within the simulation.
    :type location: Location
    :param another_location: Another location within the simulation.
    :type another_location: Location
    :return: The Euclidean distance in meters. Returns 0 if either location is invalid.
    :rtype: float
    """
    # Get coordinates for first location
    coordinates_self = get2DCoordinates(location)
    if coordinates_self is None:
        return -1  # Invalid location, can't proceed

    # Get coordinates for second location
    coordinates_value = get2DCoordinates(another_location)
    if coordinates_value is None:
        return -1  # Invalid location, can't proceed

    # Unpack the coordinates
    x1, y1 = coordinates_self
    x2, y2 = coordinates_value

    # Calculate the Euclidean distance between the two points
    distance = ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5

    return distance