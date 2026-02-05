import traci
import math
import random
from domain.TricycleState import TricycleState
from domain.Location import Location, getManhattanDistance
from collections import namedtuple

class Tricycle:
    def __init__(self, name: str, hub: str, start_time: int, end_time: int, max_gas: float, gas_consumption_rate: float, gas_threshold: float, usualGasPayment: float, getsAFullTank: bool, farthestDistance: float, dailyExpense: float) -> None:
        self.name = name
        self.hub = hub
        self.startTime = start_time
        self.endTime = end_time
        self.state = TricycleState.TO_SPAWN
        self.destination = None
        self.lastLocation = None
        self.maxGas = max_gas
        self.currentGas = max_gas
        self.gasConsumptionRate = gas_consumption_rate
        self.gasThreshold = gas_threshold
        self.money = 0
        self.usualGasPayment = usualGasPayment
        self.getsAFullTank = getsAFullTank
        self.dailyExpense = dailyExpense
        self.farthestDistance = farthestDistance
        self.log = namedtuple("log", ["run_id","trike_id","origin_edge", "dest_edge", "distance", "price","tick"])
        self.currentLog = None
        self.cooldownTime = 0
        # Track actual time spent in simulation
        self.actualStartTick = None
        self.actualEndTick = None
        # Per-day statistics
        self.dailyTrips = 0
        self.dailyIncome = 0.0
        self.dailyDistance = 0.0

    def __str__(self) -> str:
        return f"Tricycle(name={self.name}, state={self.state})"
    
    def recordLog(self, run_id:str, trike_id: str, origin_edge: str, dest_edge:str, distance:str, price:str, tick:str) -> None:
        self.currentLog = self.log(run_id, trike_id, origin_edge, dest_edge, distance, price, tick)
    
    def activate(self) -> None:
        self.state = TricycleState.FREE

    def kill(self) -> None:
        self.state = TricycleState.DEAD

    def acceptPassenger(self, destination: Location) -> None:
        if not destination:
            raise Exception(f"destination given to {self.name} was None")
        self.state = TricycleState.HAS_PASSENGER
        self.destination = destination

    def hasArrived(self, current_location: Location) -> bool:
        self.cooldownTime = math.ceil(-600 * math.log(random.random()))
        return current_location.isNear(self.destination)
    
    def isInCooldown(self):
        return self.cooldownTime == 0
    
    def decrementCooldown(self):
        self.cooldownTime = max(self.cooldownTime - 1, 0)
    
    def dropOff(self):
        self.destination = None
        self.state = TricycleState.DROPPING_OFF

    def goingToRefuel(self):
        self.state = TricycleState.GOING_TO_REFUEL
        return 

    def returnToToda(self):
        self.destination = None
        self.state = TricycleState.RETURNING_TO_TODA

    def isActive(self):
        return self.state not in [TricycleState.DEAD, TricycleState.TO_SPAWN]
    
    def hasRunOutOfGas(self, distance_travelled: float) -> bool:
        return self.currentGas < (distance_travelled / self.gasConsumptionRate)
    
    def isFree(self) -> bool:
        return self.state == TricycleState.FREE
    
    def hasPassenger(self) -> bool:
        return self.state == TricycleState.HAS_PASSENGER
    
    def isDroppingOff(self) -> bool:
        return self.state == TricycleState.DROPPING_OFF
    
    def isGoingToRefuel(self) -> bool:
        return self.state == TricycleState.GOING_TO_REFUEL
    
    def isRefuelling(self) -> bool:
        return self.state == TricycleState.REFUELLING
    
    def isDead(self) -> bool:
        return self.state == TricycleState.DEAD
    
    def hasSpawned(self) -> bool:
        return self.state != TricycleState.TO_SPAWN
    
    def isParked(self) -> bool:
        return self.state == TricycleState.PARKED
    
    def shouldDie(self, time: int) -> bool:
        return self.endTime < time
    
    def setDestination(self, destination: Location) -> None:
        self.destination = destination

    def shouldSpawn(self, time: int) -> bool:
        return self.startTime == time and self.state == TricycleState.TO_SPAWN

    def shouldDie(self, time: int) -> bool:
        return self.endTime == time and self.state != TricycleState.DEAD
    
    def shouldReturnToToda(self, current_location) -> bool:
        return self.hasArrived(current_location) and self.state == TricycleState.HAS_PASSENGER
    
    def getHub(self) -> str:
        return self.hub
    
    def getName(self) -> str:
        return self.name
    
    def park(self, current_location: Location) -> None:
        self.state = TricycleState.PARKED
        self.lastLocation = current_location

    def setLastLocation(self, last_location: Location) -> None:
        self.lastLocation = last_location

    #METHOD FOR GAS CONSUMPTION
    def consumeGas(self, current_location: Location) -> bool:
        try:
            distance_travelled = getManhattanDistance(current_location, self.lastLocation)
        except:
            distance_travelled = 0
            
        answer = distance_travelled / 1000.0
        # print(answer)
        if self.hasRunOutOfGas(answer):
            return False
        self.currentGas -= answer / self.gasConsumptionRate
        return True
    
    def payForGas(self) -> float:
        self.money -= self.usualGasPayment
        return self.usualGasPayment

    def recordActualStart(self, tick: int) -> None:
        """Record when the tricycle actually spawned into the simulation"""
        self.actualStartTick = tick

    def recordActualEnd(self, tick: int) -> None:
        """Record when the tricycle actually left the simulation"""
        self.actualEndTick = tick

    def getActualDuration(self) -> int:
        """Get the actual time spent in the simulation (in ticks/seconds)"""
        if self.actualStartTick is None or self.actualEndTick is None:
            return 0
        return self.actualEndTick - self.actualStartTick

    def recordTrip(self, distance, price) -> None:
        """Record a completed trip for daily statistics"""
        self.dailyTrips += 1
        self.dailyIncome += float(price)
        self.dailyDistance += float(distance)

    def getDailyStats(self) -> dict:
        """Get the daily statistics for this tricycle"""
        return {
            'trips': self.dailyTrips,
            'income': self.dailyIncome,
            'distance': self.dailyDistance,
            'actual_duration': self.getActualDuration()
        }