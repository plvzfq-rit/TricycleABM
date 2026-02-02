import xml.etree.ElementTree as ET
from domain.MapDescriptor import MapDescriptor

def parseParkingAreaFile(parking_file_path: str) -> MapDescriptor:
    """Parses the parking area XML file in the provided file path.
    
    It extracts TODA hub IDs and their corresponding capacities, and
    consolidates them in a MapDescriptor object. It assumes that parking areas
    represented by TODA hubs starts with 'hub'; it ignores other parking areas,
    e.g. 'gas'.

    Args:
        parking_file_path: string containing file path to parking XML file.

    Returns:
        A MapDescriptor object initialized with the values from the parking
        file object i.e., TODA hub IDs and capacities.
    """

    tree = ET.parse(parking_file_path)
    root = tree.getroot()
    map_descriptor = MapDescriptor()

    for parking_area in root.findall("parkingArea"):
        if parking_area.get("id").startswith("hub"):
            parking_area_id = parking_area.get("id")
            parking_area_capacity = int(parking_area.get("roadsideCapacity"))
            map_descriptor.addHub(parking_area_id, parking_area_capacity)

    return map_descriptor