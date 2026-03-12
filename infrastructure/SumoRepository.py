"""Module for accessing and managing a SUMO application interface.

This module provides the SumoRepository class which wraps the SUMO network
object with methods for querying network properties such as edges, lanes,
and pedestrian paths.
"""

import sumolib


class SumoRepository:
    """Repository for accessing SUMO network data.

    :ivar networkFilePath: Path to the SUMO network XML file.
    :ivar network: Cached SUMO network object.
    """
    network = None

    def __init__(self, network_file_path: str) -> None:
        """Initialize the repository with a SUMO network file.
        
        Loads and caches the network object from the specified file path.

        :param network_file_path: Path to the SUMO network XML file.
        :type network_file_path: str
        """
        self.networkFilePath = network_file_path
        self.network = sumolib.net.readNet(self.networkFilePath)

    def getNetwork(self) -> sumolib.net.Net:
        """Get the SUMO network object.

        :return: SUMO network object to access open SUMO external program.
        :rtype: sumolib.net.Net
        """
        return self.network
    
    def getNetworkPedestrianEdges(self) -> list[str]:
        """Get all pedestrian-accessible edges in the network.

        :return: List of pedestrian edge IDs.
        :rtype: list[str]
        """
        # Return pedestrian edges
        return [e.getID() for e in self.network.getEdges() if e.allows("pedestrian")]

    def getNumberOfLanes(self, edge: str) -> int:
        """Get the number of lanes for a given edge.

        :param edge: ID of the edge.
        :type edge: str
        :return: Number of lanes in the edge.
        :rtype: int
        """
        return self.network.getEdge(edge).getLaneNumber()
    
    def getLaneLength(self, lane: str) -> float:
        """Get the length of a given lane.

        :param lane: ID of the lane.
        :type lane: str
        :return: Length of the lane (in meters).
        :rtype: float
        """
        return self.network.getLane(lane).getLength()
