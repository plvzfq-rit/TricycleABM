"""Module representing tricycle drivers in the simulation.

This module defines the Tricycle class which represents a tricycle vehicle
and driver in the simulation, including state management, financial tracking,
and trip logging.
"""

import traci
import math
import random
from domain.TricycleState import TricycleState
from domain.Location import Location, getManhattanDistance
from collections import namedtuple

from utils.TraciUtils import getTricycleLocation


class Tricycle:
    """Represents a tricycle vehicle and driver.
    
    Manages the tricycle's state, location, finances, and trip records.
    Tracks daily and cumulative statistics including trips, income, and distance.
    """

    def __init__(self, name: str, hub: str, start_time: int, end_time: int, max_gas: float, gas_consumption_rate: float, usualGasPayment: float, getsAFullTank: bool, farthestDistance: float, dailyExpense: float, patience: float, aspiredPrice: float, minimumPrice: float) -> None:
        """Initialize a tricycle with operational and financial parameters.
        
        :param name: Unique identifier for the tricycle.
        :type name: str
        :param hub: ID of the TODA hub where the tricycle is stationed.
        :type hub: str
        :param start_time: Simulation time when tricycle enters service (in seconds).
        :type start_time: int
        :param end_time: Simulation time when tricycle leaves service (in seconds).
        :type end_time: int
        :param max_gas: Maximum gas capacity in liters.
        :type max_gas: float
        :param gas_consumption_rate: Fuel consumption rate (liters per meter).
        :type gas_consumption_rate: float
        :param usualGasPayment: Typical payment for a full tank.
        :type usualGasPayment: float
        :param getsAFullTank: Whether this driver fuels up completely each day.
        :type getsAFullTank: bool
        :param farthestDistance: Maximum distance willing to travel per trip (meters).
        :type farthestDistance: float
        :param dailyExpense: Daily fixed expense for operating the tricycle.
        :type dailyExpense: float
        :param patience: Driver's patience level for negotiation.
        :type patience: float
        :param aspiredPrice: Driver's desired price per kilometer.
        :type aspiredPrice: float
        :param minimumPrice: Minimum price the driver will accept.
        :type minimumPrice: float
        """
        self.name = name
        self.hub = hub
        self.startTime = start_time
        self.endTime = end_time
        self.state = TricycleState.TO_SPAWN
        self.destination = None
        self.lastLocation = None
        self.gasConsumptionRate = gas_consumption_rate
        self.dailyExpense = dailyExpense
        self.farthestDistance = farthestDistance
        self.log = namedtuple("log", ["run_id","trike_id","origin_edge", "dest_edge", "distance", "price","tick", "driver_asp", "passenger_asp", "base_price", "init_driver_asp", "init_passenger_asp"])
        self.currentLog = None
        self.cooldownTime = 0
        self.patience = patience
        self.aspiredPrice = aspiredPrice
        self.minimumPrice = minimumPrice
        # Track actual time spent in simulation
        self.actualStartTick = None
        self.actualEndTick = None
        # Per-day statistics
        self.dailyTrips = 0
        self.dailyIncome = 0.0
        self.dailyFixedIncome = 0.0
        self.dailyDistance = 0.0

    def __str__(self) -> str:
        """Return a string representation of the tricycle.
        
        :return: String showing tricycle name and current state.
        :rtype: str
        """
        return f"Tricycle(name={self.name}, state={self.state})"

    def getPatience(self) -> float:
        """Get the driver's patience level.
        
        :return: Driver's patience level as a float.
        :rtype: float
        """
        return self.patience
    
    def getAspiredPrice(self) -> float:
        """Get the driver's aspired price per kilometer.
        
        :return: Aspired price per kilometer as a float.
        :rtype: float
        """
        return self.aspiredPrice
    
    def recordLog(self, run_id: str, trike_id: str, origin_edge: str, dest_edge: str, 
                  distance: str, price: str, tick: str, driver_asp: str, 
                  passenger_asp: str, base_price: str, init_driver_asp: str, 
                  init_passenger_asp: str) -> None:
        """Record a completed trip with all relevant transaction details.
        
        :param run_id: Simulation run identifier.
        :type run_id: str
        :param trike_id: Tricycle identifier.
        :type trike_id: str
        :param origin_edge: Starting edge ID.
        :type origin_edge: str
        :param dest_edge: Destination edge ID.
        :type dest_edge: str
        :param distance: Distance traveled (in meters).
        :type distance: str
        :param price: Final price charged.
        :type price: str
        :param tick: Simulation tick when trip occurred.
        :type tick: str
        :param driver_asp: Driver's aspired price.
        :type driver_asp: str
        :param passenger_asp: Passenger's aspired price.
        :type passenger_asp: str
        :param base_price: Base price for the fare.
        :type base_price: str
        :param init_driver_asp: Initial driver aspired price.
        :type init_driver_asp: str
        :param init_passenger_asp: Initial passenger aspired price.
        :type init_passenger_asp: str
        """
        self.currentLog = self.log(run_id, trike_id, origin_edge, dest_edge, distance, 
                                    price, tick, driver_asp, passenger_asp, base_price, 
                                    init_driver_asp, init_passenger_asp)
    
    def activate(self) -> None:
        """Set tricycle to FREE state, ready to accept passengers."""
        self.state = TricycleState.FREE

    def kill(self) -> None:
        """Mark the tricycle as DEAD and remove from active simulation."""
        self.state = TricycleState.DEAD

    def acceptPassenger(self, destination: Location) -> None:
        """Accept a passenger and set the tricycle's destination.
        
        :param destination: Location object for the passenger's destination.
        :type destination: Location
        :raises Exception: If destination is None.
        """
        if not destination:
            raise Exception(f"destination given to {self.name} was None")
        self.state = TricycleState.HAS_PASSENGER
        self.destination = destination

    def hasArrived(self, current_location: Location) -> bool:
        """Check if tricycle has reached the trip destination.
        
        :param current_location: Current location of the tricycle.
        :type current_location: Location
        :return: True if tricycle is near the destination, False otherwise.
        :rtype: bool
        """
        return current_location.isNear(self.destination)
    
    def decrementCooldown(self) -> None:
        """Decrement the cooldown counter by one tick."""
        self.cooldownTime = max(self.cooldownTime - 1, 0)
    
    def dropOff(self) -> None:
        """Mark tricycle as dropping off the passenger."""
        self.destination = None
        self.state = TricycleState.DROPPING_OFF

    def returnToToda(self) -> None:
        """Set tricycle state to returning to the TODA hub."""
        self.destination = None
        self.state = TricycleState.RETURNING_TO_TODA

    def isFree(self) -> bool:
        """Check if the tricycle is free and available for dispatch.
        
        :return: True if state is FREE, False otherwise.
        :rtype: bool
        """
        return self.state == TricycleState.FREE
    
    def hasPassenger(self) -> bool:
        """Check if the tricycle currently has a passenger.
        
        :return: True if state is HAS_PASSENGER, False otherwise.
        :rtype: bool
        """
        return self.state == TricycleState.HAS_PASSENGER
    
    def isDroppingOff(self) -> bool:
        """Check if the tricycle is currently dropping off a passenger.
        
        :return: True if state is DROPPING_OFF, False otherwise.
        :rtype: bool
        """
        return self.state == TricycleState.DROPPING_OFF
    
    def isDead(self) -> bool:
        """Check if the tricycle is dead and inactive.
        
        :return: True if state is DEAD, False otherwise.
        :rtype: bool
        """
        return self.state == TricycleState.DEAD
    
    def hasSpawned(self) -> bool:
        """Check if the tricycle has spawned into the simulation.
        
        :return: True if state is not TO_SPAWN, False otherwise.
        :rtype: bool
        """
        return self.state != TricycleState.TO_SPAWN
    
    def shouldDie(self, time: int) -> bool:
        """Check if it is time for the tricycle to leave the simulation.
        
        :param time: Current simulation tick.
        :type time: int
        :return: True if current tick matches end tick and state of tricycle is not dead.
        :rtype: bool
        """
        return self.endTime == time and self.state != TricycleState.DEAD
    
    def setDestination(self, destination: Location) -> None:
        """Set the tricycle's destination.
        
        :param destination: Location object for the destination.
        :type destination: Location
        """
        self.destination = destination

    def shouldSpawn(self, time: int) -> bool:
        """Check if it is time for the tricycle to spawn into the simulation.
        
        :param time: Current simulation tick.
        :type time: int
        :return: True if current time matches start time and tricycle is not yet spawned.
        :rtype: bool
        """
        return self.startTime == time and self.state == TricycleState.TO_SPAWN

    def getHub(self) -> str:
        """Get the TODA where this tricycle is stationed.
        
        :return: TODA Hub string.
        :rtype: str
        """
        return self.hub
    
    def getName(self) -> str:
        """Get the tricycle ID.
        
        :return: Tricycle ID in str.
        :rtype: str
        """
        return self.name
    
    def getLastLocation(self) -> Location:
        """Get the most recent recorded location of the tricycle.
        
        :return: Location object or None if unset.
        :rtype: Location
        """
        return self.lastLocation

    def setLastLocation(self, last_location: Location) -> None:
        """Set the tricycle's current location.
        
        :param last_location: Location object representing the tricycle's position.
        :type last_location: Location
        """
        self.lastLocation = last_location

    def recordActualStart(self, tick: int) -> None:
        """Record the simulation tick when the tricycle actually spawned.
        
        :param tick: Simulation time in ticks.
        :type tick: int
        """
        self.actualStartTick = tick

    def recordActualEnd(self, tick: int) -> None:
        """Record the simulation tick when the tricycle left the simulation.
        
        :param tick: Simulation time in ticks.
        :type tick: int
        """
        self.actualEndTick = tick

    def getActualDuration(self) -> int:
        """Get the actual time spent in the simulation.
        
        :return: Duration in ticks, or 0 if not yet set.
        :rtype: int
        """
        if self.actualStartTick is None or self.actualEndTick is None:
            return 0
        return self.actualEndTick - self.actualStartTick

    def recordTrip(self, distance: float, price: float, base_price: float) -> None:
        """Record a completed trip for daily statistics.
        
        :param distance: Distance traveled (in meters).
        :type distance: float
        :param price: Total fare charged.
        :type price: float
        :param base_price: Base fare component.
        :type base_price: float
        """
        self.dailyTrips += 1
        self.dailyIncome += float(price)
        self.dailyFixedIncome += float(base_price)
        self.dailyDistance += float(distance)

    def resetDailyStats(self) -> None:
        """Resets all daily statistics. Prerequisite before a new run starts."""
        self.dailyTrips = 0
        self.dailyIncome = 0.0
        self.dailyFixedIncome = 0.0
        self.dailyDistance = 0.0
        self.actualStartTick = None
        self.actualEndTick = None
        self.state = TricycleState.TO_SPAWN
        self.destination = None
        self.lastLocation = None
        self.cooldownTime = 0

    def getDailyStats(self) -> dict:
        """Get the daily statistics for this tricycle.
        
        :return: Dictionary with keys: trips, income, fixed_income, distance, actual_duration.
        :rtype: dict
        """
        return {
            'trips': self.dailyTrips,
            'income': self.dailyIncome,
            'fixed_income': self.dailyFixedIncome,
            'distance': self.dailyDistance,
            'actual_duration': self.getActualDuration()
        }
    
    def canAcceptDispatch(self, passenger_destination: Location) -> bool:
        """Check if the tricycle can accept a dispatch to the given destination.
        
        :param passenger_destination: Destination Location for the potential passenger.
        :type passenger_destination: Location
        :return: True if tricycle is free and able to accept, False otherwise.
        :rtype: bool
        """
        return self.isFree()