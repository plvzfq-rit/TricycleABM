from infrastructure.TricycleRepository import TricycleRepository
from infrastructure.TraciService import TraciService
import traci

class TricycleStateManager:
    def __init__(self, tricycle_repository: TricycleRepository, traci_service: TraciService):
        self.tricycleRepository = tricycle_repository
        self.traciService = traci_service

    def updateTricycleStates(self, current_tick: int):
        for tricycle in self.tricycleRepository.getTricycles():
            if tricycle.isDead():
                continue

            tricycle_id = tricycle.getName()
            tricycle_hub = tricycle.getHub()

            if tricycle.shouldSpawn(current_tick):
                self.traciService.initializeTricycle(tricycle_id, tricycle_hub)
                tricycle.activate()
                continue
            elif not tricycle.hasSpawned():
                continue

            current_location = self.traciService.getTricycleLocation(tricycle_id)
            if not current_location:
                tricycle.kill()
                continue
            if current_location.isInvalid():
                tricycle.park(current_location)
                continue
            
            if tricycle.isReturningToToda() and self.traciService.checkIfTricycleParked(tricycle_id, tricycle_hub):
                tricycle.activate()
                continue
            
            if tricycle.shouldReturnToToda(current_location):
                self.traciService.returnTricycleToHub(tricycle_id, tricycle_hub)
                tricycle.returnToToda()
                continue
            elif tricycle.shouldDie(current_tick):
                self.traciService.removeTricycle(tricycle_id)
                tricycle.kill()
                continue
            else:
                # self.tricycleRepository.updateTricycleLocation(tricycle_id, current_location)
                tricycle.setLastLocation(current_location)
                continue