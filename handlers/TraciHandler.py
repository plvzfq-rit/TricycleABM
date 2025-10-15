import traci
import random
from repositories.PassengerRepository import PassengerRepository
from repositories.TricycleRepository import TricycleRepository
from domain.MapDescriptor import MapDescriptor
from infrastructure.SimulationConfig import SimulationConfig

class TraciHandler:
    def __init__(self, map_descriptor: MapDescriptor, simulation_config: SimulationConfig, duration: int) -> None:
        self.tick = 0
        self.passengerRepository = PassengerRepository(simulation_config)
        self.tricycleRepository = TricycleRepository()
        self.LEAST_NUMBER_OF_PASSENGERS = 0
        self.MOST_NUMBER_OF_PASSENGERS = 5
        self.mapConfig = map_descriptor
        self.simulationConfig = simulation_config
        self.tricycleRepository.generateTricycles(map_descriptor.getNumberOfTricycles(), duration, map_descriptor.getHubDistribution())

    def startTraci(self) -> None:
        additionalFiles = f"{self.simulationConfig.getParkingFilePath()},{self.simulationConfig.getDecalFilePath()}"
        traci.start([
            "sumo-gui",
            "-n", self.simulationConfig.getNetworkFilePath(),
            "-r", self.simulationConfig.getRoutesFilePath(),
            "-a", additionalFiles,
            "--lateral-resolution", "2.0"
        ])
        self.passengerRepository.initializePossibleSources()

    def generateRandomNumberOfPassengers(self) -> None:
        LOWER_BOUND = self.LEAST_NUMBER_OF_PASSENGERS
        UPPER_BOUND = self.MOST_NUMBER_OF_PASSENGERS
        number_of_passengers = random.randint(LOWER_BOUND, UPPER_BOUND)
        for _ in range(number_of_passengers):
            self.passengerRepository.generateRandomPassenger()

    def assignPassengersToTricycles(self) -> None:
        active_passenger_ids = self.passengerRepository.getActivePassengerIds()
        active_tricycles = self.tricycleRepository.getActiveTricycles()

        for active_passenger_id in active_passenger_ids:
            active_passenger_location = self.passengerRepository.getPassengerLocation(active_passenger_id)
            for active_tricycle in active_tricycles:
                active_tricycle_location = self.tricycleRepository.getTricycleLocation(active_tricycle.name)

                if active_passenger_location.isNear(active_tricycle_location) and self.tricycleRepository.isTricycleFree(active_tricycle.name) and self.passengerRepository.passengers[active_passenger_id].isAlive():
                    self.passengerRepository.killPassenger(active_passenger_id)
                    active_passenger_destination = self.passengerRepository.getPassengerDestination(active_passenger_id)
                    success = self.tricycleRepository.assignPassengerToTricycle(active_tricycle.name, active_passenger_destination, self.traciConfig)
                    if success:
                        break


    def doMainLoop(self, simulation_duration: int) -> None:
        self.startTraci()
        while self.tick < simulation_duration:
            self.passengerRepository.syncPassengers()
            self.generateRandomNumberOfPassengers()
            self.tricycleRepository.syncTricycles()
            self.tricycleRepository.toggleTricycles(self.tick)
            self.assignPassengersToTricycles()
            self.tick += 1
            traci.simulationStep()

    def setPassengerBoundaries(self, lower_bound: int, upper_bound: int) -> None:
        self.LEAST_NUMBER_OF_PASSENGERS = lower_bound
        self.MOST_NUMBER_OF_PASSENGERS = upper_bound

    def close(self) -> None:
        traci.close()