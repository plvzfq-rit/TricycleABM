from .TricycleRepository import TricycleRepository
from utils.TraciUtils import initializeTricycle, getTricycleLocation, returnTricycleToHub, getTricycleHubEdge, removeTricycle 
from .SimulationLogger import SimulationLogger
import traci

class TricycleStateManager:
    def __init__(self, tricycle_repository: TricycleRepository, simulation_logger: SimulationLogger):
        self.tricycleRepository = tricycle_repository
        self.simulationLogger = simulation_logger

    def updateTricycleStates(self, current_tick: int):
        for tricycle in self.tricycleRepository.getTricycles():
            if tricycle.isDead():
                continue
            self._advanceSingleTricycle(tricycle, current_tick)

    def _advanceSingleTricycle(self, tricycle, current_tick: int):
        tricycle_id = tricycle.getName()
        tricycle_hub = tricycle.getHub()

        if tricycle.shouldSpawn(current_tick):
            initializeTricycle(tricycle_id, tricycle_hub)
            tricycle.activate()
            tricycle.recordActualStart(current_tick)
            return
        elif not tricycle.hasSpawned():
            return

        tricycle.decrementCooldown()

        if not (tricycle.isFree() or tricycle.isRefuelling() or tricycle.isDead() or tricycle.isParked() or tricycle.isGoingToRefuel()):
            self.tricycleRepository.simulateGasConsumption(tricycle_id)

        current_location = getTricycleLocation(tricycle_id)
        if not current_location or current_location.isInvalid():
            return

        tricycle.setLastLocation(current_location)

        if tricycle.hasArrived(current_location):
            tricycle.dropOff()
            self.simulationLogger.add(*tricycle.currentLog)
            # Record trip stats for per-day tracking
            tricycle.recordTrip(tricycle.currentLog.distance, tricycle.currentLog.price)
            return

        if tricycle.isDroppingOff():
            returnTricycleToHub(tricycle_id, tricycle_hub)
            tricycle.returnToToda()
            return

        if current_location.edge == getTricycleHubEdge(tricycle_hub) and traci.vehicle.isStoppedParking(tricycle_id):
            tricycle.activate()
            return
        
        if tricycle.shouldDie(current_tick) and not tricycle.hasPassenger():
            removeTricycle(tricycle_id)
            tricycle.recordActualEnd(current_tick)
            tricycle.kill()
            return

        if tricycle.isGoingToRefuel() and not traci.vehicle.isStoppedParking(tricycle_id):
            self.tricycleRepository.rerouteToGasStation(tricycle_id)
            return
        if tricycle.isGoingToRefuel() and traci.vehicle.isStoppedParking(tricycle_id):
            gas_amt = self.tricycleRepository.refuelTricycle(tricycle_id)
            self.simulationLogger.addExpenseToLog(tricycle_id, "midday_gas", gas_amt, current_tick)
            tricycle.returnToToda()
            return
        if tricycle.currentGas <= 0:
            tricycle.goingToRefuel()
            traci.vehicle.setSpeed(tricycle_id, 1)
            return