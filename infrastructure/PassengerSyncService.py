from infrastructure.PassengerRepository import PassengerRepository
from infrastructure.TraciService import TraciService

class PassengerSyncService:
    def __init__(self, passenger_repository: PassengerRepository | None = None, traci_service: TraciService | None = None):
        self.passengerRepository = passenger_repository
        self.traciService = traci_service
    
    def sync(self):
        current_passengers = set(self.traciService.getPassengerIds())
        passengers_in_memory = set(self.passengerRepository.getActivePassengerIds())
        passengers_to_kill = passengers_in_memory - current_passengers
        for passenger_id in passengers_to_kill:
            self.passengerRepository.killPassenger(passenger_id)