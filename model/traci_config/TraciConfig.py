from pathlib import Path

class TraciConfig:
    directoryName = "maps"
    networkFileName = "net.net.xml"
    parkingFileName = "parking.add.xml"

    def __init__(self, directoryName: str, networkFileName: str, parkingFileName: str) -> None:
        self.directoryName = directoryName
        self.networkFileName = networkFileName
        self.parkingFileName = parkingFileName

    def getDirectoryName(self) -> str:
        return self.directoryName
    
    def getNetworkFileName(self) -> str:
        return self.networkFileName
    
    def getParkingFileName(self) -> str:
        return self.parkingFileName
    
    def getNetworkFilePath(self) -> str:
        script_dir = Path(__file__).resolve().parent
        assets_dir = script_dir.parent / self.directoryName
        net_file = assets_dir / self.networkFileName
        return str(net_file)
    
    def getParkingFilePath(self) -> str:
        script_dir = Path(__file__).resolve().parent
        assets_dir = script_dir.parent / self.directoryName
        parking_file = assets_dir / self.parkingFileName
        return str(parking_file)
    
    def setDirectoryName(self, directoryName: str) -> None:
        if not directoryName.strip():
            raise Exception("Invalid directory name. Was empty.")
        self.directoryName = directoryName.strip()

    def setNetworkFileName(self, networkFileName: str) -> None:
        if not networkFileName.strip():
            raise Exception("Invalid network file name. Was empty.")
        self.networkFileName = networkFileName.strip()

    def setParkingFileName(self, parkingFileName: str) -> None:
        if not parkingFileName.strip():
            raise Exception("Invalid parking file name. Was empty.")
        self.parkingFileName = parkingFileName.strip()