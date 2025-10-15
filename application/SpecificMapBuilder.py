from domain.MapDescriptor import MapDescriptor
from infrastructure.SimulationConfig import SimulationConfig
from infrastructure.ParkingAreaParser import ParkingAreaParser
from infrastructure.FileSystemDescriptor import FileSystemDescriptor
from infrastructure.FileSyncService import FileSyncService

class SpecificMapBuilder:
    def __init__(self, traci_config:SimulationConfig | None, 
                file_system_descriptor: FileSystemDescriptor | None,
                parking_area_parser: ParkingAreaParser | None,
                file_sync_service: FileSyncService | None) -> None:
        self.traciConfig = traci_config or SimulationConfig()
        self.fileSystemDescriptor = file_system_descriptor or FileSystemDescriptor()
        self.parkingAreaParser = parking_area_parser or ParkingAreaParser()
        self.fileSyncService = file_sync_service or FileSyncService()

    def build(self) -> MapDescriptor:
        destination_directory = self.fileSystemDescriptor.getDestinationDirectory()
        self.fileSyncService.removeFilesInDirectory(destination_directory)

        source_directory = self.fileSystemDescriptor.getSourceDirectory()
        self.fileSyncService.copyFilesFromDirectory(source_directory, destination_directory)

        return self.parkingAreaParser.parse(self.traciConfig.getParkingFilePath())
        

