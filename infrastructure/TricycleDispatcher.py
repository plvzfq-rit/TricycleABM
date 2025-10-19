from domain.Location import Location

from infrastructure.TricycleRepository import TricycleRepository
from infrastructure.PassengerRepository import PassengerRepository

class TricycleDispatcher:

    def __init__(self, tricycle_repository: TricycleRepository, passenger_repository: PassengerRepository):
        self.tricycleRepository = tricycle_repository
        self.passengerRepository = passenger_repository

    def dispatchTricycles(self) -> None:
        active_passenger_ids = self.passengerRepository.getActivePassengerIds()

        for passenger_id in active_passenger_ids:
            passenger_location = self.passengerRepository.getPassengerLocation(passenger_id)
            active_tricycles = self.tricycleRepository.getActiveFreeTricycleIds()
            for tricycle_id in active_tricycles:
                tricycle_location = self.tricycleRepository.getTricycleLocation(tricycle_id)

                if self.canDispatch(tricycle_id, passenger_id, tricycle_location, passenger_location):
                    self.passengerRepository.killPassenger(passenger_id)
                    passenger_destination = self.passengerRepository.getPassengerDestination(passenger_id)
                    success = self.tricycleRepository.dispatchTricycle(tricycle_id, passenger_destination)
                    if success:
                        break

    def canDispatch(self, tricycle_id: str, passenger_id: str, tricycle_location: Location, passenger_location: Location):
        return passenger_location.isNear(tricycle_location) and self.tricycleRepository.isTricycleFree(tricycle_id) and self.passengerRepository.isPassengerAlive(passenger_id)