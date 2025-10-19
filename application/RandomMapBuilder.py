import random
from pathlib import Path
from typing import Self
from infrastructure.SimulationConfig import SimulationConfig
from domain.MapDescriptor import MapDescriptor
from infrastructure.MapGenerator import MapGenerator
from infrastructure.ParkingFileGenerator import ParkingFileGenerator

class RandomMapBuilder:
    def __init__(self, simulation_config: SimulationConfig | None = None, 
                parking_file_generator: ParkingFileGenerator | None = None,
                map_generator: MapGenerator | None = None):
        self._type = "spider"
        self.junctions = 3
        self.divisions = 3
        self.parkings = 5
        self.blockLength = 50.00
        self.divisionLength = 30.00
        self.simulationConfig = simulation_config or SimulationConfig()
        self.parkingFileGenerator = parking_file_generator or ParkingFileGenerator()
        self.mapGenerator = map_generator or MapGenerator()

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
        self.mapGenerator.create(self._type, self.junctions, self.divisions, self.blockLength, self.divisionLength, self.simulationConfig.getAssetDirectory(), self.simulationConfig.getNetworkFilePath())
        return self.parkingFileGenerator.createParkingFile(self.simulationConfig.getNetworkFilePath(), self.simulationConfig.getParkingFilePath(), self.parkings)
