from pathlib import Path

class SimulationConfig:
    assetDirectoryName = "maps"
    networkFileName = "net.net.xml"
    parkingFileName = "parking.add.xml"
    decalFileName = "map.xml"
    routesFileName = "routes.xml"
    gasPricePerLiter = 58.9
    
    def getAssetDirectory(self) -> str:
        script_dir = Path(__file__).resolve().parent.parent
        assets_dir = script_dir / self.assetDirectoryName
        return assets_dir
    
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
    
    def getWTPDistribution(self) -> callable:
        from scipy.stats import lognorm
        shape = 0.7134231299166108
        scale = 38.38513260285555
        return lambda size=1: lognorm.rvs(shape, loc=0, scale=scale, size=size)
    
    def getTodaPositions(self) -> dict[str, float]:
        return {
            "hub0": 6.12,
            "hub1": 16.48,
            "hub2": 7.72,
            "hub3": 20.44,
            "hub4": 508.38,
            "hub5": 73.76,
            "hub6": 40.82,
            "hub7": 75.65,
            "hub8": 57.71
        }