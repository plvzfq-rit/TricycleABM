from pathlib import Path

class DestinationConfig:
    def __init__(self, destination_directory_name:str = "assets"):
        self.destinationDirectoryName = destination_directory_name

    def getDestinationDirectory(self) -> str:
        script_dir = Path(__file__).resolve().parent.parent.parent
        destination_dir = script_dir / self.destinationDirectoryName
        return destination_dir