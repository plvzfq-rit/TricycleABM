import random
from domain.Tricycle import Tricycle

class TricycleFactory:
    LOWER_MAX_GAS = 50.0
    UPPER_MAX_GAS = 52.0

    def createRandomTricycle(self, assigned_id: int, simulation_duration: int, assigned_hub: str) -> tuple[str, Tricycle]:
        trike_name = "trike" + str(assigned_id)
        start_time = random.randint(0, simulation_duration // 2)
        end_time = random.randint(start_time, simulation_duration)
        max_gas = self.LOWER_MAX_GAS + (self.UPPER_MAX_GAS - self.LOWER_MAX_GAS) * random.random()
        gas_consumption = random.random()
        gas_threshold = max_gas * random.random()
        return (trike_name, Tricycle(trike_name, assigned_hub, start_time, end_time, max_gas, gas_consumption, gas_threshold))