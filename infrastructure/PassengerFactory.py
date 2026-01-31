import random

from domain.Passenger import Passenger

from infrastructure.SumoService import SumoService
from infrastructure.TraciService import TraciService

class PassengerFactory:
    def __init__(self, sumo_service: SumoService | None = None, traci_service: TraciService | None = None):
        self.sumoService = sumo_service or SumoService()
        self.traciService = traci_service or TraciService()
        self.index = 0

    def createRandomPassenger(self, possible_source) -> tuple[str, Passenger]:
        edges = self.sumoService.getNetworkPedestrianEdges()

        # pick start and destination
        starting_edge = possible_source
        destination_edge = random.choice(edges)
        while destination_edge.getID() == starting_edge:
            destination_edge = random.choice(edges)

        name = f"ped{self.index}"
        self.index += 1

        # destination position
        lane_index = self.traciService.getNumberOfLanes(destination_edge.getID()) - 1 if random.random() >= 0.5 else 0
        lane = destination_edge.getID() + "_" + str(lane_index)

        lane_length = self.traciService.getLaneLength(lane)
        dist = random.random() * lane_length

        # let SUMO compute walking route
        # self.traciService.setPassengerDestination(name, destination_edge, destination_position)
        
        return Passenger(name, starting_edge, destination_edge.getID(), lane_index, dist)