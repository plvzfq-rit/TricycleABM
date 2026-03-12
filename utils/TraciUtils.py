"""Utility functions for interacting with SUMO via TraCI.

This module provides helper functions for managing tricycle vehicles in
the SUMO simulation, including spawning, positioning, routing, and state queries.
"""

import traci

from domain.Location import Location


def getListOfHubIds() -> list[str]:
    """Get all TODA hub identifiers in the simulation.
    
    :return: List of hub ID strings.
    :rtype: list[str]
    """
    hub_ids = ["hub0", "hub1", "hub2", "hub3", "hub4", "hub5", "hub6", "hub7", "hub8"]
    return hub_ids


def getTricycleLocation(tricycle_id: str) -> Location | None:
    """Get the current location of a tricycle in the SUMO simulation.
    
    Queries the SUMO network for the tricycle's road, position, and lane.
    
    :param tricycle_id: Identifier of the tricycle vehicle.
    :type tricycle_id: str
    :return: Location object with the tricycle's current position, or None if the tricycle is not found in the simulation.
    :rtype: Location | None
    """
    try:
        current_edge = traci.vehicle.getRoadID(tricycle_id)
        current_position = traci.vehicle.getLanePosition(tricycle_id)
        current_lane = traci.vehicle.getLaneIndex(tricycle_id)
        return Location(current_edge, current_position, current_lane)
    except traci.exceptions.TraCIException:
        return None


def getTricycleHubEdge(hub_string: str) -> str:
    """Get the edge ID corresponding to a TODA hub.
    
    :param hub_string: Hub identifier (e.g., "hub0").
    :type hub_string: str
    :return: Edge ID where the hub is located.
    :rtype: str
    """
    HUB_EDGE_MAPPING = {
        "hub0": "E196",
        "hub1": "E154",
        "hub2": "E74",
        "hub3": "E97",
        "hub4": "E106",
        "hub5": "E41",
        "hub6": "E57",
        "hub7": "E162",
        "hub8": "E23"
    }
    return HUB_EDGE_MAPPING[hub_string]


def returnTricycleToHub(tricycle_id: str, hub_string: str) -> None:
    """Send a tricycle to a parking area at a hub.
    
    Instructs the vehicle to proceed to and park at the specified hub's
    parking area.
    
    :param tricycle_id: Identifier of the tricycle vehicle.
    :type tricycle_id: str
    :param hub_string: Hub identifier where the tricycle should park.
    :type hub_string: str
    """
    try:
        traci.vehicle.setParkingAreaStop(tricycle_id, hub_string, duration=99999)
    except traci.exceptions.TraCIException:
        pass


def initializeTricycle(tricycle_id: str, hub_string: str) -> None:
    """Initialize and spawn a tricycle into the SUMO simulation.
    
    Creates a route for the tricycle, adds it to the simulation, sets
    its initial speed, and sends it to the hub's parking area.
    
    :param tricycle_id: Identifier for the new tricycle vehicle.
    :type tricycle_id: str
    :param hub_string: Hub identifier where the tricycle should start.
    :type hub_string: str
    """
    route_id = f"route_{tricycle_id}"
    hub_edge = getTricycleHubEdge(hub_string)
    if route_id not in traci.route.getIDList():
        traci.route.add(route_id, [hub_edge])
    traci.vehicle.add(tricycle_id, route_id, "trike", departLane="free", departPos="free", departSpeed="0")
    traci.vehicle.setSpeed(tricycle_id, 8.33)
    returnTricycleToHub(tricycle_id, hub_string)


def removeTricycle(tricycle_id: str) -> None:
    """Remove a tricycle from the SUMO simulation.
    
    :param tricycle_id: Identifier of the tricycle vehicle to remove.
    :type tricycle_id: str
    """
    try:
        traci.vehicle.remove(tricycle_id)
    except traci.exceptions.TraCIException:
        pass


def hasTricycleParked(tricycle_id: str) -> bool:
    """Check if a tricycle is currently parked in a parking area.
    
    :param tricycle_id: Identifier of the tricycle vehicle.
    :type tricycle_id: str
    :return: True if the tricycle is stopped at a parking area, False otherwise.
    :rtype: bool
    """
    try:
        return traci.vehicle.isStoppedParking(tricycle_id)
    except traci.exceptions.TraCIException:
        return False
