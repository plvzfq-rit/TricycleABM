import traci

from domain.Location import Location
from domain.Tricycle import Tricycle
from infrastructure.TricycleFactory import TricycleFactory
from domain.TricycleState import TricycleState
from infrastructure.SumoService import SumoService
from infrastructure.TraciService import TraciService
from infrastructure.SimulationConfig import SimulationConfig


class TricycleRepository:
    def __init__(self, tricycle_factory: TricycleFactory | None = None, traci_service: TraciService | None = None, sumo_service: SumoService | None = None, simulation_config: SimulationConfig | None = None):
        self.tricycles = dict()
        self.tricycleFactory = tricycle_factory or TricycleFactory()
        self.traciService = traci_service or TraciService()
        self.sumoService = sumo_service or SumoService()
        self.simulationConfig = simulation_config or SimulationConfig()

    def createTricycles(self, number_of_tricycles: int, simulation_duration: int, hub_distribution: dict) -> None:
        # create list of hub tags; each would be assigned to a new tricycle
        hubs = []
        for hub, number_of_tricycles_in_hub in hub_distribution.items():
            for i in range(number_of_tricycles_in_hub):
                hubs.append(hub)

        for i in range(number_of_tricycles):
            assigned_hub = hubs.pop()
            assigned_id = i
            trike_name, tricycle = self.tricycleFactory.createRandomTricycle(assigned_id, simulation_duration, assigned_hub)
            self.tricycles[trike_name] = tricycle

    def getTricycle(self, tricycle_id: str) -> Tricycle:
        return self.tricycles[tricycle_id]
    
    def getTricycles(self) -> list[Tricycle]:
        return list(self.tricycles.values())
    
    def getActiveTricycles(self) -> set[Tricycle]:
        return set([tricycle for tricycle in self.tricycles.values() if tricycle.isActive()])
    
    def getActiveTricycleIds(self) -> set[Tricycle]:
        return set([tricycle_id for tricycle_id in self.tricycles.keys() if self.getTricycle(tricycle_id).isActive()])
    
    def getTricycleLocation(self, tricycle_id: str) -> Location:
        return self.traciService.getTricycleLocation(tricycle_id)
    
    def setTricycleDestination(self, tricycle_id: str, destination: Location) -> None:
        if tricycle_id in self.tricycles.keys():
            self.getTricycle(tricycle_id).setDestination(destination)
    
    #TODO: Refactor this!!
    def dispatchTricycle(self, tricycle_id: str, destination: Location) -> bool:
        tricycle = self.tricycles[tricycle_id]

        hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
        dest_edge = destination.location
        current_edge = traci.vehicle.getRoadID(tricycle_id)

        if current_edge == dest_edge:
            #print("Failed to assign.")
            return False

        net = self.sumoService.getNetwork()
        edge = net.getEdge(dest_edge)
        if edge.getLaneNumber() <= 1:
            return False

        traci.vehicle.setParkingAreaStop(tricycle_id, self.tricycles[tricycle_id].hub, duration=0)

        to_route = traci.simulation.findRoute(current_edge, dest_edge)
        return_route = traci.simulation.findRoute(dest_edge, hub_edge)

        full_route = list(to_route.edges) + list(return_route.edges)[1:]

        traci.vehicle.setRoute(tricycle_id, full_route)

        traci.vehicle.setStop(tricycle_id, dest_edge, laneIndex=1, pos=destination.position, duration=10)

        self.getTricycle(tricycle_id).acceptPassenger(destination)
        self.setTricycleDestination(tricycle_id, destination)

        return True

    def hasTricycleArrived(self, tricycle_id: str) -> bool:
        return self.getTricycle(tricycle_id).hasArrived()
    
    def isTricycleFree(self, tricycle_id: str) -> bool:
        return self.getTricycle(tricycle_id).isFree()
    
    def simulateConsumption(self, tricycle_id: str) -> None:
        if tricycle_id in self.tricycles.keys():
            current_location = self.traciService.getTricycleLocation(tricycle_id)
            return self.getTricycle(tricycle_id).consumeGas(current_location)

    def activateTricycle(self, tricycle_id: str):
        self.getTricycle(tricycle_id).activate()

    def killTricycle(self, tricycle_id: str):
        self.getTricycle(tricycle_id).kill()

    def redirectTricycleToToda(self, tricycle_id: str):
        self.getTricycle(tricycle_id).returnToToda()

    def updateTricycleLocation(self, tricycle_id: str, current_location: Location):
        self.getTricycle(tricycle_id).setLastLocation(current_location)


