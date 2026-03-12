"""Main repository for managing tricycles in the simulation.

Contains methods for creation, querying, bargaining, routing, and dispatching
of tricycle objects in the simulation.
"""

import random
import traci

from domain.Location import Location
from domain.Tricycle import Tricycle
from domain.Passenger import Passenger
from domain.TricycleState import TricycleState

from .TricycleFactory import TricycleFactory
from .SumoRepository import SumoRepository
from utils.TraciUtils import getTricycleHubEdge, getTricycleLocation
from config.SimulationConfig import SimulationConfig
from .SimulationLogger import SimulationLogger

import math


def driver_matrix(given: float, base_price: float = 50) -> float:
    """Calculate driver-side base fare estimation for a bargaining scenario.

    Implements a dynamic pricing matrix with alternating increments:
    0-1000m: base_price
    Additional 500m (or fraction thereof): +20
    Additional 500m (or fraction thereof) after first 500m: +30

    :param given: Distance in meters
    :type given: float
    :param base_price: Starting price for calculation (aspired or minimum). Defaults to 50
    :type base_price: float
    :return: Driver-side price
    :rtype: float
    """
    # Starting point
    limit = 1000
    value = base_price
    
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


class TricycleRepository:
    """Repository managing the fleet of tricycles in the simulation.
    
    :ivar tricycles: Dictionary mapping tricycle IDs to Tricycle objects.
    :ivar sumoService: SumoRepository instance for SUMO network queries.
    :ivar tricycleFactory: Factory for creating new Tricycle instances.
    :ivar simulationConfig: Global simulation configuration.
    :ivar simulationLogger: Logger for recording tricycle operations.
    """
    def __init__(self, sumo_service: SumoRepository, tricycle_factory: TricycleFactory, 
                 simulation_config: SimulationConfig) -> None:
        """Initialize the tricycle repository.
        
        :param sumo_service: SumoRepository for network queries.
        :type sumo_service: SumoRepository
        :param tricycle_factory: Factory for creating tricycle instances.
        :type tricycle_factory: TricycleFactory
        :param simulation_config: Simulation configuration with distribution methods.
        :type simulation_config: SimulationConfig
        """
        self.tricycles = dict()
        self.sumoService = sumo_service
        self.tricycleFactory = tricycle_factory
        self.simulationConfig = simulation_config

    def createTricycles(self, number_of_tricycles: int, hub_distribution: dict) -> None:
        """Initialize tricycles by hubs.
        
        :param number_of_tricycles: Total number of tricycles to create.
        :type number_of_tricycles: int
        :param hub_distribution: Dict mapping hub names to number of tricycles per hub.
        :type hub_distribution: dict
        """
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
        """Get a tricycle instance by its ID.
        
        :param tricycle_id: Unique identifier of the tricycle.
        :type tricycle_id: str
        :return: Tricycle object with the given ID.
        :rtype: Tricycle
        """
        return self.tricycles[tricycle_id]
    
    def getTricycles(self) -> list[Tricycle]:
        """Gets all tricycle objects.
        
        :return: List of all Tricycle objects.
        :rtype: list[Tricycle]
        """
        return list(self.tricycles.values())
    
    def getTricycleLocation(self, tricycle_id: str) -> Location:
        """Get the current location of a tricycle.
        
        :param tricycle_id: ID of the tricycle.
        :type tricycle_id: str
        :return: Location object with current position.
        :rtype: Location
        """
        return getTricycleLocation(tricycle_id)

    def setTricycleDestination(self, tricycle_id: str, destination: Location) -> None:
        """Set the destination for a tricycle.
        
        :param tricycle_id: ID of the tricycle.
        :type tricycle_id: str
        :param destination: Destination Location object.
        :type destination: Location
        """
        if tricycle_id in self.tricycles.keys():
            self.getTricycle(tricycle_id).setDestination(destination)
    
    def dispatchTricycle(self, tricycle_id: str, passenger: Passenger, 
                        simulationLogger: SimulationLogger, tick: int) -> bool:
        """Dispatch a tricycle to start a trip with negotiated fare.
        
        Simulates bargaining between driver and passenger over rounds.
        
        :param tricycle_id: ID of tricycle to dispatch.
        :type tricycle_id: str
        :param passenger: Passenger object with destination and preferences.
        :type passenger: Passenger
        :param tick: Current simulation tick.
        :type tick: int
        :return: True if dispatch successful, False/None if failed.
        :rtype: bool
        """
        tricycle = self.tricycles[tricycle_id]
        destination = passenger.destination
        
        hub_edge = getTricycleHubEdge(tricycle.getHub())
        dest_edge = destination.edge
        current_edge = hub_edge

        if current_edge == dest_edge:
            return None
        
        distance = traci.simulation.getDistanceRoad(current_edge, 0, dest_edge, 0, isDriving=True)
        
        # Bargaining Algorithm Start
        driver_patience = tricycle.getPatience()
        passenger_patience = passenger.getPatience()

        driver_price_1 = round(driver_matrix(distance, tricycle.getAspiredPrice()), 2)
        driver_price_2 = round(driver_matrix(distance, tricycle.minimumPrice), 2)

        min_price = min(driver_price_1, driver_price_2)
        init_driver_asp = max(driver_price_1, driver_price_2)
        driver_asp = init_driver_asp
        max_price = round(passenger.willingness_to_pay * distance / 1000, 2)
        init_passenger_asp = round(passenger.getAspiredPrice() * distance / 1000, 2)
        passenger_asp = init_passenger_asp

        base_price = round(self.simulationConfig.matrix(distance), 2)
        curr_offer = base_price

        driver_sentinel = 0
        passenger_sentinel = 1
        turn = driver_sentinel if random.random() < 0.5 else passenger_sentinel
        first = True
        agree = False
        max_turns = 2
        for i in range(max_turns):
            driver_asp = round(max(min_price, driver_asp * driver_patience), 2)
            passenger_asp = round(max_price - (max_price - passenger_asp) * (passenger_patience ** i), 2)
            if turn == driver_sentinel:
                if curr_offer >= driver_asp:
                    agree = True
                    if first:
                        pass
                    break
                else:
                    curr_offer = driver_asp
                    first = False
                    turn = passenger_sentinel
            elif turn == passenger_sentinel:
                if curr_offer <= passenger_asp:
                    agree = True
                    if first:
                        pass
                    break
                else:
                    curr_offer = passenger_asp
                    first = False
                    turn = driver_sentinel

        if not agree:
            curr_offer = driver_asp
        # Bargaining End

        # If bargaining is successful, access SUMO to direct tricycle to 
        # passenger destination
        net = self.sumoService.getNetwork()
        edge = net.getEdge(dest_edge)
        if edge.getLaneNumber() <= 1:
            return None
        try:
            traci.vehicle.setParkingAreaStop(tricycle_id, self.tricycles[tricycle_id].hub, duration=0)
        except:
            pass

        to_route = traci.simulation.findRoute(current_edge, dest_edge)
        return_route = traci.simulation.findRoute(dest_edge, hub_edge)

        full_route = list(to_route.edges) + list(return_route.edges)[1:]

        try:
            traci.vehicle.setRoute(tricycle_id, full_route)
            traci.vehicle.setStop(tricycle_id, dest_edge, laneIndex=passenger.destination.lane, 
                                 pos=destination.position, duration=60)
        except traci.exceptions.TraCIException:
            return None

        self.getTricycle(tricycle_id).acceptPassenger(destination)
        self.setTricycleDestination(tricycle_id, destination)

        tricycle.recordLog("run002", str(tricycle_id), str(hub_edge), str(dest_edge), str(distance), 
                          str(curr_offer), str(tick), str(driver_asp), str(passenger_asp), str(base_price), 
                          str(init_driver_asp), str(init_passenger_asp))

        return True

    def startExpenseAllTricycles(self, gas_price: float) -> None:
        """Compute and log daily expenses for all tricycles.
        
        :param gas_price: Gas price
        :type gas_price: float
        """
        for tricycle_id in self.tricycles.keys():
            tricycle = self.getTricycle(tricycle_id)

            gas_money = tricycle.dailyDistance / 1000 / tricycle.gasConsumptionRate * gas_price
            self.simulationLogger.addExpenseToLog(tricycle_id, "gas", gas_money, 57600)

            self.simulationLogger.addExpenseToLog(tricycle_id, "daily_expense", tricycle.dailyExpense, 57600)

    def resetAllDailyStats(self) -> None:
        """Reset daily statistics for all tricycles and removes them
        from SUMO.
        
        Removes non-active vehicles from SUMO before resetting their state
        in order to conduct multiple runs continuously.
        """
        for tricycle in self.tricycles.values():
            # Remove surviving vehicles from SUMO before resetting state
            if not tricycle.isDead():
                try:
                    traci.vehicle.remove(tricycle.getName())
                except traci.exceptions.TraCIException:
                    pass
            tricycle.resetDailyStats()

    def changeLogger(self, simulationLogger: SimulationLogger) -> None:
        """Change the simulation logger instance (contains output directory) 
        in order to conduct multiple runs continuously.
        
        :param simulationLogger: New SimulationLogger object to use.
        :type simulationLogger: SimulationLogger
        """
        self.simulationLogger = simulationLogger