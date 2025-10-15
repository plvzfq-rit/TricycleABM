from domain.MapDescriptor import MapDescriptor
from config.TraciConfig import TraciConfig
from config.DestinationConfig import DestinationConfig
from config.SourceConfig import SourceConfig
from infrastructure.ParkingAreaParser import ParkingAreaParser

import xml.etree.ElementTree as ET

import shutil
import os

class SpecificMapBuilder:
    def __init__(self, map_config:MapDescriptor = MapDescriptor(), 
                 traci_config:TraciConfig = TraciConfig(), 
                 source_config:SourceConfig = SourceConfig(), 
                 destination_config:DestinationConfig = DestinationConfig()) -> None:
        self.mapConfig = map_config
        self.traciConfig = traci_config
        self.sourceConfig = source_config
        self.destinationConfig = destination_config

    def build(self) -> MapDescriptor:
        destination_directory = self.destinationConfig.getDestinationDirectory()
        for file in os.listdir(destination_directory):
            filepath = os.path.join(destination_directory, file)
            os.remove(filepath)

        source_directory = self.sourceConfig.getSourceDirectory()
        for file in os.listdir(source_directory):
            source_file_path = os.path.join(source_directory, file)
            destination_file_path = os.path.join(destination_directory, file)
            shutil.copyfile(source_file_path, destination_file_path)

        return ParkingAreaParser.parse(self.traciConfig.getParkingFilePath())
        

