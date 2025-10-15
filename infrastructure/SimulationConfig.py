from pathlib import Path

class SimulationConfig:
    DEFAULT_ASSET_DIRECTORY_NAME = "assets"
    DEFAULT_NETWORK_FILE_NAME = "net.net.xml"
    DEFAULT_PARKING_FILE_NAME = "parking.add.xml"
    DEFAULT_DECAL_FILE_NAME = "map.xml"
    DEFAULT_ROUTE_FILE_NAME = "routes.xml"
    DEFAULT_GAS_PRICE_PER_LITER = 50.00

    def __init__(self, assetDirectoryName: str=DEFAULT_ASSET_DIRECTORY_NAME, 
                networkFileName: str=DEFAULT_NETWORK_FILE_NAME, 
                parkingFileName: str=DEFAULT_PARKING_FILE_NAME, 
                decalFileName: str = DEFAULT_DECAL_FILE_NAME, 
                routesFileName:str =DEFAULT_ROUTE_FILE_NAME, 
                gasPricePerLiter=DEFAULT_GAS_PRICE_PER_LITER) -> None:
        self.assetDirectoryName = assetDirectoryName
        self.networkFileName = networkFileName
        self.parkingFileName = parkingFileName
        self.decalFileName = decalFileName
        self.routesFileName = routesFileName
        self.gasPricePerLiter = gasPricePerLiter

    def getAssetDirectoryName(self) -> str:
        return self.directoryName
    
    def getAssetDirectory(self) -> str:
        script_dir = Path(__file__).resolve().parent.parent
        assets_dir = script_dir / self.assetDirectoryName
        return assets_dir
    
    def getNetworkFileName(self) -> str:
        return self.networkFileName
    
    def getParkingFileName(self) -> str:
        return self.parkingFileName
    
    def getDecalFileName(self) -> str:
        return self.decalFileName
    
    def getRoutesFileName(self) -> str:
        return self.routesFileName
    
    def getNetworkFilePath(self) -> str:
        return str(self.getAssetDirectory() / self.networkFileName)
    
    def getParkingFilePath(self) -> str:
        return str(self.getAssetDirectory() / self.parkingFileName)
    
    def getDecalFilePath(self) -> str:
        return str(self.getAssetDirectory() / self.decalFileName)
    
    def getRoutesFilePath(self) -> str:
        return str(self.getAssetDirectory() / self.routesFileName)
    
    def getGasPricePerLiter(self) -> float:
        return float(self.gasPricePerLiter)
    
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

    def setDecalFileName(self, decalFileName: str) -> None:
        if not decalFileName.strip():
            raise Exception("Invalid Decal file name. Was empty.")
        self.decalFileName = decalFileName.strip()

    def setRoutesFileName(self, routesFileName: str) -> None:
        if not routesFileName.strip():
            raise Exception("Invalid routes file name. Was empty.")
        self.routesFileName = routesFileName.strip()