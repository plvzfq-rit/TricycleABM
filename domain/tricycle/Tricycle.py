import traci
from domain.tricycle.TricycleState import TricycleState
from domain.location.Location import Location

class Tricycle:
    def __init__(self, name: str, hub: str, start_time: int, end_time: int, max_gas: float, gas_consumption_rate: float, gas_threshold: float) -> None:
        self.name = name
        self.hub = hub
        self.startTime = start_time
        self.endTime = end_time
        self.status = TricycleState.FREE
        self.destination = None
        self.maxGas = max_gas
        self.gasConsumptionRate = gas_consumption_rate
        self.gasThreshold = gas_threshold

    def __str__(self) -> str:
        return f"Tricycle(name={self.name}, hub={self.hub}, start_time={self.startTime}, end_time={self.endTime})"
    
    def hasArrived(self) -> bool:
        current_edge = traci.vehicle.getRoadID(self.name)
        current_position = traci.vehicle.getLanePosition(self.name)
        current_location = Location(current_edge, current_position)
        return current_location.isNear(self.destination)