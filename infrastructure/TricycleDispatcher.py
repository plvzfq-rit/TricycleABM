from domain.Location import Location

from infrastructure.TricycleRepository import TricycleRepository
from infrastructure.PassengerFactory import PassengerFactory
from domain.TricycleState import TricycleState

import traci
import math
import random

class TricycleDispatcher:

    def __init__(self, tricycle_repository: TricycleRepository, passenger_factory: PassengerFactory):
        self.tricycleRepository = tricycle_repository
        self.passengerFactory = passenger_factory

    def dispatchTricycles(self, simulationLogger, tick) -> None:
        # active_passenger_ids = self.passengerRepository.getActivePassengerIds()
        active_tricycles = self.tricycleRepository.getActiveFreeTricycleIds()
        peak_hour_prob = [0.08284023669,	0.1301775148,	0.1538461538,	0.1301775148,	0.08284023669,	0.07100591716,	0.04733727811,	0.0650887574,	0.03550295858,	0.02366863905,	0.02366863905,	0.04142011834,	0.02366863905,	0.01183431953,	0.005917159763,	0.005917159763,	0.005917159763, 0.005917159763]

        curr_prob = peak_hour_prob[math.floor(tick / 60 / 60)] / 60.0

        for tricycle_id in active_tricycles:

            if random.random() >= curr_prob:
                continue

            tricycle = self.tricycleRepository.getTricycle(tricycle_id)
            tricycle_location = self.tricycleRepository.getTricycleLocation(tricycle_id)
            passenger = self.passengerFactory.createRandomPassenger(traci.parkingarea.getLaneID(tricycle.hub).split("_")[0])
            # print("made")
            if self.canDispatch(tricycle_id, tricycle_location, passenger.destination, tricycle.farthestDistance):
                # print("trying to dispatch...")
                success = self.tricycleRepository.dispatchTricycle(tricycle_id, passenger, simulationLogger, tick)

    def canDispatch(self, tricycle_id: str, tricycle_location: Location, passenger_location: Location, tricycle_farthest_distance: float):
        try:
            estimated_distance = traci.simulation.getDistanceRoad(tricycle_location.edge, tricycle_location.position, passenger_location.edge, passenger_location.position)
        except Exception as e:
            print(e)
            print(str(tricycle_location), str(passenger_location))
            estimated_distance = float("inf")
        return self.tricycleRepository.isTricycleFree(tricycle_id) and estimated_distance <= tricycle_farthest_distance