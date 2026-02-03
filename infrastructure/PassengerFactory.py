import random
from scipy.stats import lognorm

from .SumoRepository import SumoRepository
from utils.TraciUtils import getNumberOfLanes, getLaneLength

from domain.Passenger import Passenger
from domain.Location import Location

class PassengerFactory:
    """Generates Passenger objects with a random destination in the
    simulation.

    Attributes:
        sumoService: 
    """
    def __init__(self, sumo_repository: SumoRepository):
        """Initializes object with access to a SumoRepository and a count.
        
        SumoRepository serves as a source of """
        self.sumoRepository = sumo_repository 
        self.index = 0

    def createRandomPassenger(self, starting_edge: str) -> tuple[str, Passenger]:
        pedestrian_edges = self.sumoRepository.getNetworkPedestrianEdges()

        # pick start and destination
        destination_edge = random.choice(pedestrian_edges)
        while destination_edge.getID() == starting_edge:
            destination_edge = random.choice(pedestrian_edges)

        name = f"ped{self.index}"
        self.index += 1

        # destination position
        lane_index = getNumberOfLanes(destination_edge.getID()) - 1 if random.random() >= 0.5 else 0
        lane = destination_edge.getID() + "_" + str(lane_index)

        lane_length = getLaneLength(lane)
        dist = random.random() * lane_length

        willingness_to_pay = lognorm.rvs(0.7134231299166108, loc=0, scale=38.38513260285555, size=1)

        destination = Location(destination_edge.getID(), dist, lane_index)
        
        return Passenger(name, willingness_to_pay, destination)