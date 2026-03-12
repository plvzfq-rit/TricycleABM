"""Module for parsing SUMO parking area XML files.

Provides utilities to extract TODA hub information from SUMO parking area
configuration files and populate TodaHubDescriptor objects.
"""

import xml.etree.ElementTree as ET
from domain.TodaHubDescriptor import TodaHubDescriptor


def parseParkingAreaFile(parking_file_path: str) -> TodaHubDescriptor:
    """Parse a SUMO parking area XML file to extract TODA hub information.
    
    Extracts TODA hub IDs and their parking capacities, consolidating them
    into a TodaHubDescriptor object. Only parking areas with IDs starting 
    with 'hub' are included; other areas (e.g., 'gas') are ignored.

    :param parking_file_path: Path to the parking area XML file.
    :type parking_file_path: str
    :return: TodaHubDescriptor object initialized with hub IDs and capacities from the parking file.
    :rtype: TodaHubDescriptor
    """
    tree = ET.parse(parking_file_path)
    root = tree.getroot()
    toda_hub_descriptor = TodaHubDescriptor()

    for parking_area in root.findall("parkingArea"):
        if parking_area.get("id").startswith("hub"):
            parking_area_id = parking_area.get("id")
            parking_area_capacity = int(parking_area.get("roadsideCapacity"))
            toda_hub_descriptor.addHub(parking_area_id, parking_area_capacity)

    return toda_hub_descriptor