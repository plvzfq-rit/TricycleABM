import subprocess
from pathlib import Path
from typing import Self

class MapBuilder:
    def __init__(self):
        self._type = None
        self.blocks = 5
        self.divisions = 5
        self.blockLength = 100.00
        self.divisionLength = 100.00
        self.directoryName = "maps"
        self.fileName = "net.net.xml"

    def withType(self, _type: str) -> Self:
        if _type not in ["grid", "spider", "rand"]:
            raise Exception("Invalid type. Was: " + _type)
        self._type = _type
        return self

    def withNumberOfBlocks(self, blocks: int) -> Self:
        if type(blocks) is not int and blocks <= 1:
            raise Exception("Invalid number of blocks. Was: " + str(blocks))
        self.blocks = blocks
        return self

    def withNumberOfDivisions(self, divisions: int) -> Self:
        if type(divisions) is not int and divisions <= 1:
            raise Exception("Invalid number of divisions. Was: " + str(divisions))
        self.divisions = divisions
        return self

    def withBlockLength(self, blockLength: float) -> Self:
        if type(blockLength) is not float and blockLength <= 1:
            raise Exception("Invalid block length. Was: " + str(blockLength))
        self.blockLength = blockLength
        return self
    
    def withDivisionLength(self, divisionLength: float) -> Self:
        if type(divisionLength) is not float and divisionLength <= 1:
            raise Exception("Invalid division length. Was: " + str(divisionLength))
        self.divisionLength = divisionLength
        return self
    
    def build(self) -> None:
        if self._type == None or self._type not in ["grid", "spider", "rand"]:
            raise Exception("Invalid type. Was: " + type)
        
        cmd = ["netgenerate"]

        if self._type == "grid":
            cmd.append("--grid")
            cmd.append("--grid.x-number=" + str(self.blocks))
            cmd.append("--grid.y-number=" + str(self.divisions))
            cmd.append("--grid.x-length=" + str(self.blockLength))
            cmd.append("--grid.y-length=" + str(self.divisionLength))

        elif self._type == "spider":
            print("Ignoring division length for type 'spider'...")
            cmd.append("--spider")
            cmd.append("--spider.circle-number=" + str(self.blocks))
            cmd.append("--spider.arm-number=" + str(self.divisions))
            cmd.append("--spider.space-radius=" + str(self.blockLength))

        elif self._type == "rand":
            print("Ignoring all numeric arguments...")
            cmd.append("--rand")

        script_dir = Path(__file__).resolve().parent
        assets_dir = script_dir.parent / self.directoryName
        assets_dir.mkdir(parents=True, exist_ok=True)

        net_file = assets_dir / self.fileName

        cmd.append(f"--output-file={net_file}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("Error:", result.stderr)
        else:
            print("Network generated successfully.")

