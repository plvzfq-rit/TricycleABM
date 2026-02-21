import traci

from domain.Location import Location

def getListOfHubIds() -> list[str]:
    hub_ids = ["hub0", "hub1", "hub2", "hub3", "hub4", "hub5", "hub6", "hub7", "hub8"]
    # parking_area_ids = traci.parkingarea.getIDList()
    # for parking_area_id in parking_area_ids:
    #     if parking_area_id[0:3] == "hub":
    #         hub_ids.append(parking_area_id)
    return hub_ids

def getTricycleLocation(tricycle_id: str) -> Location | None:
    try:
        current_edge = traci.vehicle.getRoadID(tricycle_id)
        current_position = traci.vehicle.getLanePosition(tricycle_id)
        current_lane = traci.vehicle.getLaneIndex(tricycle_id)
        return Location(current_edge, current_position, current_lane)
    except traci.exceptions.TraCIException:
        return None

def getTricycleHubEdge(hub_string: str) -> str:
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
    # return traci.parkingarea.getLaneID(hub_string).split("_")[0]

def returnTricycleToHub(tricycle_id: str, hub_string: str) -> None:
    traci.vehicle.setParkingAreaStop(tricycle_id, hub_string, duration=99999)

def initializeTricycle(tricycle_id: str, hub_string: str) -> None:
    route_id = f"route_{tricycle_id}"
    hub_edge = getTricycleHubEdge(hub_string)
    traci.route.add(route_id, [hub_edge])
    traci.vehicle.add(tricycle_id, route_id, "trike", departLane="free", departPos="free", departSpeed="0")
    # brute force entry
    # traci.vehicle.moveTo(tricycle_id, hub_edge + "_0", 0)
    traci.vehicle.setSpeed(tricycle_id, 8.33)
    returnTricycleToHub(tricycle_id, hub_string)

def removeTricycle(tricycle_id: str) -> None:
    traci.vehicle.remove(tricycle_id)

def hasTricycleParked(tricycle_id: str):
    try:
        return traci.vehicle.isStoppedParking(tricycle_id)
    except traci.exceptions.TraCIException:
        return False
