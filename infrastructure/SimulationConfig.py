from pathlib import Path

class SimulationConfig:
    DEFAULT_ASSET_DIRECTORY_NAME = "maps"
    DEFAULT_NETWORK_FILE_NAME = "net.net.xml"
    DEFAULT_PARKING_FILE_NAME = "parking.add.xml"
    DEFAULT_DECAL_FILE_NAME = "map.xml"
    DEFAULT_ROUTE_FILE_NAME = "routes.xml"
    DEFAULT_GAS_PRICE_PER_LITER = 58.9

    def __init__(self) -> None:
        self.assetDirectoryName = self.DEFAULT_ASSET_DIRECTORY_NAME
        self.networkFileName = self.DEFAULT_NETWORK_FILE_NAME
        self.parkingFileName = self.DEFAULT_PARKING_FILE_NAME
        self.decalFileName = self.DEFAULT_ROUTE_FILE_NAME
        self.routesFileName = self.DEFAULT_ROUTE_FILE_NAME
        self.gasPricePerLiter = self.DEFAULT_GAS_PRICE_PER_LITER

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