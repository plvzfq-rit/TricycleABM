class Passenger:
    def __init__(self, name: str, starting_edge: str, destination_edge: str) -> None:
        self.destination = destination_edge
        self.name = name
        self.startingEdge = starting_edge
        self.alive = True
    def __str__(self) -> str:
        return f"Passenger(destination=\"{self.destination}\")"
    def kill(self) -> None:
        self.alive = False