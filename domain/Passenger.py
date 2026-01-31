from domain.Location import Location
import scipy.stats as stats

import random

def randomize_passenger_size():
    if random.random() <= 0.5:
        return 1
    elif random.random() <=0.75:
        return 2
    elif random.random() <= 0.75:
        return 3
    elif random.random() <= 0.75:
        return 4
    elif random.random() <= 0.75:
        return 5

class Passenger:
    def __init__(self, name: str, starting_edge: str, destination_edge: str, lane: int, dist: float) -> None:
        self.destination = Location(destination_edge, dist)
        self.name = name
        self.startingEdge = starting_edge
        self.alive = True
        self.willingness_to_pay = stats.lognorm.rvs(0.7134231299166108, loc=0, scale=38.38513260285555, size=1)
        self.size = randomize_passenger_size()
        self.knowledgable = random.random() < 0.1
        self.lane = lane
    def __str__(self) -> str:
        return f"Passenger(name=,\"{self.name}\", start=\"{self.startingEdge}\", destination=\"{self.destination}\")"
    def kill(self) -> None:
        self.alive = False
    def isAlive(self) -> bool:
        return self.alive 