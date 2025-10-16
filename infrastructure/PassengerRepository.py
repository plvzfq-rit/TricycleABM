import traci
import random
from pathlib import Path
from domain.Passenger import Passenger
from domain.PassengerFactory import PassengerFactory
from domain.Location import Location
from infrastructure.SimulationConfig import SimulationConfig
from infrastructure.SumoService import SumoService
from infrastructure.TraciService import TraciService

class PassengerRepository:
    def __init__(self, simulation_config: SimulationConfig | None, 
                sumo_service: SumoService | None, 
                traci_service: TraciService | None,
                passenger_factory: PassengerFactory | None) -> None:
        self.passengers = dict()
        self.nextIndex = 0
        self.simulationConfig = simulation_config or SimulationConfig()
        self.sumoService = sumo_service or SumoService()
        self.traciService = traci_service or TraciService()
        self.passengerFactory = passenger_factory or PassengerFactory()
        self.possibleSources = self.traciService.getListOfHubIds()

    def getPassenger(self, passenger_id: str) -> Passenger:
        return self.passengers[passenger_id]
    
    def getPassengerLocation(self, passenger_id: str) -> Location:
        return self.traciService.getPassengerLocation(passenger_id)
    
    def getPassengerDestination(self, passenger_id: str) -> Location:
        return self.getPassenger(passenger_id).destination
    
    def killPassenger(self, passenger_id: str) -> None:
        self.passengers[passenger_id].kill()

    def getActivePassengerIds(self) -> set[str]:
        return set([passenger_id for passenger_id in self.passengers.keys() if self.getPassenger(passenger_id).isAlive()])

    def generateRandomPassenger(self) -> Passenger:
        passenger_id, passenger = self.passengerFactory.createRandomPassenger(self.nextIndex)
        self.passengers[passenger_id] = passenger
        self.nextIndex += 1
        return passenger