"""Module for managing tricycle state transitions during simulation.

Provides the TricycleStateManager class which handles state updates of
tricycles based on simulation events.
"""

from domain import Location, Tricycle
from .TricycleRepository import TricycleRepository
from utils.TraciUtils import (initializeTricycle, getTricycleLocation, 
                              returnTricycleToHub, getTricycleHubEdge, 
                              removeTricycle, hasTricycleParked)
from .SimulationLogger import SimulationLogger


class TricycleStateManager:
    """Manages state transitions and updates for tricycle objects.
    
    Handles all state changes for tricycles including spawning into the
    simulation, location updates, passenger pickup/dropoff, and removal.
    
    :ivar tricycleRepository: Repository of tricycle objects.
    :ivar simulationLogger: Logger for recording events.
    """
    
    def __init__(self, tricycle_repository: TricycleRepository, 
                 simulation_logger: SimulationLogger) -> None:
        """Initialize the state manager.
        
        :param tricycle_repository: Repository of all tricycles.
        :type tricycle_repository: TricycleRepository
        :param simulation_logger: Logger for recording data.
        :type simulation_logger: SimulationLogger
        """
        self.tricycleRepository = tricycle_repository
        self.simulationLogger = simulation_logger

    def updateTricycleStates(self, current_tick: int) -> None:
        """Update the state of all tricycles in the repository.
        
        Iterates through all tricycles and advances their state based on
        current simulation conditions. Entry point from main loop.
        
        :param current_tick: Current simulation tick.
        :type current_tick: int
        """
        for tricycle in self.tricycleRepository.getTricycles():
            if tricycle.isDead():
                continue
            self._advanceSingleTricycle(tricycle, current_tick)

    def _advanceSingleTricycle(self, tricycle: Tricycle, current_tick: int) -> None:
        """Helper for updateTricycleStates. Advance a single tricycle's state
        through the event sequence.
        
        :param tricycle: Tricycle object to update.
        :type tricycle: Tricycle
        :param current_tick: Current simuation tick
        :type current_tick: int
        """
        # TRICYCLE SPAWNING LOGIC
        if self._handleSpawn(current_tick, tricycle):
            return
        elif not tricycle.hasSpawned():
            return
        
        # TRICYCLE COOLDOWN BEFORE ANOTHER PASSENGER
        tricycle.decrementCooldown()

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
        
        is_parked = hasTricycleParked(tricycle.getName())

        # HUB ARRIVAL
        if self._handleHubArrival(tricycle, current_location, is_parked):
            return
        
        # DEATH
        if self._handleDeath(tricycle, current_tick):
            return

    def _handleSpawn(self, current_tick: int, tricycle: Tricycle) -> bool:
        """Initializes tricycles spawning into the simulation.
        
        :param current_tick: Current simulation tick
        :type current_tick: int
        :param tricycle: Tricycle to spawn.
        :type tricycle: Tricycle
        :return: True if tricycle was spawned, False otherwise.
        :rtype: bool
        """
        if tricycle.shouldSpawn(current_tick): # Tricycle object contains start_time
            initializeTricycle(tricycle.getName(), tricycle.getHub())
            tricycle.activate()
            tricycle.recordActualStart(current_tick)
            return True
        return False
    
    def _handleLocationUpdate(self, tricycle: Tricycle) -> bool:
        """Update the recorded location of a tricycle.
        
        :param tricycle: Tricycle to update.
        :type tricycle: Tricycle
        :return: True if location was successfully updated, False otherwise.
        :rtype: bool
        """
        current_location = getTricycleLocation(tricycle.getName())
        if current_location and not current_location.isInvalid():
            tricycle.setLastLocation(current_location)
            return True
        return False
    
    def _handleArrival(self, tricycle: Tricycle, current_location: Location) -> bool:
        """Log transaction data after tricycle arrives at passenger destination.
        
        :param tricycle: Tricycle that may have arrived.
        :type tricycle: Tricycle
        :param current_location: Current location of the tricycle.
        :type current_location: Location
        :return: True if tricycle arrived, False otherwise.
        :rtype: bool
        """
        if tricycle.hasArrived(current_location):
            tricycle.dropOff()
            self.simulationLogger.add(*tricycle.currentLog)
            # Record trip stats for per-day tracking
            tricycle.recordTrip(tricycle.currentLog.distance, tricycle.currentLog.price, tricycle.currentLog.base_price)
            return True
        return False
    
    def _handleDroppingOff(self, tricycle: Tricycle) -> bool:
        """After passenger drop-off, route tricycles to return to respective 
        TODA hub spawn.
        
        :param tricycle: Tricycle that may be dropping off.
        :type tricycle: Tricycle
        :return: True if tricycle is in dropoff state, False otherwise.
        :rtype: bool
        """
        if tricycle.isDroppingOff():
            returnTricycleToHub(tricycle.getName(), tricycle.getHub())
            tricycle.returnToToda()
            return True
        return False
    
    def _handleHubArrival(self, tricycle: Tricycle, current_location: Location, 
                         is_parked: bool) -> bool:
        """Upon arrival to TODA hub, TricycleState of tricycle is set ACTIVE.
        
        :param tricycle: Tricycle that may have arrived at hub.
        :type tricycle: Tricycle
        :param current_location: Current location.
        :type current_location: Location
        :param is_parked: Whether the tricycle is parked.
        :type is_parked: bool
        :return: True if tricycle arrived at hub, False otherwise.
        :rtype: bool
        """
        if current_location.edge == getTricycleHubEdge(tricycle.getHub()) and is_parked:
            tricycle.activate()
            return True
        return False
    
    def _handleDeath(self, tricycle: Tricycle, current_tick: int) -> bool:
        """Handle tricycle removal from simulation at end-of-shift.
        (tricycle has end_time)
        
        :param tricycle: Tricycle to potentially remove 
        :type tricycle: Tricycle
        :param current_tick: Current simulation tick.
        :type current_tick: int
        :return: True if tricycle was removed, False otherwise.
        :rtype: bool
        """
        if tricycle.shouldDie(current_tick) and not tricycle.hasPassenger():
            removeTricycle(tricycle.getName())
            tricycle.recordActualEnd(current_tick)
            tricycle.kill()
            return True
        return False