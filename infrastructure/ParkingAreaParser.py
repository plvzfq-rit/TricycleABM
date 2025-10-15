import xml.etree.ElementTree as ET
from domain.MapDescriptor import MapDescriptor
class ParkingAreaParser:
    def __init__(self):
        pass

    def parse(parking_file_path: str) -> MapDescriptor:
        tree = ET.parse(parking_file_path)
        root = tree.getroot()
        map_descriptor = MapDescriptor()

        for pa in root.findall("parkingArea"):
            if pa.get("id").startswith("hub"):
                map_descriptor.addHub(pa.get("id"), int(pa.get("roadsideCapacity")))

        return map_descriptor