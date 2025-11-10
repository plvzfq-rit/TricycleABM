from domain.MapDescriptor import MapDescriptor
from infrastructure.SimulationConfig import SimulationConfig
from infrastructure.ParkingAreaParser import ParkingAreaParser
from infrastructure.FileSystemDescriptor import FileSystemDescriptor
from infrastructure.FileSynchronizer import FileSynchronizer
import os

class SpecificMapBuilder:
    def __init__(self, traci_config:SimulationConfig | None = None, 
                file_system_descriptor: FileSystemDescriptor | None = None,
                parking_area_parser: ParkingAreaParser | None = None,
                file_sync_service: FileSynchronizer | None = None) -> None:
        self.traciConfig = traci_config or SimulationConfig()
        self.fileSystemDescriptor = file_system_descriptor or FileSystemDescriptor()
        self.parkingAreaParser = parking_area_parser or ParkingAreaParser()
        self.fileSyncService = file_sync_service or FileSynchronizer()

    def build(self) -> MapDescriptor:
        destination_directory = self.fileSystemDescriptor.getOutputDirectory()
        os.makedirs(destination_directory, exist_ok=True)
        self.fileSyncService.removeFilesInDirectory(destination_directory)

        source_directory = self.fileSystemDescriptor.getInputDirectory()
        self.fileSyncService.copyFilesFromDirectory(source_directory, destination_directory)

        return self.parkingAreaParser.parse(self.traciConfig.getParkingFilePath())
        

