from domain import Location, Tricycle
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

        # TRICYCLE SPAWNING LOGIC
        if self._handleSpawn(current_tick, tricycle):
            return
        elif not tricycle.hasSpawned():
            return
        
        # TRIYCLE COOLDOWN BEFORE ANOTHER PASSENGER
        tricycle.decrementCooldown()

        # SIMULATE GAS CONSUMPTION
        self._handleGasConsumption(tricycle)

        # LOCATION UPDATE
        if not self._handleLocationUpdate(tricycle):
            return
        current_location = tricycle.getLastLocation()

        # ARRIVAL AND DROPOFF
        if self._handleArrival(tricycle, current_location):
            return

        # POST-DROPOFF RETURN
        if self._handleDroppingOff(tricycle):
            return
        
        is_parked = traci.vehicle.isStoppedParking(tricycle.getName())

        # HUB ARRIVAL
        if self._handleHubArrival(tricycle, current_location, is_parked):
            return
        
        # DEATH
        if self._handleDeath(tricycle, current_tick):
            return

        # REFUELING LOGIC
        if self._handleRefueling(tricycle, current_tick, is_parked):
            return
        
        # OUT OF GAS HANDLING
        if self._handleOutOfGas(tricycle):
            return
        
    def _handleSpawn(self, current_tick: int, tricycle: Tricycle) -> bool:
        if tricycle.shouldSpawn(current_tick):
            initializeTricycle(tricycle.getName(), tricycle.getHub())
            tricycle.activate()
            tricycle.recordActualStart(current_tick)
            return True
        return False
    
    def _handleGasConsumption(self, tricycle: Tricycle) -> None:
        if not (
            tricycle.isFree() or 
            tricycle.isRefuelling() or 
            tricycle.isDead() or 
            tricycle.isParked() or 
            tricycle.isGoingToRefuel()
        ):
            self.tricycleRepository.simulateGasConsumption(tricycle.getName())

    def _handleLocationUpdate(self, tricycle: Tricycle) -> None:
        current_location = getTricycleLocation(tricycle.getName())
        if current_location and not current_location.isInvalid():
            tricycle.setLastLocation(current_location)
            return True
        return False
    
    def _handleArrival(self, tricycle: Tricycle, current_location: Location) -> bool:
        if tricycle.hasArrived(current_location):
            tricycle.dropOff()
            self.simulationLogger.add(*tricycle.currentLog)
            # Record trip stats for per-day tracking
            tricycle.recordTrip(tricycle.currentLog.distance, tricycle.currentLog.price)
            return True
        return False
    
    def _handleDroppingOff(self, tricycle: Tricycle) -> bool:
        if tricycle.isDroppingOff():
            returnTricycleToHub(tricycle.getName(), tricycle.getHub())
            tricycle.returnToToda()
            return True
        return False
    
    def _handleHubArrival(self, tricycle: Tricycle, current_location: Location, is_parked: bool) -> bool:
        if current_location.edge == getTricycleHubEdge(tricycle.getHub()) and is_parked:
            tricycle.activate()
            return True
        return False
    
    def _handleDeath(self, tricycle: Tricycle, current_tick: int) -> bool:
        if tricycle.shouldDie(current_tick) and not tricycle.hasPassenger():
            removeTricycle(tricycle.getName())
            tricycle.recordActualEnd(current_tick)
            tricycle.kill()
            return True
        return False

    def _handleRefueling(self, tricycle: Tricycle, current_tick: int, is_parked: bool) -> bool:
        if tricycle.isGoingToRefuel():
            if not is_parked:
                self.tricycleRepository.rerouteToGasStation(tricycle.getName())
                return True
            if is_parked:
                gas_amt = self.tricycleRepository.refuelTricycle(tricycle.getName())
                self.simulationLogger.addExpenseToLog(tricycle.getName(), "midday_gas", gas_amt, current_tick)
                tricycle.returnToToda()
                return True
        return False
    
    def _handleOutOfGas(self, tricycle: Tricycle) -> bool:
        if tricycle.currentGas <= 0:
            tricycle.goingToRefuel()
            traci.vehicle.setSpeed(tricycle.getName(), 1)
            return True
        return False