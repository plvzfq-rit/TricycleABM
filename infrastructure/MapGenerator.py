import subprocess
class MapGenerator:
    def create(self, _type: str, junctions: int, divisions: int, block_length: float, division_length: float, asset_directory: str, network_file_path: str) -> None:
        cmd = MapGenerator._buildCommand(_type, junctions, divisions, block_length, division_length)
        assets_dir = asset_directory
        assets_dir.mkdir(parents=True, exist_ok=True)

        net_file = network_file_path

        cmd.append(f"--output-file={net_file}")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("Error:", result.stderr)
        else:
            print("Network generated successfully.")

    def _buildCommand(_type: str, junctions: int, divisions: int, block_length: float, division_length: float) -> list[str]:
        if _type == None or _type not in ["grid", "spider", "rand"]:
            raise Exception("Invalid type. Was: " + type)
        
        cmd = ["netgenerate", "--sidewalks.guess", "--walkingareas", "--crossings.guess", "--junctions.join",]

        if _type == "grid":
            cmd.append("--grid")
            cmd.append("--grid.x-number=" + str(junctions))
            cmd.append("--grid.y-number=" + str(divisions))
            cmd.append("--grid.x-length=" + str(block_length))
            cmd.append("--grid.y-length=" + str(division_length))

        elif _type == "spider":
            print("Ignoring division length for type 'spider'...")
            cmd.append("--spider")
            cmd.append("--spider.circle-number=" + str(junctions))
            cmd.append("--spider.arm-number=" + str(divisions))
            cmd.append("--spider.space-radius=" + str(block_length))

        elif _type == "rand":
            print("Ignoring all numeric arguments...")
            cmd.append("--rand")

        return cmd