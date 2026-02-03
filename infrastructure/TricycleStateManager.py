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

            tricycle_id = tricycle.getName()
            tricycle_hub = tricycle.getHub()

            if tricycle.shouldSpawn(current_tick):
                initializeTricycle(tricycle_id, tricycle_hub)
                tricycle.activate()
                tricycle.recordActualStart(current_tick)
                continue
            elif not tricycle.hasSpawned():
                continue

            # if tricycle.hasSpawned() and not (tricycle.isFree() or tricycle.isRefuelling() or tricycle.isDead() or tricycle.isParked() or tricycle.isGoingToRefuel()):
            #     self.tricycleRepository.simulateGasConsumption(tricycle_id)

            tricycle.decrementCooldown()

            if not (tricycle.isFree() or tricycle.isRefuelling() or tricycle.isDead() or tricycle.isParked() or tricycle.isGoingToRefuel()):
                self.tricycleRepository.simulateGasConsumption(tricycle_id)

            current_location = getTricycleLocation(tricycle_id)
            if not current_location or current_location.isInvalid():
                continue

            tricycle.setLastLocation(current_location)

            if tricycle.hasArrived(current_location):
                tricycle.dropOff()
                self.simulationLogger.add(*tricycle.currentLog)
                # Record trip stats for per-day tracking
                tricycle.recordTrip(tricycle.currentLog.distance, tricycle.currentLog.price)
                continue

            if tricycle.isDroppingOff():
                returnTricycleToHub(tricycle_id, tricycle_hub)
                tricycle.returnToToda()
                continue

            if current_location.edge == getTricycleHubEdge(tricycle_hub) and traci.vehicle.isStoppedParking(tricycle_id):
                tricycle.activate()
                continue
            
            if tricycle.shouldDie(current_tick) and not tricycle.hasPassenger():
                removeTricycle(tricycle_id)
                tricycle.recordActualEnd(current_tick)
                tricycle.kill()
                continue

            if tricycle.isGoingToRefuel() and not traci.vehicle.isStoppedParking(tricycle_id):
                self.tricycleRepository.rerouteToGasStation(tricycle_id)
                continue
            if tricycle.isGoingToRefuel() and traci.vehicle.isStoppedParking(tricycle_id):
                gas_amt = self.tricycleRepository.refuelTricycle(tricycle_id)
                self.simulationLogger.addExpenseToLog(tricycle_id, "midday_gas", gas_amt, current_tick)
                tricycle.returnToToda()
                continue
            if tricycle.currentGas <= 0:
                tricycle.goingToRefuel()
                traci.vehicle.setSpeed(tricycle_id, 1)
                continue