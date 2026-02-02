import sumolib
class SumoRepository:
    network = None

    def __init__(self, network_file_path: str):
        self.networkFilePath = network_file_path

    def getNetwork(self):
        if self.network:
            return self.network
        self.network = sumolib.net.readNet(self.networkFilePath)
        return self.network
    
    def getNetworkPedestrianEdges(self):
        if self.network:
            return [e for e in self.network.getEdges() if e.allows("pedestrian")]
        network = self.getNetwork()
        return [e for e in network.getEdges() if e.allows("pedestrian")]
