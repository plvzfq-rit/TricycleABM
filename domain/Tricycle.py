import traci
from domain.TricycleState import TricycleState
from domain.Location import Location

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

    def __str__(self) -> str:
        return f"Tricycle(name={self.name}, hub={self.hub}, start_time={self.startTime}, end_time={self.endTime})"
    
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
        # current_edge = traci.vehicle.getRoadID(self.name)
        # current_position = traci.vehicle.getLanePosition(self.name)
        # current_location = Location(current_edge, current_position)
        return current_location.isNear(self.destination)
    
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
        return self.state == TricycleState.FREE or self.state == TricycleState.PARKED
    
    def hasPassenger(self) -> bool:
        return self.state == TricycleState.HAS_PASSENGER
    
    def isDroppingOff(self) -> bool:
        return self.state == TricycleState.DROPPING_OFF
    
    def isGoingToRefuel(self) -> bool:
        return self.state == TricycleState.GOING_TO_REFUEL
    
    def isRefuelling(self) -> bool:
        return self.state == TricycleState.REFUELLING
    
    def isReturningToToda(self) -> bool:
        return self.state == TricycleState.RETURNING_TO_TODA
    
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
        distance_travelled = current_location.distanceTo(self.lastLocation)

        answer = distance_travelled / 1000.0

        if self.hasRunOutOfGas(answer):
            return False
        self.currentGas -= answer / self.gasConsumptionRate
        return True
    
    def payForGas(self) -> None:
        self.money -= self.usualGasPayment