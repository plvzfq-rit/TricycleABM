from domain.Location import Location
import scipy.stats as stats

import random

class Passenger:
    def __init__(self, name: str, starting_edge: str, destination_edge: str, lane: int, dist: float) -> None:
        self.destination = Location(destination_edge, dist)
        self.name = name
        self.startingEdge = starting_edge
        self.alive = True
        self.willingness_to_pay = stats.lognorm.rvs(0.7134231299166108, loc=0, scale=38.38513260285555, size=1)
        self.lane = lane
    def __str__(self) -> str:
        return f"Passenger(name=,\"{self.name}\", start=\"{self.startingEdge}\", destination=\"{self.destination}\")"
    def kill(self) -> None:
        self.alive = False
    def isAlive(self) -> bool:
        return self.alive 