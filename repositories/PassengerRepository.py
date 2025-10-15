import traci
import random
from pathlib import Path
from domain.Passenger import Passenger
from domain.Location import Location
from infrastructure.SimulationConfig import SimulationConfig
from infrastructure.SumoService import SumoService
from infrastructure.TraciService import TraciService

class PassengerRepository:
    def __init__(self, simulation_config: SimulationConfig | None, 
                sumo_service: SumoService | None, 
                traci_service: TraciService | None) -> None:
        self.passengers = dict()
        self.activePassengers = dict()
        self.killedPassengers = dict()
        self.nextIndex = 0
        self.simulationConfig = simulation_config or SimulationConfig()
        self.sumoService = sumo_service or SumoService()
        self.traciService = traci_service or TraciService()
        self.possibleSources = self.traciService.getListOfHubIds()

    def generateRandomPassenger(self) -> Passenger:
        # only pedestrian-allowed edges
        edges = self.sumoService.getNetworkPedestrianEdges()

        # pick start and destination
        starting_edge = random.choice(self.possibleSources)
        destination_edge = random.choice(edges)
        while destination_edge.getID() == starting_edge:
            destination_edge = random.choice(edges)

        # start position
        start_pos = 0.0
        name = f"ped{self.nextIndex}"

        # add the person
        traci.person.add(name, starting_edge, start_pos, typeID="fatPed")

        # destination position
        dest_pos = 0.0

        # let SUMO compute walking route
        traci.person.appendWalkingStage(name, destination_edge.getID(), dest_pos)

        # track passenger
        passenger = Passenger(name, starting_edge, destination_edge.getID())
        self.passengers[name] = passenger
        self.activePassengers[name] = passenger
        self.nextIndex += 1
        # print(passenger)
        return passenger
    
    def killPassenger(self, passenger_id: str) -> None:
        self.passengers[passenger_id].kill()
        self.killedPassengers[passenger_id] = self.passengers[passenger_id]
        del self.activePassengers[passenger_id]

    def syncPassengers(self) -> None:
        current_passengers = set(traci.person.getIDList())
        passengers_in_memory = set(self.activePassengers.keys())
        passengers_to_kill = passengers_in_memory - current_passengers
        for passenger_id in passengers_to_kill:
            self.killPassenger(passenger_id)

    def getActivePassengerIds(self) -> set[str]:
        return set(self.activePassengers.keys())
    
    def getPassengerLocation(self, passenger_id: str) -> tuple[str, float]:
        current_edge = traci.person.getRoadID(passenger_id)
        current_position = traci.person.getLanePosition(passenger_id)
        return Location(current_edge, current_position)
    
    def getPassengerDestination(self, passenger_id: str) -> str:
        return self.passengers[passenger_id].destination
