"""Module for dispatching tricycles to waiting passengers.

Provides the TricycleDispatcher class which manages the process of assigning
tricycles to passenger requests based on availability, demand probabilities,
and geographic constraints.
"""

from domain.Location import Location, getManhattanDistance

from config.SimulationConfig import SimulationConfig
from infrastructure.TricycleRepository import TricycleRepository
from infrastructure.TodaRepository import TodaRepository
from infrastructure.PassengerFactory import PassengerFactory
from domain.TricycleState import TricycleState
from utils.TraciUtils import getTricycleLocation, getTricycleHubEdge

import math
import random

class TricycleDispatcher:
    """Dispatches tricycles to passenger requests from TODA queues.
    
    Manages the process of attempting to match tricycles with waiting
    passengers, handling dispatch acceptance/rejection and logging.
    
    :ivar tricycleRepository: Repository of tricycle objects.
    :ivar passengerFactory: Factory for creating passenger instances.
    :ivar peakHourProbabilities: Hourly demand probabilities.
    """

    def __init__(self, tricycle_repository: TricycleRepository, passenger_factory: PassengerFactory, 
                 simulation_config: SimulationConfig) -> None:
        """Initialize the dispatcher.
        
        :param tricycle_repository: TricycleRepository object.
        :type tricycle_repository: TricycleRepository
        :param passenger_factory: PassengerFactory object.
        :type passenger_factory: PassengerFactory
        :param simulation_config: SimulationConfig file (for demand probabilities).
        :type simulation_config: SimulationConfig
        """
        self.tricycleRepository = tricycle_repository
        self.passengerFactory = passenger_factory
        self.peakHourProbabilities = simulation_config.getPeakHourProbabilities()

    def shouldAttemptDispatch(self, tick: int) -> bool:
        """Using peak hour probabilities and math.random, convert current tick to hour and determine if a dispatch occurs.
        
        :param tick: Current simulation tick.
        :type tick: int
        :return: True if a dispatch should be attempted, False otherwise.
        :rtype: bool
        """
        curr_prob = self.peakHourProbabilities[math.floor(tick / 60 / 60)] / 60.0
        return random.random() < curr_prob

    def tryDispatchFromTodaQueues(self, simulationLogger, tick: int, todaRepository: TodaRepository) -> None:
        """Attempt to dispatch tricycles to passengers from all TODA queues.
        
        Iterates through TODA queues in random order, attempting to match
        waiting tricycles with newly generated passenger requests.
        
        :param simulationLogger: Logger for recording results.
        :param tick: Current simulation time.
        :type tick: int
        :param todaRepository: Repository of TODA queues.
        :type todaRepository: TodaRepository
        """
        todaQueues = todaRepository.getAllToda()

        todaQueues = list(todaQueues)
        random.shuffle(todaQueues)

        for toda in todaQueues:
            if not todaRepository.canTodaDispatch(toda):
                continue

            if not self.shouldAttemptDispatch(tick):
                continue

            # Peek at first tricycle without removing from queue
            tricycle_id = todaRepository.peekToda(toda)
            tricycle = self.tricycleRepository.getTricycle(tricycle_id)

            # Only proceed if tricycle is FREE (physically back in TODA and ready)
            if not tricycle.isFree():
                continue

            hub_edge = getTricycleHubEdge(tricycle.getHub())
            passenger = self.passengerFactory.createRandomPassenger(hub_edge)
            passenger_destination = passenger.getDestination()

            if tricycle.canAcceptDispatch(passenger_destination):
                success = self.tricycleRepository.dispatchTricycle(tricycle_id, passenger, simulationLogger, tick)
                if success == None:
                    pass
                elif success:
                    simulationLogger.recordAcceptedTrip()
                    # Only remove from queue on successful dispatch
                    todaRepository.dequeToda(toda)
                else:
                    simulationLogger.recordRejectedTrip()
            else:
                simulationLogger.recordRejectedTrip()
