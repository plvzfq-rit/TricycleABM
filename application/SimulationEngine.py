import traci
import random
from infrastructure.PassengerRepository import PassengerRepository
from infrastructure.TricycleRepository import TricycleRepository
from domain.MapDescriptor import MapDescriptor
from infrastructure.SimulationConfig import SimulationConfig
from infrastructure.TricycleDispatcher import TricycleDispatcher
from infrastructure.TricycleSynchronizer import TricycleSynchronizer
from infrastructure.PassengerSynchronizer import PassengerSynchronizer
from infrastructure.TricycleStateManager import TricycleStateManager

class SimulationEngine:
    def __init__(self, map_descriptor: MapDescriptor, simulation_config: SimulationConfig, tricycle_dispatcher: TricycleDispatcher, passenger_repository: PassengerRepository, tricycle_repository: TricycleRepository, passenger_synchronizer: PassengerSynchronizer, tricycle_synchronizer: TricycleSynchronizer, tricycle_state_manager: TricycleStateManager, duration: int) -> None:
        self.tick = 0
        self.passengerRepository = passenger_repository
        self.tricycleRepository = tricycle_repository
        self.tricycleDispatcher = tricycle_dispatcher
        self.LEAST_NUMBER_OF_PASSENGERS = 0
        self.MOST_NUMBER_OF_PASSENGERS = 5
        self.mapConfig = map_descriptor
        self.simulationConfig = simulation_config
        self.passengerSynchronizer = passenger_synchronizer
        self.tricycleSynchronizer = tricycle_synchronizer
        self.tricycleStateManager = tricycle_state_manager
        self.tricycleRepository.createTricycles(map_descriptor.getNumberOfTricycles(), duration, map_descriptor.getHubDistribution())

    def startTraci(self) -> None:
        additionalFiles = f"{self.simulationConfig.getParkingFilePath()},{self.simulationConfig.getDecalFilePath()}"
        traci.start([
            "sumo-gui",
            "-n", self.simulationConfig.getNetworkFilePath(),
            "-r", self.simulationConfig.getRoutesFilePath(),
            "-a", additionalFiles,
            "--lateral-resolution", "2.0"
        ])
        self.passengerRepository.discoverPossibleSources()

    def generateRandomNumberOfPassengers(self) -> None:
        LOWER_BOUND = self.LEAST_NUMBER_OF_PASSENGERS
        UPPER_BOUND = self.MOST_NUMBER_OF_PASSENGERS
        number_of_passengers = random.randint(LOWER_BOUND, UPPER_BOUND)
        for _ in range(number_of_passengers):
            self.passengerRepository.createRandomPassenger()

    def doMainLoop(self, simulation_duration: int) -> None:
        self.startTraci()
        #TODO: 
        while self.tick < simulation_duration:
            self.passengerSynchronizer.sync()
            self.generateRandomNumberOfPassengers()
            self.tricycleSynchronizer.sync()
            self.tricycleStateManager.updateTricycleStates(self.tick)
            self.tricycleDispatcher.dispatchTricycles()
            self.tricycleRepository.simulateGasConsumption()
            #Have gas stations check if a tricycle needing to refuel is near, to refuel to max (change to actual number later)
            self.tick += 1
            traci.simulationStep()

    def setPassengerBoundaries(self, lower_bound: int, upper_bound: int) -> None:
        self.LEAST_NUMBER_OF_PASSENGERS = lower_bound
        self.MOST_NUMBER_OF_PASSENGERS = upper_bound

    def close(self) -> None:
        traci.close()