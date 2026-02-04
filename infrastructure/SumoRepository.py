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

    def getNetwork(self) -> sumolib.net.Net:
        """Get the SUMO network object.

        Returns:
            SUMO network object.
        """

        # Check if network is already loaded
        if self.network:
            return self.network
        
        # Load and cache the network
        self.network = sumolib.net.readNet(self.networkFilePath)
        return self.network
    
    def getNetworkPedestrianEdges(self) -> list[str]:
        """Get the list of pedestrian edges in the network.

        Returns:
            List of pedestrian edge IDs.
        """

        # Check if network is already loaded
        if self.network:
            return [e.getID() for e in self.network.getEdges() if e.allows("pedestrian")]
        
        # Load the network
        network = self.getNetwork()

        # Return pedestrian edges
        return [e.getID() for e in network.getEdges() if e.allows("pedestrian")]
