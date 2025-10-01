import subprocess
import random
import sumolib
from pathlib import Path
from typing import Self
from config.traci_config.TraciConfig import TraciConfig
from config.map_config.MapConfig import MapConfig

class RandomMapBuilder:
    def __init__(self):
        self._type = "spider"
        self.junctions = 3
        self.divisions = 3
        self.parkings = 5
        self.blockLength = 50.00
        self.divisionLength = 30.00
        self.traciConfig = TraciConfig()
        self.mapConfig = MapConfig()

    def withType(self, _type: str) -> Self:
        if _type not in ["grid", "spider", "rand", "final"]:
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
    
    def _createParkingFile(self) -> None:
        network = sumolib.net.readNet(self.traciConfig.getNetworkFilePath())
        output_file = self.traciConfig.getParkingFilePath()

        edges = list(network.getEdges())
        random_edges = random.sample(edges, self.parkings)

        with open(output_file, "w") as file:
            file.write("<additional>\n")

            # Put in custom tricycle and passenger types
            file.write("<vType id=\"trike\" accel=\"0.8\" decel=\"4.5\" sigma=\"0.5\" length=\"2.5\" maxSpeed=\"10.0\" guiShape=\"bicycle\"/>\n")
            file.write(f"<vType id=\"fatPed\" vClass=\"pedestrian\" guiShape=\"pedestrian\" color=\"yellow\" width=\"1\" length=\"1\"/>\n")

            for i, edge in enumerate(random_edges):
                lane = edge.getLanes()[1]  
                lane_id = lane.getID()
                lane_length = lane.getLength()

                start_pos = 5
                end_pos = min(25, lane_length - 1)

                file.write(f"\t<parkingArea id=\"hub{i}\" lane=\"{lane_id}\" startPos=\"{start_pos}\" endPos=\"{end_pos}\" lines=\"3\" roadsideCapacity=\"3\"/>\n")

                self.mapConfig.addHub(f"hub{i}", 3)

            file.write("</additional>\n")
        
        print(f"Wrote parking areas to {self.traciConfig.getParkingFileName()}")

    
    def _generateAndExportMap(self, cmd: list[str]) -> None:
        assets_dir = self.traciConfig.getAssetDirectory()
        assets_dir.mkdir(parents=True, exist_ok=True)

        net_file = self.traciConfig.getNetworkFilePath()

        cmd.append(f"--output-file={net_file}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("Error:", result.stderr)
        else:
            print("Network generated successfully.")

    def getNetworkFilePath(self) -> str:
        return self.traciConfig.getNetworkFilePath()
    
    def getParkingFilePath(self) -> str:
        return self.traciConfig.getParkingFilePath()
    
    def getHubDistribution(self) -> dict:
        return self.mapConfig.getHubDistribution()
    
    def getNumberOfTricycles(self) -> int:
        return self.mapConfig.getNumberOfTricycles()
    
    def build(self) -> MapConfig:
        if self._type == None or self._type not in ["grid", "spider", "rand"]:
            raise Exception("Invalid type. Was: " + type)
        
        cmd = ["netgenerate", "--sidewalks.guess", "--walkingareas", "--crossings.guess", "--junctions.join",]

        if self._type == "final":
            pass
        elif self._type == "grid":
            cmd.append("--grid")
            cmd.append("--grid.x-number=" + str(self.junctions))
            cmd.append("--grid.y-number=" + str(self.divisions))
            cmd.append("--grid.x-length=" + str(self.blockLength))
            cmd.append("--grid.y-length=" + str(self.divisionLength))

        elif self._type == "spider":
            print("Ignoring division length for type 'spider'...")
            cmd.append("--spider")
            cmd.append("--spider.circle-number=" + str(self.junctions))
            cmd.append("--spider.arm-number=" + str(self.divisions))
            cmd.append("--spider.space-radius=" + str(self.blockLength))

        elif self._type == "rand":
            print("Ignoring all numeric arguments...")
            cmd.append("--rand")

        self._generateAndExportMap(cmd)
        self._createParkingFile()

        return self.mapConfig
        