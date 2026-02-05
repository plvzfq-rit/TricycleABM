from domain.Location import Location

from infrastructure import SimulationConfig
from infrastructure.TricycleRepository import TricycleRepository
from infrastructure.TodaRepository import TodaRepository
from infrastructure.PassengerFactory import PassengerFactory
from domain.TricycleState import TricycleState

import traci
import math
import random

class TricycleDispatcher:

    def __init__(self, tricycle_repository: TricycleRepository, passenger_factory: PassengerFactory, simulation_config: SimulationConfig) -> None:
        self.tricycleRepository = tricycle_repository
        self.passengerFactory = passenger_factory
        self.peakHourProbabilities = simulation_config.getPeakHourProbabilities()

    def tryDispatchFromTodaQueues(self, simulationLogger, tick, todaRepository: TodaRepository) -> None:
        curr_prob = self.peakHourProbabilities[math.floor(tick / 60 / 60)] / 60.0

        todaQueues = todaRepository.getAllToda()

        for toda in todaQueues:
            if not todaRepository.canTodaDispatch(toda):
                continue

            if random.random() >= curr_prob:
                continue

            # Peek at first tricycle without removing from queue
            tricycle_id = todaRepository.peekToda(toda)
            tricycle = self.tricycleRepository.getTricycle(tricycle_id)

            # Only proceed if tricycle is FREE (physically back in TODA and ready)
            if not tricycle.isFree():
                continue

            tricycle_location = self.tricycleRepository.getTricycleLocation(tricycle_id)
            passenger = self.passengerFactory.createRandomPassenger(traci.parkingarea.getLaneID(tricycle.hub).split("_")[0])

            if self.canDispatch(tricycle_id, tricycle_location, passenger.destination, tricycle.farthestDistance):
                success = self.tricycleRepository.dispatchTricycle(tricycle_id, passenger, simulationLogger, tick)
                if success:
                    # Only remove from queue on successful dispatch
                    todaRepository.dequeToda(toda)


    def canDispatch(self, tricycle_id: str, tricycle_location: Location, passenger_location: Location, tricycle_farthest_distance: float):
        try:
            estimated_distance = traci.simulation.getDistanceRoad(tricycle_location.edge, tricycle_location.position, passenger_location.edge, passenger_location.position)
        except Exception as e:
            print(e)
            print(str(tricycle_location), str(passenger_location))
            estimated_distance = float("inf")
        return self.tricycleRepository.isTricycleFree(tricycle_id) and estimated_distance <= tricycle_farthest_distance