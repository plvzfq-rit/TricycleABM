import traci

from domain.Location import Location
from domain.Tricycle import Tricycle
from domain.Passenger import Passenger
from infrastructure.TricycleFactory import TricycleFactory
from domain.TricycleState import TricycleState
from infrastructure.SumoService import SumoService
from infrastructure.TraciService import TraciService
from infrastructure.SimulationConfig import SimulationConfig
from infrastructure.SimulationLogger import SimulationLogger

import math


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
        return set([tricycle_id for tricycle_id in self.tricycles.keys() if self.getTricycle(tricycle_id).isActive() or self.getTricycle(tricycle_id).isFree()])
    
    def getTricycleLocation(self, tricycle_id: str) -> Location:
        return self.traciService.getTricycleLocation(tricycle_id)
    
    #Any tricycle literally moving
    def getBusyTricycleIds(self) -> set[str]:
        return set([tricycle_id for tricycle_id in self.tricycles.keys() if self.getTricycle(tricycle_id).state not in{ TricycleState.FREE, TricycleState.REFUELLING, TricycleState.DEAD, TricycleState.TO_SPAWN, TricycleState.PARKED}])
    
    def setTricycleDestination(self, tricycle_id: str, destination: Location) -> None:
        if tricycle_id in self.tricycles.keys():
            self.getTricycle(tricycle_id).setDestination(destination)
    
    #TODO: Refactor this!!
    def dispatchTricycle(self, tricycle_id: str, passenger: Passenger, simulationLogger, tick) -> bool:
        tricycle = self.tricycles[tricycle_id]
        destination = passenger.destination

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
        try:
            traci.vehicle.setParkingAreaStop(tricycle_id, self.tricycles[tricycle_id].hub, duration=0)
        except:
            pass

        to_route = traci.simulation.findRoute(current_edge, dest_edge)
        return_route = traci.simulation.findRoute(dest_edge, hub_edge)

        full_route = list(to_route.edges) + list(return_route.edges)[1:]

        traci.vehicle.setRoute(tricycle_id, full_route)

        traci.vehicle.setStop(tricycle_id, dest_edge, laneIndex=1, pos=destination.position, duration=10)

        self.getTricycle(tricycle_id).acceptPassenger(destination)
        self.setTricycleDestination(tricycle_id, destination)

        distance = traci.simulation.getDistanceRoad(current_edge, 0, dest_edge, 0, isDriving=True)

        #TODO
        # if : # something something bargain
            # do bargaining
        # else:
        default_fare = 16 if distance < 1000 else 16 + 5 * math.ceil((distance - 1000) / 500)



        simulationLogger.add("run002", tricycle_id, hub_edge, dest_edge, distance, default_fare, tick)
        return True

    def hasTricycleArrived(self, tricycle_id: str) -> bool:
        return self.getTricycle(tricycle_id).hasArrived()
    
    def isTricycleFree(self, tricycle_id: str) -> bool:
        return self.getTricycle(tricycle_id).isFree()
    
    def isTricycleParked(self, tricycle_id: str) -> bool:
        tricycle = self.tricycles[tricycle_id]
        return self.traciService.checkIfTricycleParked(tricycle_id, tricycle.hub)

    def activateTricycle(self, tricycle_id: str):
        self.getTricycle(tricycle_id).activate()

    def killTricycle(self, tricycle_id: str):
        self.getTricycle(tricycle_id).kill()

    def redirectTricycleToToda(self, tricycle_id: str):
        self.getTricycle(tricycle_id).returnToToda()

    def updateTricycleLocation(self, tricycle_id: str, current_location: Location):
        self.getTricycle(tricycle_id).setLastLocation(current_location)

    #FUNCTIONS FOR GAS CONSUMPTION AND GAS REFUELLING
    def simulateGasConsumption(self, tricycle_id: str) -> None:
        tricycle = self.getTricycle(tricycle_id)
        current_location = self.traciService.getTricycleLocation(tricycle_id)
        tricycle.consumeGas(current_location)
        return
    
    def rerouteToGasStation(self,tricycle_id: str) -> None:

        tricycle = self.getTricycle(tricycle_id)
        gasHub_id = self.findClosestGasStation(tricycle_id)
        gasHub_edge = traci.parkingarea.getLaneID(gasHub_id).split("_")[0]

        hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
        current_edge = traci.vehicle.getRoadID(tricycle_id)

        to_route = traci.simulation.findRoute(current_edge, gasHub_edge)
        return_route = traci.simulation.findRoute(gasHub_edge, hub_edge)

        full_route = list(to_route.edges) + list(return_route.edges)[1:]

        traci.vehicle.setRoute(tricycle_id, full_route)
        try:
            traci.vehicle.setParkingAreaStop(
                vehID= tricycle_id,
                stopID= gasHub_id,
                duration=2
            )
        except Exception:
            pass
        return
    
    def findClosestGasStation(self, tricycle_id: str) -> str:
        start_edge = traci.vehicle.getRoadID(tricycle_id)
        gas_stations_edges = self.traciService.getListofGasEdges()
        gas_stations = self.traciService.getListofGasIds()
        nearest_station_edge = min(
            gas_stations_edges,
            key=lambda edge_id: traci.simulation.findRoute(start_edge, edge_id).travelTime
        )
        for gas_id in gas_stations:
            parking_lane=traci.parkingarea.getLaneID(gas_id).split("_")[0]
            if parking_lane == nearest_station_edge:
                hub_id = gas_id
                return hub_id
        return "No Gas Station Found!"
    
    def refuelTricycle(self, tricycle_id: str) -> None:
        tricycle = self.getTricycle(tricycle_id)
        tricycle.currentGas = tricycle.maxGas
        tricycle.payForGas()
        traci.vehicle.setSpeed(tricycle_id, -1)
        return

