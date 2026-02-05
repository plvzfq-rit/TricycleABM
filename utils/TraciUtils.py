import traci

from domain.Location import Location

def getListOfHubIds() -> list[str]:
    hub_ids = []
    parking_area_ids = traci.parkingarea.getIDList()
    for parking_area_id in parking_area_ids:
        if parking_area_id[0:3] == "hub":
            hub_ids.append(parking_area_id)
    return hub_ids

def getListofGasEdges() -> list[str]:
    hub_ids = []
    parking_area_ids = traci.parkingarea.getIDList()
    for gas_station_id in parking_area_ids:
        if gas_station_id.lower().startswith("gas"):
            edge = traci.parkingarea.getLaneID(gas_station_id).split("_")[0]
            hub_ids.append(edge)
    return hub_ids

def getListofGasIds() -> list[str]:
    hub_ids = []
    parking_area_ids = traci.parkingarea.getIDList()
    for gas_station_id in parking_area_ids:
        if gas_station_id.lower().startswith("gas"):
            hub_ids.append(gas_station_id)
    return hub_ids

def getTricycleLocation(tricycle_id: str) -> Location | None:
    if not checkIfTricycleInSimulation(tricycle_id):
        return None
    current_edge = traci.vehicle.getRoadID(tricycle_id)
    current_position = traci.vehicle.getLanePosition(tricycle_id)
    current_lane = traci.vehicle.getLaneIndex(tricycle_id)
    return Location(current_edge, current_position, current_lane)

def getTricycleHubEdge(hub_string: str) -> str:
    return traci.parkingarea.getLaneID(hub_string).split("_")[0]

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

def getTricycleIds():
    return [tricycle_id for tricycle_id in list(traci.vehicle.getIDList()) if tricycle_id.startswith('trike')]

def checkIfTricycleInSimulation(tricycle_id):
    return tricycle_id in getTricycleIds()

def checkIfTricycleParked(tricycle_id: str, tricycle_hub: str) -> bool:
    try:
        return tricycle_id in traci.parkingarea.getVehicleIDs(tricycle_hub)
    except traci.TraCIException:
        return False

def getNumberOfLanes(edge:str)->int:
    return traci.edge.getLaneNumber(edge)

def getLaneLength(lane_id:str)->float:
    return traci.lane.getLength(lane_id)

