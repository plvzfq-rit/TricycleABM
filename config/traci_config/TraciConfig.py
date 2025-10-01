from pathlib import Path

class TraciConfig:
    assetDirectoryName = "assets"
    networkFileName = "net.net.xml"
    parkingFileName = "parking.add.xml"

    def __init__(self, assetDirectoryName: str="assets", networkFileName: str="net.net.xml", parkingFileName: str="parking.add.xml") -> None:
        self.assetDirectoryName = assetDirectoryName
        self.networkFileName = networkFileName
        self.parkingFileName = parkingFileName

    def getAssetDirectoryName(self) -> str:
        return self.directoryName
    
    def getAssetDirectory(self) -> str:
        script_dir = Path(__file__).resolve().parent.parent.parent
        assets_dir = script_dir / self.assetDirectoryName
        return assets_dir
    
    def getNetworkFileName(self) -> str:
        return self.networkFileName
    
    def getParkingFileName(self) -> str:
        return self.parkingFileName
    
    def getNetworkFilePath(self) -> str:
        return str(self.getAssetDirectory() / self.networkFileName)
    
    def getParkingFilePath(self) -> str:
        return str(self.getAssetDirectory() / self.parkingFileName)
    
    def setAssetDirectoryName(self, assetDirectoryName: str) -> None:
        if not assetDirectoryName.strip():
            raise Exception("Invalid asset directory name. Was empty.")
        self.directoryName = assetDirectoryName.strip()

    def setNetworkFileName(self, networkFileName: str) -> None:
        if not networkFileName.strip():
            raise Exception("Invalid network file name. Was empty.")
        self.networkFileName = networkFileName.strip()

    def setParkingFileName(self, parkingFileName: str) -> None:
        if not parkingFileName.strip():
            raise Exception("Invalid parking file name. Was empty.")
        self.parkingFileName = parkingFileName.strip()