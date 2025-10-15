from pathlib import Path

class FileSystemDescriptor:
    INPUT_DIRECTORY_NAME = "maps"
    PARKING_FILE_NAME = "parking.add.xml"
    OUTPUT_DIRECTORY_NAME = "assets"

    def getInputDirectory(self) -> str:
        script_dir = Path(__file__).resolve().parent.parent
        input_dir = script_dir / self.SOURCE_DIRECTORY_NAME
        return input_dir
    
    def getInputParkingFilePath(self) -> str:
        return str(self.getInputDirectory() / self.PARKING_FILE_NAME)
    
    def getOutputDirectory(self) -> str:
        script_dir = Path(__file__).resolve().parent.parent
        output_dir = script_dir / self.DESTINATION_DIRECTORY_NAME
        return output_dir