from domain.Location import Location

from infrastructure.TricycleRepository import TricycleRepository
from infrastructure.PassengerRepository import PassengerRepository
from domain.TricycleState import TricycleState

class TricycleDispatcher:

    def __init__(self, tricycle_repository: TricycleRepository, passenger_repository: PassengerRepository):
        self.tricycleRepository = tricycle_repository
        self.passengerRepository = passenger_repository

    def dispatchTricycles(self, simulationLogger, tick) -> None:
        active_passenger_ids = self.passengerRepository.getActivePassengerIds()
        active_tricycles = self.tricycleRepository.getActiveFreeTricycleIds()

        for tricycle_id in active_tricycles:
            # just to be sure
            if self.tricycleRepository.getTricycle(tricycle_id).state != TricycleState.FREE:
                continue
            tricycle_location = self.tricycleRepository.getTricycleLocation(tricycle_id)
            for passenger_id in active_passenger_ids:
                passenger_location = self.passengerRepository.getPassengerLocation(passenger_id)
                if self.canDispatch(tricycle_id, passenger_id, tricycle_location, passenger_location):
                    self.passengerRepository.killPassenger(passenger_id)
                    passenger_destination = self.passengerRepository.getPassengerDestination(passenger_id)
                    ## TODO = change success into a dict object
                    success = self.tricycleRepository.dispatchTricycle(tricycle_id, passenger_destination, simulationLogger, tick)
                    ## negotiation part here??? 
                    if success:
                        # simulationLogger.add("run002", tricycle_id, "edge_010", "edge_200", 7.3, 14.80)
                        break

    def canDispatch(self, tricycle_id: str, passenger_id: str, tricycle_location: Location, passenger_location: Location):
        return passenger_location.isNear(tricycle_location) and self.tricycleRepository.isTricycleFree(tricycle_id) and self.passengerRepository.isPassengerAlive(passenger_id) and self.tricycleRepository.isTricycleParked(tricycle_id)