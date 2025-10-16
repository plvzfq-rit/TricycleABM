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
    
    def addPassenger(self, name: str, starting_edge: str, starting_position: float):
        traci.person.add(name, starting_edge, starting_position, typeID="fatPed")

    def getPassengerIds(self) -> list[str]:
        return traci.person.getIDList()

    def getPassengerLocation(self, passenger_id: str) -> Location:
        current_edge = traci.person.getRoadID(passenger_id)
        current_position = traci.person.getLanePosition(passenger_id)
        return Location(current_edge, current_position)
    
    def getTricycleLocation(self, tricycle_id: str) -> Location:
        current_edge = traci.vehicle.getRoadID(tricycle_id)
        current_position = traci.vehicle.getLanePosition(tricycle_id)
        return Location(current_edge, current_position)
    
    def setPassengerDestination(self, passenger_id: str, destination_edge, destination_position: float) -> None:
        traci.person.appendWalkingStage(passenger_id, destination_edge.getID(), destination_position)