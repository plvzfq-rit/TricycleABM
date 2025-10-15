import traci
from domain.tricycle.TricycleState import TricycleState
from domain.location.Location import Location

class Tricycle:
    def __init__(self, name: str, hub: str, start_time: int, end_time: int, max_gas: float, gas_consumption_rate: float, gas_threshold: float) -> None:
        self.name = name
        self.hub = hub
        self.startTime = start_time
        self.endTime = end_time
        self.status = TricycleState.TO_SPAWN
        self.destination = None
        self.lastLocation = None
        self.maxGas = max_gas
        self.currentGas = max_gas
        self.gasConsumptionRate = gas_consumption_rate
        self.gasThreshold = gas_threshold

    def __str__(self) -> str:
        return f"Tricycle(name={self.name}, hub={self.hub}, start_time={self.startTime}, end_time={self.endTime})"
    
    def hasArrived(self) -> bool:
        current_edge = traci.vehicle.getRoadID(self.name)
        current_position = traci.vehicle.getLanePosition(self.name)
        current_location = Location(current_edge, current_position)
        return current_location.isNear(self.destination)
    
    def hasRunOutOfGas(self, distance_travelled: float) -> bool:
        print(self.name, distance_travelled, self.gasConsumptionRate, self.currentGas, distance_travelled / self.gasConsumptionRate)
        print(self.currentGas < (distance_travelled / self.gasConsumptionRate))
        return self.currentGas < (distance_travelled / self.gasConsumptionRate)
    
    def consumeGas(self, distance_travelled: float) -> bool:
        if self.hasRunOutOfGas(distance_travelled):
            return False
        self.currentGas -= distance_travelled / self.gasConsumptionRate
        return True
    
