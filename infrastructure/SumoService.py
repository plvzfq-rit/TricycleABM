import sumolib
class SumoService:
    def getNetwork(self, network_file_path: str):
        return sumolib.net.readNet(network_file_path)