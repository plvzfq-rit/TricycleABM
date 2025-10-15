import random
from pathlib import Path
from typing import Self
from config.TraciConfig import TraciConfig
from domain.MapDescriptor import MapDescriptor
from infrastructure.SumoService import SumoService
from infrastructure.MapGenerator import MapGenerator
from infrastructure.ParkingFileGenerator import ParkingFileGenerator

class RandomMapBuilder:
    def __init__(self, traci_config: TraciConfig):
        self._type = "spider"
        self.junctions = 3
        self.divisions = 3
        self.parkings = 5
        self.blockLength = 50.00
        self.divisionLength = 30.00
        self.traciConfig = traci_config

    def ofType(self, _type: str) -> Self:
        if _type not in ["grid", "spider", "rand"]:
            raise Exception("Invalid type. Was: " + _type)
        self._type = _type
        return self

    def withNumberOfJunctions(self, junctions: int | float) -> Self:
        if isinstance(junctions, float):
            junctions = round(junctions)
        if not isinstance(junctions, int) or junctions <= 1:
            raise Exception("Invalid number of junctions. Was: " + str(junctions))
        self.junctions = junctions
        return self

    def withNumberOfDivisions(self, divisions: int | float) -> Self:
        if isinstance(divisions, float):
            divisions = round(divisions)
        if not isinstance(divisions, int) or divisions <= 1:
            raise Exception("Invalid number of divisions. Was: " + str(divisions))
        self.divisions = divisions
        return self

    def withBlockLength(self, block_length: int | float) -> Self:
        if isinstance(block_length, int):
            block_length = float(block_length)
        if not isinstance(block_length, float) or block_length <= 1:
            raise Exception("Invalid block length. Was: " + str(block_length))
        self.blockLength = block_length
        return self
    
    def withDivisionLength(self, division_length: int | float) -> Self:
        if isinstance(division_length, int):
            division_length = float(division_length)
        if not isinstance(division_length, float) or division_length <= 1:
            raise Exception("Invalid division length. Was: " + str(division_length))
        self.divisionLength = division_length
        return self
    
    def withParkings(self, parkings: int | float) -> Self:
        if isinstance(parkings, float):
            parkings = round(parkings)
        if not isinstance(parkings, int) or parkings < 1:
            raise Exception("Invalid number of parking. Was: " + str(parkings))
        self.parkings = parkings
        return self

    def build(self) -> MapDescriptor:
        MapGenerator.generate(self._type, self.junctions, self.divisions, self.blockLength, self.divisionLength, self.traciConfig.getAssetDirectory(), self.traciConfig.getNetworkFilePath())
        return ParkingFileGenerator.createParkingFile(self.traciConfig.getNetworkFilePath(), self.traciConfig.getParkingFilePath(), self.parkings)
