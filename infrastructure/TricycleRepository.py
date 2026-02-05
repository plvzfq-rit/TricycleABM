import traci

from domain.Location import Location
from domain.Tricycle import Tricycle
from domain.Passenger import Passenger
from domain.TricycleState import TricycleState

from .TricycleFactory import TricycleFactory
from .SumoRepository import SumoRepository
from utils.TraciUtils import getTricycleLocation, checkIfTricycleParked, getListofGasEdges, getListofGasIds
from .SimulationConfig import SimulationConfig
from .SimulationLogger import SimulationLogger

import math

def driver_matrix(given):
    # Starting point
    limit = 1000
    value = 50
    
    # Alternating increments: +20, +30, +20, +30, ...
    increments = [20, 30]
    inc_index = 0  # which increment to use
    
    # Expand ranges until we cover the given input
    while given > limit:
        # Move to next bracket
        value += increments[inc_index]
        limit += 500
        
        # Alternate increment index: 0 -> 1 -> 0 -> 1 ...
        inc_index = 1 - inc_index

    return value

def manila_matrix(given):
    return 16 if given < 1000 else 16 + 5 * math.ceil((given - 1000) / 500)

class TricycleRepository:
    def __init__(self, sumo_service: SumoRepository, tricycle_factory: TricycleFactory,simulation_config: SimulationConfig):
        self.tricycles = dict()
        self.sumoService = sumo_service
        self.tricycleFactory = tricycle_factory
        self.simulationConfig = simulation_config

    def hasActiveTricycles(self) -> bool:
        for tricycle in self.tricycles.values():
            if tricycle.isActive():
                return True
        return False

    def createTricycles(self, number_of_tricycles: int, hub_distribution: dict) -> None:
        # create list of hub tags; each would be assigned to a new tricycle
        hubs = []
        for hub, number_of_tricycles_in_hub in hub_distribution.items():
            for i in range(number_of_tricycles_in_hub):
                hubs.append(hub)

        for i in range(number_of_tricycles):
            assigned_hub = hubs.pop()
            assigned_id = i
            trike_name, tricycle = self.tricycleFactory.createRandomTricycle(assigned_id, assigned_hub)
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
        return set([tricycle_id for tricycle_id in self.tricycles.keys() if self.getTricycle(tricycle_id).isActive() and not self.getTricycle(tricycle_id).isInCooldown() and self.getTricycle(tricycle_id).isFree()])
    
    def getActiveTricycleIds(self) -> set[Tricycle]:
        return set([tricycle_id for tricycle_id in self.tricycles.keys() if self.getTricycle(tricycle_id).isActive() or self.getTricycle(tricycle_id).isFree()])
    
    def getTricycleLocation(self, tricycle_id: str) -> Location:
        return getTricycleLocation(tricycle_id)
    
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
        dest_edge = destination.edge
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

        traci.vehicle.setStop(tricycle_id, dest_edge, laneIndex=passenger.destination.lane, pos=destination.position, duration=60)

        self.getTricycle(tricycle_id).acceptPassenger(destination)
        self.setTricycleDestination(tricycle_id, destination)

        distance = traci.simulation.getDistanceRoad(current_edge, 0, dest_edge, 0, isDriving=True)

        # SCENARIO TESTING
        default_fare = driver_matrix(distance)

        if passenger.willingness_to_pay * distance >= default_fare:
            tricycle.money += default_fare
        else:
            tricycle.money += passenger.willingness_to_pay * distance

        tricycle.recordLog("run002", str(tricycle_id), str(hub_edge), str(dest_edge), str(distance), str(default_fare), str(tick))

        #1. create a trip object
        #2. make a record
        #3. refactor simulationLogger.add
        #4. tricycle is in a "trip" state, 
        return True

    def hasTricycleArrived(self, tricycle_id: str) -> bool:
        return self.getTricycle(tricycle_id).hasArrived()
    
    def isTricycleFree(self, tricycle_id: str) -> bool:
        return self.getTricycle(tricycle_id).isFree()
    
    def isTricycleParked(self, tricycle_id: str) -> bool:
        tricycle = self.tricycles[tricycle_id]
        return checkIfTricycleParked(tricycle_id, tricycle.hub)

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
        current_location = getTricycleLocation(tricycle_id)
        tricycle.consumeGas(current_location)
    
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
        gas_stations_edges = getListofGasEdges()
        gas_stations = getListofGasIds()
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
    
    def refuelTricycle(self, tricycle_id: str) -> float:
        tricycle = self.getTricycle(tricycle_id)
        tricycle.currentGas += tricycle.usualGasPayment / self.simulationConfig.gasPricePerLiter
        gasPrice = tricycle.payForGas()

        traci.vehicle.setSpeed(tricycle_id, -1)
        return gasPrice
    
    def startRefuelAllTricycles(self) -> None:
        for tricycle_id in self.tricycles.keys():
            tricycle = self.getTricycle(tricycle_id)
            if tricycle.getsAFullTank:
                amount = tricycle.maxGas - tricycle.currentGas
                payment = amount * self.simulationConfig.gasPricePerLiter
            else:
                amount = tricycle.usualGasPayment / self.simulationConfig.gasPricePerLiter
                payment = tricycle.usualGasPayment
                if amount + tricycle.currentGas > tricycle.maxGas:
                    amount = tricycle.maxGas - tricycle.currentGas
                    payment = amount * self.simulationConfig.gasPricePerLiter
            tricycle.money -= payment
            tricycle.currentGas += amount
            self.simulationLogger.addExpenseToLog(tricycle_id, "end_gas", payment, 1080)

    def startExpenseAllTricycles(self) -> None:
        for tricycle_id in self.tricycles.keys():
            tricycle = self.getTricycle(tricycle_id)
            tricycle.money -= tricycle.dailyExpense
            self.simulationLogger.addExpenseToLog(tricycle_id, "daily_expense", tricycle.dailyExpense, 1080)

    def changeLogger(self, simulationLogger) -> None:
        self.simulationLogger = simulationLogger

