import random
from domain.Tricycle import Tricycle

class TricycleFactory:
    lowerGasBound = 50.0
    upperGasBound = 52.0

    def __init__(self, lower_gas_bound: float = 50.0, upper_gas_bound: float = 52.0):
        self.lowerGasBound = lower_gas_bound
        self.upperGasBound = upper_gas_bound

    def createRandomTricycle(self, assigned_id: int, simulation_duration: int, assigned_hub: str) -> tuple[str, Tricycle]:
        trike_name = "trike" + str(assigned_id)
        #start_time = random.randint(0, simulation_duration // 2)
        #end_time = random.randint(start_time, simulation_duration)
        start_time = 0
        end_time = simulation_duration
        max_gas = self.lowerGasBound + (self.upperGasBound - self.lowerGasBound) * random.random()
        gas_consumption = random.random()
        gas_threshold = max_gas * random.random()
        return (trike_name, Tricycle(trike_name, assigned_hub, start_time, end_time, max_gas, gas_consumption, gas_threshold))