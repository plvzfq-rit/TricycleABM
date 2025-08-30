import sumolib
import traci
import random
from pathlib import Path
from enum import Enum

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

class PassengerRepository:
    def __init__(self) -> None:
        self.passengers = dict()
        self.activePassengers = dict()
        self.killedPassengers = dict()
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
        self.activePassengers[name] = passenger
        self.nextIndex += 1
        return passenger
    
    def killPassenger(self, passenger_id: str) -> None:
        self.killedPassengers[passenger_id] = self.passengers[passenger_id]
        del self.activePassengers[passenger_id]

    def auditPassengers(self) -> None:
        current_passengers = set(traci.person.getIDList())
        passengers_in_memory = set(self.activePassengers.keys())
        passengers_to_kill = passengers_in_memory - current_passengers
        for passenger_id in passengers_to_kill:
            self.killedPassengers[passenger_id] = self.passengers[passenger_id]
            del self.activePassengers[passenger_id]

    def getActivePassengerIds(self) -> set[str]:
        return set(self.activePassengers.keys())
    
    def getPassengerLocation(self, name: str) -> None:
        return (traci.person.getRoadID(name), traci.person.getLanePosition())


