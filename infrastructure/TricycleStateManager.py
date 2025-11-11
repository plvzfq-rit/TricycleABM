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
                self.tricycleRepository.simulateGasConsumption(tricycle_id)
                self.traciService.returnTricycleToHub(tricycle_id, tricycle_hub)
                tricycle.returnToToda()
                continue
            elif tricycle.shouldDie(current_tick):
                self.traciService.removeTricycle(tricycle_id)
                tricycle.kill()
                continue
            if not (tricycle.isFree() or tricycle.isRefuelling() or tricycle.isDead() or tricycle.hasSpawned() or tricycle.isParked() or tricycle.isGoingToRefuel()):
                self.tricycleRepository.simulateGasConsumption(tricycle_id)
                continue
            if tricycle.isGoingToRefuel() and not traci.vehicle.isStoppedParking(tricycle_id):
                self.tricycleRepository.rerouteToGasStation(tricycle_id)
                continue
            elif tricycle.isGoingToRefuel() and traci.vehicle.isStoppedParking(tricycle_id):
                self.tricycleRepository.refuelTricycle(tricycle_id)
                tricycle.returnToToda()
                continue
            if tricycle.currentGas <= 0:
                tricycle.goingToRefuel()
                traci.vehicle.setSpeed(tricycle_id, 1.34112)
                continue
            else:
                # self.tricycleRepository.updateTricycleLocation(tricycle_id, current_location)
                tricycle.setLastLocation(current_location)
                continue
