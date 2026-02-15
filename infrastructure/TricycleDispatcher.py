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

    def __init__(self, tricycle_repository: TricycleRepository, passenger_factory: PassengerFactory, simulation_config: SimulationConfig) -> None:
        self.tricycleRepository = tricycle_repository
        self.passengerFactory = passenger_factory
        self.peakHourProbabilities = simulation_config.getPeakHourProbabilities()

    def shouldAttemptDispatch(self, tick) -> bool:
        curr_prob = self.peakHourProbabilities[math.floor(tick / 60 / 60)] / 60.0
        return random.random() < curr_prob

    def tryDispatchFromTodaQueues(self, simulationLogger, tick, todaRepository: TodaRepository) -> None:

        todaQueues = todaRepository.getAllToda()

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

            tricycle_location = getTricycleLocation(tricycle_id)
            if tricycle_location is None:
                tricycle.kill()
                continue
                
            hub_edge = getTricycleHubEdge(tricycle.getHub())
            passenger = self.passengerFactory.createRandomPassenger(hub_edge)
            passenger_destination = passenger.getDestination()

            if tricycle.canAcceptDispatch(passenger_destination):
                success = self.tricycleRepository.dispatchTricycle(tricycle_id, passenger, simulationLogger, tick)
                if success:
                    todaRepository.dequeToda(toda)
                else:
                    pass
                    # simulationLogger.recordRejectedTrip()
            else:
                transaction = [tricycle_id, passenger.name, getManhattanDistance(getTricycleLocation(tricycle.name), passenger_destination), tick, "reject", 0]
                simulationLogger.recordTransaction(transaction, [])
