import traci
import random
import math
from infrastructure.TricycleRepository import TricycleRepository
from domain.MapDescriptor import MapDescriptor
from infrastructure.SimulationConfig import SimulationConfig
from infrastructure.TricycleDispatcher import TricycleDispatcher
from infrastructure.TricycleSynchronizer import TricycleSynchronizer
from infrastructure.TricycleStateManager import TricycleStateManager
from infrastructure.SimulationLogger import SimulationLogger

class SimulationEngine:
    def __init__(self, map_descriptor: MapDescriptor, simulation_config: SimulationConfig, tricycle_dispatcher: TricycleDispatcher, tricycle_repository: TricycleRepository, tricycle_synchronizer: TricycleSynchronizer, tricycle_state_manager: TricycleStateManager, logger: SimulationLogger) -> None:
        self.tick = 0
        self.tricycleRepository = tricycle_repository
        self.tricycleDispatcher = tricycle_dispatcher
        self.mapConfig = map_descriptor
        self.simulationConfig = simulation_config
        self.tricycleSynchronizer = tricycle_synchronizer
        self.tricycleStateManager = tricycle_state_manager
        self.tricycleRepository.createTricycles(map_descriptor.getNumberOfTricycles(), map_descriptor.getHubDistribution())
        self.simulationLogger = logger

    def startTraci(self) -> None:
        additionalFiles = f"{self.simulationConfig.getParkingFilePath()},{self.simulationConfig.getDecalFilePath()}"
        additionalFiles = f"{self.simulationConfig.getParkingFilePath()}"
        traci.start([
            "sumo-gui",
            "-n", self.simulationConfig.getNetworkFilePath(),
            "-r", self.simulationConfig.getRoutesFilePath(),
            "-a", additionalFiles,
            "--lateral-resolution", "2.0"
        ])

    def doMainLoop(self, simulation_duration: int) -> None:
        self.startTraci()
        #TODO:
        while self.tick < simulation_duration:
            self.tricycleStateManager.updateTricycleStates(self.tick)
            self.tricycleDispatcher.dispatchTricycles(self.simulationLogger, self.tick)
            self.tick += 1
            print(f"\rCurrent time: {math.floor(self.tick / 3600) + 6:02d}:{math.floor((self.tick % 3600) / 60):02d}:{self.tick % 60:02d}                 ", end="")
            traci.simulationStep()

        # Finalize any tricycles still active and log driver info with actual durations
        self._finalizeSimulation(simulation_duration)

    def _finalizeSimulation(self, final_tick: int) -> None:
        """Record final actual end times for any tricycles still active and log all driver info"""
        for tricycle in self.tricycleRepository.getTricycles():
            if tricycle.actualEndTick is None and tricycle.actualStartTick is not None:
                tricycle.recordActualEnd(final_tick)
        # Log driver info with actual durations at the end of simulation
        self.simulationLogger.addDriverInfo(self.tricycleRepository.getTricycles())

    def setPassengerBoundaries(self, lower_bound: int, upper_bound: int) -> None:
        self.LEAST_NUMBER_OF_PASSENGERS = lower_bound
        self.MOST_NUMBER_OF_PASSENGERS = upper_bound

    def close(self) -> None:
        traci.close()