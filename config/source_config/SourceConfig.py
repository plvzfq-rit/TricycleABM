from pathlib import Path

class SourceConfig:
    def __init__(self, source_directory_name:str = "maps", 
                    network_file_name:str = "net.net.xml", 
                    parking_file_name:str = "parking.add.xml",
                    decal_file_name:str = "map.xml"):
        self.sourceDirectoryName = source_directory_name
        self.networkFileName = network_file_name
        self.parkingFileName = parking_file_name
        self.decalFileName = decal_file_name

    def getSourceDirectory(self) -> str:
        script_dir = Path(__file__).resolve().parent.parent.parent
        source_dir = script_dir / self.sourceDirectoryName
        return source_dir

    def getSourceNetworkFilePath(self) -> str:
        return str(self.getSourceDirectory() / self.networkFileName)
    
    def getSourceParkingFilePath(self) -> str:
        return str(self.getSourceDirectory() / self.parkingFileName)
    
    def getSourceDecalFilePath(self) -> str:
        return str(self.getSourceDirectory() / self.decalFileName)