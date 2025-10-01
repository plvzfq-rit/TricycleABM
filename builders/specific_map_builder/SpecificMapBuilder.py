from config.map_config.MapConfig import MapConfig
from config.traci_config.TraciConfig import TraciConfig
from config.destination_config.DestinationConfig import DestinationConfig
from config.source_config.SourceConfig import SourceConfig

import xml.etree.ElementTree as ET

import shutil
import sumolib

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
        source_network_file = self.sourceConfig.getSourceNetworkFilePath()
        destination_network_file = self.destinationConfig.getDestinationNetworkFilePath()
        shutil.copyfile(source_network_file, destination_network_file)

        source_parking_file = self.sourceConfig.getSourceParkingFilePath()
        destination_parking_file = self.destinationConfig.getDestinationParkingFilePath()
        shutil.copyfile(source_parking_file, destination_parking_file)

        self._constructMapConfig()
        return self.mapConfig
        

