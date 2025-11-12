import traci
from domain.Location import Location
class TraciService:
    def getListOfHubIds(self) -> list[str]:
        hub_ids = []
        parking_area_ids = traci.parkingarea.getIDList()
        for parking_area_id in parking_area_ids:
            if parking_area_id[0:3] == "hub":
                edge = traci.parkingarea.getLaneID(parking_area_id).split("_")[0]
                hub_ids.append(edge)
        return hub_ids
    
    def getListofGasEdges(self) -> list[str]:
        hub_ids = []
        parking_area_ids = traci.parkingarea.getIDList()
        for gas_station_id in parking_area_ids:
            if gas_station_id.lower().startswith("gas"):
                edge = traci.parkingarea.getLaneID(gas_station_id).split("_")[0]
                hub_ids.append(edge)
        return hub_ids
    
    def getListofGasIds(self) -> list[str]:
        hub_ids = []
        parking_area_ids = traci.parkingarea.getIDList()
        for gas_station_id in parking_area_ids:
            if gas_station_id.lower().startswith("gas"):
                hub_ids.append(gas_station_id)
        return hub_ids
    
    def addPassenger(self, name: str, starting_edge: str, starting_position: float):
        traci.person.add(name, starting_edge, starting_position, typeID="fatPed")

    def getPassengerIds(self) -> list[str]:
        return traci.person.getIDList()

    def getPassengerLocation(self, passenger_id: str) -> Location:
        current_edge = traci.person.getRoadID(passenger_id)
        current_position = traci.person.getLanePosition(passenger_id)
        return Location(current_edge, current_position)
    
    def getTricycleLocation(self, tricycle_id: str) -> Location | None:
        if not self.checkIfTricycleInSimulation(tricycle_id):
            return None
        current_edge = traci.vehicle.getRoadID(tricycle_id)
        current_position = traci.vehicle.getLanePosition(tricycle_id)
        return Location(current_edge, current_position)
    
    def setPassengerDestination(self, passenger_id: str, destination_edge, destination_position: float) -> None:
        traci.person.appendWalkingStage(passenger_id, destination_edge.getID(), destination_position)

    def getTricycleHubEdge(self, hub_string: str) -> str:
        return traci.parkingarea.getLaneID(hub_string).split("_")[0]
    
    def returnTricycleToHub(self, tricycle_id: str, hub_string: str) -> None:
        traci.vehicle.setParkingAreaStop(tricycle_id, hub_string, duration=99999)
    
    def initializeTricycle(self, tricycle_id: str, hub_string: str) -> None:
        route_id = f"route_{tricycle_id}"
        hub_edge = self.getTricycleHubEdge(hub_string)
        traci.route.add(route_id, [hub_edge])
        traci.vehicle.add(tricycle_id, route_id, "trike", departLane="best_prob", departPos="last", departSpeed="last")
        # brute force entry
        # traci.vehicle.moveTo(tricycle_id, hub_edge + "_0", 0)
        traci.vehicle.setSpeed(tricycle_id, 8.33)
        self.returnTricycleToHub(tricycle_id, hub_string)

    def removeTricycle(self, tricycle_id: str) -> None:
        traci.vehicle.remove(tricycle_id)

    def getTricycleIds(self):
        return [tricycle_id for tricycle_id in list(traci.vehicle.getIDList()) if tricycle_id.startswith('trike')]
    
    def checkIfTricycleInSimulation(self, tricycle_id):
        return tricycle_id in self.getTricycleIds()
    
    def checkIfTricycleParked(self, tricycle_id: str, tricycle_hub: str) -> bool:
        return tricycle_id in traci.parkingarea.getVehicleIDs(tricycle_hub)