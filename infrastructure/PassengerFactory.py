import random

from .SumoRepository import SumoRepository
from .TraciManager import TraciManager

from domain.Passenger import Passenger



class PassengerFactory:
    def __init__(self, sumo_service: SumoRepository):
        self.sumoService = sumo_service 
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
        lane_index = TraciManager.getNumberOfLanes(destination_edge.getID()) - 1 if random.random() >= 0.5 else 0
        lane = destination_edge.getID() + "_" + str(lane_index)

        lane_length = TraciManager.getLaneLength(lane)
        dist = random.random() * lane_length
        
        return Passenger(name, starting_edge, destination_edge.getID(), lane_index, dist)