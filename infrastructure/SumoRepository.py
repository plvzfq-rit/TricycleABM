import sumolib
class SumoRepository:
    """Repository for accessing SUMO network data.

    Attributes:
        networkFilePath: path to the SUMO network file.
        network: cached SUMO network object.
    """
    network = None

    def __init__(self, network_file_path: str) -> None:
        """Initializes the repository with the network file path.

        Args:
            network_file_path: path to the SUMO network file.
        """
        self.networkFilePath = network_file_path
        self.network = sumolib.net.readNet(self.networkFilePath)

    def getNetwork(self) -> sumolib.net.Net:
        """Get the SUMO network object.

        Returns:
            SUMO network object.
        """
        return self.network
    
    def getNetworkPedestrianEdges(self) -> list[str]:
        """Get the list of pedestrian edges in the network.

        Returns:
            List of pedestrian edge IDs.
        """

        # Return pedestrian edges
        return [e.getID() for e in self.network.getEdges() if e.allows("pedestrian")]

    def getNumberOfLanes(self, edge:str)->int:
        """Get the number of lanes for a given edge.

        Args:
            edge: ID of the edge.
        Returns:
            Number of lanes for the edge.
        """
        return self.network.getEdge(edge).getLaneNumber()
    
    def getLaneLength(self, lane:str)->float:
        """Get the length of a given lane.

        Args:
            lane: ID of the lane.
        Returns:
            Length of the lane.
        """
        return self.network.getLane(lane).getLength()
