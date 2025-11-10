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
    
    def getGoingToRefuelTricycleIds(self) -> list[Tricycle]:
        return set([tricycle_id for tricycle_id in self.tricycles.keys() if self.getTricycle(tricycle_id).isGoingToRefuel()])
    
    def getActiveTricycles(self) -> set[Tricycle]:
        return set([tricycle for tricycle in self.tricycles.values() if tricycle.isActive()])
    
    def getActiveFreeTricycleIds(self) -> set[Tricycle]:
        return set([tricycle_id for tricycle_id in self.tricycles.keys() if self.getTricycle(tricycle_id).isActive()])
    
    def getActiveTricycleIds(self) -> set[Tricycle]:
        return set([tricycle_id for tricycle_id in self.tricycles.keys() if self.getTricycle(tricycle_id).isActive() and self.getTricycle(tricycle_id).isFree()])
    
    def getTricycleLocation(self, tricycle_id: str) -> Location:
        return self.traciService.getTricycleLocation(tricycle_id)
    
    #Any tricycle literally moving
    def getBusyTricycleIds(self) -> set[str]:
        return set([tricycle_id for tricycle_id in self.tricycles.keys() if self.getTricycle(tricycle_id).state not in{ TricycleState.FREE, TricycleState.REFUELLING, TricycleState.DEAD, TricycleState.TO_SPAWN, TricycleState.PARKED}])
    
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

    def activateTricycle(self, tricycle_id: str):
        self.getTricycle(tricycle_id).activate()

    def killTricycle(self, tricycle_id: str):
        self.getTricycle(tricycle_id).kill()

    def redirectTricycleToToda(self, tricycle_id: str):
        self.getTricycle(tricycle_id).returnToToda()

    def updateTricycleLocation(self, tricycle_id: str, current_location: Location):
        self.getTricycle(tricycle_id).setLastLocation(current_location)

    #FUNCTIONS FOR GAS CONSUMPTION AND GAS REFUELLING
    def simulateGasConsumption(self) -> None:
        tricyles_ids = self.getBusyTricycleIds()
        for tricycle_id in tricyles_ids:
            tricycle = self.getTricycle(tricycle_id)
            tricycle.consumeGas()
            if tricycle.currentGas <= 0:
                tricycle.state = TricycleState.GOING_TO_REFUEL
                self.rerouteToGasStation(tricycle_id)
        return
    
    def rerouteToGasStation(self,tricycle_id: str) -> None:
        tricycle = self.getTricycle(tricycle_id)
        gas_stations = self.traciService.getListofGasEdges()

        start_edge = traci.vehicle.getRoadID(tricycle_id)
        
        nearest_station_edge = min(
            gas_stations,
            key=lambda edge_id: traci.simulation.findRoute(start_edge, edge_id).travelTime
        )

        hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
        current_edge = traci.vehicle.getRoadID(tricycle_id)

        to_route = traci.simulation.findRoute(current_edge, nearest_station_edge)
        return_route = traci.simulation.findRoute(nearest_station_edge, hub_edge)

        full_route = list(to_route.edges) + list(return_route.edges)[1:]

        traci.vehicle.setRoute(tricycle_id, full_route)

        traci.vehicle.setStop(
            vehID= tricycle_id,
            edgeID= nearest_station_edge,
            duration=9999,
            flags=0x01 | 0x02
        )
        return
    
    def CheckGasStationForTricycles(self ) -> None:
        tricycle_ids = self.getGoingToRefuelTricycleIds()

        for tricycle_id in tricycle_ids:
            route = traci.vehicle.getRoute(tricycle_id)
            current_edge = traci.vehicle.getRoadID(tricycle_id)

            if current_edge == route[-1]:
                print("I hate thesis :D")

        return
