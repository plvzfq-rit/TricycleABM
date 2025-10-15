from pathlib import Path

class SourceConfig:
    def __init__(self, source_directory_name:str = "maps", 
                    parking_file_name:str = "parking.add.xml"):
        self.sourceDirectoryName = source_directory_name
        self.parkingFileName = parking_file_name

    def getSourceDirectory(self) -> str:
        script_dir = Path(__file__).resolve().parent.parent.parent
        source_dir = script_dir / self.sourceDirectoryName
        return source_dir
    
    def getSourceParkingFilePath(self) -> str:
        return str(self.getSourceDirectory() / self.parkingFileName)