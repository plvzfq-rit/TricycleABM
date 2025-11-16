import random

from domain.Passenger import Passenger

from infrastructure.SumoService import SumoService
from infrastructure.TraciService import TraciService

class PassengerFactory:
    def __init__(self, sumo_service: SumoService | None = None, traci_service: TraciService | None = None):
        self.sumoService = sumo_service or SumoService()
        self.traciService = traci_service or TraciService()
        self.index = 0

    def createRandomPassenger(self, possible_sources) -> tuple[str, Passenger]:
        edges = self.sumoService.getNetworkPedestrianEdges()

        # pick start and destination
        starting_edge = random.choice(possible_sources)
        destination_edge = random.choice(edges)
        while destination_edge.getID() == starting_edge:
            destination_edge = random.choice(edges)

        # start position
        # TODO: Have this actually be a random destination and not just the start smh
        starting_position = 0.0
        name = f"ped{self.index}"
        self.index += 1

        # add the person
        self.traciService.addPassenger(name, starting_edge, starting_position)

        # destination position
        # TODO: Have this actually be a random destination and not just the start smh
        destination_position = 0.0

        # let SUMO compute walking route
        self.traciService.setPassengerDestination(name, destination_edge, destination_position)
        
        return (name, Passenger(name, starting_edge, destination_edge.getID()))