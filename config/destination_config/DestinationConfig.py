from pathlib import Path

class DestinationConfig:
    def __init__(self, destination_directory_name:str = "assets",
                 destination_network_file_name:str = "net.net.xml",
                 destination_parking_file_name:str = "parking.add.xml"):
        self.destinationDirectoryName = destination_directory_name
        self.destinationNetworkFileName = destination_network_file_name
        self.destinationParkingFileName = destination_parking_file_name

    def getDestinationDirectory(self) -> str:
        script_dir = Path(__file__).resolve().parent.parent.parent
        destination_dir = script_dir / self.destinationDirectoryName
        return destination_dir

    def getDestinationNetworkFilePath(self) -> str:
        return str(self.getDestinationDirectory() / self.destinationNetworkFileName)
    
    def getDestinationParkingFilePath(self) -> str:
        return str(self.getDestinationDirectory() / self.destinationParkingFileName)