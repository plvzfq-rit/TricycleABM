import sumolib
import traci
import random
from pathlib import Path

class Passenger:
    def __init__(self, name: str, starting_edge: str, destination_edge: str) -> None:
        self.destination = destination_edge
        self.name = name
        self.startingEdge = starting_edge
    def __str__(self) -> str:
        return f"Passenger(destination=\"{self.destination}\")"

class PassengerGenerator:
    def __init__(self) -> None:
        self.passengers = dict()
        self.nextIndex = 0
        self.directoryName = "maps"
        self.networkFileName = "net.net.xml"

    def generateRandomPassenger(self) -> Passenger:
        directory = Path(__file__).resolve().parent.parent / self.directoryName 
        network = sumolib.net.readNet(directory / self.networkFileName)

        # only pedestrian-allowed edges
        edges = [e for e in network.getEdges() if e.allows("pedestrian")]

        # pick start and destination
        starting_edge = random.choice(edges)
        destination_edge = random.choice(edges)
        while destination_edge == starting_edge:
            destination_edge = random.choice(edges)

        # start position
        start_pos = 1.0
        name = f"ped{self.nextIndex}"

        # add the person
        traci.person.add(name, starting_edge.getID(), start_pos, typeID="fatPed")

        # destination position
        dest_pos = 1.0

        # let SUMO compute walking route
        traci.person.appendWalkingStage(name, destination_edge.getID(), dest_pos)

        # track passenger
        passenger = Passenger(name, starting_edge.getID(), destination_edge.getID())
        self.passengers[name] = passenger
        self.nextIndex += 1
        return passenger

