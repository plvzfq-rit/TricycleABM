import random

class Tricycle:
    def __init__(self, name: str, hub: str, start_time: int, end_time: int) -> None:
        self.name = name
        self.hub = hub
        self.startTime = start_time
        self.endTime = end_time

    def __str__(self) -> str:
        return f"Tricycle(name={self.name}, hub={self.hub}, start_time={self.startTime}, end_time={self.endTime})"

class TricycleGenerator:
    def __init__(self):
        self.spawnedTricycles = set()

    def generateTricycles(self, number_of_tricycles: int, simulation_duration: int, hub_distribution: dict) -> None:
        hubs = []
        for hub, number_of_tricycles_in_hub in hub_distribution.items():
            for i in range(number_of_tricycles_in_hub):
                hubs.append(hub)

        for i in range(number_of_tricycles):
            trike_name = "trike" + str(i)
            start_time = random.randint(0, simulation_duration // 2)
            end_time = random.randint(start_time, simulation_duration)
            tricycle = Tricycle(trike_name, hubs.pop(), start_time, end_time)
            self.spawnedTricycles.add(tricycle)

