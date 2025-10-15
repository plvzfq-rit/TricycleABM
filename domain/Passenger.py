from domain.Location import Location
class Passenger:
    def __init__(self, name: str, starting_edge: str, destination_edge: str) -> None:
        self.destination = Location(destination_edge, 1.0)
        self.name = name
        self.startingEdge = starting_edge
        self.alive = True
    def __str__(self) -> str:
        return f"Passenger(name=,\"{self.name}\", start=\"{self.startingEdge}\", destination=\"{self.destination}\")"
    def kill(self) -> None:
        self.alive = False
    def isAlive(self) -> bool:
        return self.alive 