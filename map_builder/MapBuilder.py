import subprocess
import random
import sumolib
from pathlib import Path
from typing import Self

class MapBuilder:
    def __init__(self):
        self._type = None
        self.junctions = 5
        self.divisions = 5
        self.parkings = 5
        self.blockLength = 100.00
        self.divisionLength = 100.00
        self.directoryName = "maps"
        self.networkFileName = "net.net.xml"
        self.parkingFileName = "parking.add.xml"

    def withType(self, _type: str) -> Self:
        if _type not in ["grid", "spider", "rand"]:
            raise Exception("Invalid type. Was: " + _type)
        self._type = _type
        return self

    def withNumberOfJunctions(self, junctions: int) -> Self:
        if not isinstance(junctions, int) or junctions <= 1:
            raise Exception("Invalid number of junctions. Was: " + str(junctions))
        self.junctions = junctions
        return self

    def withNumberOfDivisions(self, divisions: int) -> Self:
        if not isinstance(divisions, int) or divisions <= 1:
            raise Exception("Invalid number of divisions. Was: " + str(divisions))
        self.divisions = divisions
        return self

    def withBlockLength(self, blockLength: float) -> Self:
        if not isinstance(blockLength, float) or blockLength <= 1:
            raise Exception("Invalid block length. Was: " + str(blockLength))
        self.blockLength = blockLength
        return self
    
    def withDivisionLength(self, divisionLength: float) -> Self:
        if not isinstance(divisionLength, float) or divisionLength <= 1:
            raise Exception("Invalid division length. Was: " + str(divisionLength))
        self.divisionLength = divisionLength
        return self
    
    def withParkings(self, parkings: int) -> Self:
        if not isinstance(parkings, int) or parkings < 1:
            raise Exception("Invalid number of parking. Was: " + str(parkings))
        self.parkings = parkings
        return self
    
    def _createParkingFile(self) -> None:
        directory = Path(__file__).resolve().parent.parent / self.directoryName 
        network = sumolib.net.readNet(directory / self.networkFileName)
        output_file = directory / self.parkingFileName

        edges = list(network.getEdges())
        random_edges = random.sample(edges, self.parkings)

        with open(output_file, "w") as file:
            file.write("<additional>\n")
            for i, edge in enumerate(random_edges):
                lane = edge.getLanes()[0]  
                lane_id = lane.getID()
                lane_length = lane.getLength()

                start_pos = 5
                end_pos = min(25, lane_length - 1)

                file.write(f"\t<parkingArea id=\"hub{i}\" lane=\"{lane_id}\" startPos=\"{start_pos}\" endPos=\"{end_pos}\" lines=\"3\"/>\n")
            file.write("</additional>\n")
        
        print(f"Wrote parking areas to {self.parkingFileName}")

    
    def _generateAndExportMap(self, cmd: list[str]) -> None:
        script_dir = Path(__file__).resolve().parent
        assets_dir = script_dir.parent / self.directoryName
        assets_dir.mkdir(parents=True, exist_ok=True)

        net_file = assets_dir / self.networkFileName

        cmd.append(f"--output-file={net_file}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("Error:", result.stderr)
        else:
            print("Network generated successfully.")

    def getNetworkFilePath(self) -> str:
        script_dir = Path(__file__).resolve().parent
        assets_dir = script_dir.parent / self.directoryName
        net_file = assets_dir / self.networkFileName
        return str(net_file)
    
    def getParkingFilePath(self) -> str:
        script_dir = Path(__file__).resolve().parent
        assets_dir = script_dir.parent / self.directoryName
        parking_file = assets_dir / self.parkingFileName
        return str(parking_file)

    
    def build(self) -> None:
        if self._type == None or self._type not in ["grid", "spider", "rand"]:
            raise Exception("Invalid type. Was: " + type)
        
        cmd = ["netgenerate"]

        if self._type == "grid":
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
        