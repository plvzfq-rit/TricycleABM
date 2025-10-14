from config.map_config.MapConfig import MapConfig
from config.traci_config.TraciConfig import TraciConfig
from config.destination_config.DestinationConfig import DestinationConfig
from config.source_config.SourceConfig import SourceConfig

import xml.etree.ElementTree as ET

import shutil
import os

class SpecificMapBuilder:
    def __init__(self, map_config:MapConfig = MapConfig(), 
                 traci_config:TraciConfig = TraciConfig(), 
                 source_config:SourceConfig = SourceConfig(), 
                 destination_config:DestinationConfig = DestinationConfig()) -> None:
        self.mapConfig = map_config
        self.traciConfig = traci_config
        self.sourceConfig = source_config
        self.destinationConfig = destination_config

    def _constructMapConfig(self):
        tree = ET.parse(self.sourceConfig.getSourceParkingFilePath())
        root = tree.getroot()

        for pa in root.findall("parkingArea"):
            if pa.get("id").startswith("hub"):
                self.mapConfig.addHub(pa.get("id"), int(pa.get("roadsideCapacity")))

    def build(self) -> MapConfig:
        destination_directory = self.destinationConfig.getDestinationDirectory()
        for file in os.listdir(destination_directory):
            filepath = os.path.join(destination_directory, file)
            os.remove(filepath)

        source_directory = self.sourceConfig.getSourceDirectory()
        for file in os.listdir(source_directory):
            source_file_path = os.path.join(source_directory, file)
            destination_file_path = os.path.join(destination_directory, file)
            shutil.copyfile(source_file_path, destination_file_path)

        self._constructMapConfig()
        return self.mapConfig
        

