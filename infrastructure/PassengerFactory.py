import random

from config.SimulationConfig import SimulationConfig

from .SumoRepository import SumoRepository
from .SimulationLogger import SimulationLogger

from domain.Passenger import Passenger
from domain.Location import Location, getManhattanDistance

class PassengerFactory:
    """Generates Passenger objects with a random destination in the
    simulation.

    Attributes:
        networkPedestrianEdges: list of pedestrian edges in the network.
        wtpDistribution: distribution function for willingness to pay.
        todaPositions: dictionary of Toda hub positions.
        index: integer index for unique passenger naming.
    """
    def __init__(self, sumo_repository: SumoRepository, simulation_config: SimulationConfig, simulation_logger: SimulationLogger) -> None:
        """Initializes object with elements from SumoRepository and SimulationConfig.

        Args:
            sumo_repository: SumoRepository object to extract network edges.
            simulation_config: SimulationConfig object to extract WTP and Toda positions.
        """

        # Extract necessary data from SumoRepository and SimulationConfig
        self.networkPedestrianEdges = sumo_repository.getNetworkPedestrianEdges()
        self.wtpDistribution = simulation_config.getWTPDistribution()
        self.todaPositions = simulation_config.getTodaPositions()
        self.patienceDistribution = simulation_config.getPassengerPatienceDistribution()
        self.aspiredPriceDistribution = simulation_config.getPassengerAspiredPriceDistribution()
        self.sumoRepository = sumo_repository
        self.simulationLogger = simulation_logger

        # Initialize passenger index for unique naming
        self.index = 0

    def createRandomPassenger(self, starting_edge: str) -> tuple[str, Passenger]:
        """Creates a Passenger object with a random destination edge.

        Args:
            starting_edge: the edge ID where the passenger starts.

        Returns:
            A Passenger object with a random destination edge.
        """

        # select a random destination edge different from starting edge
        destination_edge = random.choice(self.networkPedestrianEdges)
        while destination_edge == starting_edge:
            destination_edge = random.choice(self.networkPedestrianEdges)

        # create passenger name
        name = f"ped{self.index}"
        self.index += 1

        # select lane index (first or last lane of the edge)
        lane_index = self.sumoRepository.getNumberOfLanes(destination_edge) - 1 if \
                     random.random() >= 0.5 else \
                     0
        
        # construct full lane ID
        lane_id = destination_edge + "_" + str(lane_index)

        # select random distance along lane
        lane_length = self.sumoRepository.getLaneLength(lane_id)
        position = random.random() * lane_length

        # calculate distance to destination
        source_position = self.todaPositions.get(starting_edge, 0.0)
        source = Location(starting_edge, source_position, -1)
        destination = Location(destination_edge, position, lane_index)
        distance = getManhattanDistance(source, destination) / 1000.0  # convert to km

        # generate willingness to pay (peso/km times distance in km)
        willingness_to_pay = self.wtpDistribution(size=1) * distance

        # create Location object for destination
        destination = Location(destination_edge, position, lane_index)

        patience = self.patienceDistribution()

        aspiredPrice = self.aspiredPriceDistribution()

        passenger = Passenger(name, willingness_to_pay, patience, aspiredPrice, destination)

        self.simulationLogger.addPassenger(passenger)
        
        # create and return Passenger object
        return passenger