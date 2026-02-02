import traci
import random
import math
from infrastructure.TricycleRepository import TricycleRepository
from domain.TodaHubDescriptor import TodaHubDescriptor
from infrastructure.SimulationConfig import SimulationConfig
from infrastructure.TricycleDispatcher import TricycleDispatcher
from infrastructure.TricycleSynchronizer import TricycleSynchronizer
from infrastructure.TricycleStateManager import TricycleStateManager
from infrastructure.SimulationLogger import SimulationLogger

class SimulationEngine:
    def __init__(self, toda_hub_descriptor: TodaHubDescriptor, simulation_config: SimulationConfig, tricycle_dispatcher: TricycleDispatcher, tricycle_repository: TricycleRepository, tricycle_synchronizer: TricycleSynchronizer, tricycle_state_manager: TricycleStateManager, logger: SimulationLogger, duration: int, first_run: bool = True) -> None:
        self.tick = 0
        self.tricycleRepository = tricycle_repository
        self.tricycleDispatcher = tricycle_dispatcher
        self.todaHubDescriptor = toda_hub_descriptor
        self.simulationConfig = simulation_config
        self.tricycleSynchronizer = tricycle_synchronizer
        self.tricycleStateManager = tricycle_state_manager
        self.simulationLogger = logger
        self.duration = duration
        self.first_run = first_run
        if first_run:
            self.tricycleRepository.createTricycles(toda_hub_descriptor.getNumberOfTricycles(), toda_hub_descriptor.getHubDistribution())

    def startTraci(self) -> None:
        additionalFiles = f"{self.simulationConfig.getParkingFilePath()},{self.simulationConfig.getDecalFilePath()}"
        additionalFiles = f"{self.simulationConfig.getParkingFilePath()}"
        traci.start([
            "sumo",
            "-n", self.simulationConfig.getNetworkFilePath(),
            "-r", self.simulationConfig.getRoutesFilePath(),
            "-a", additionalFiles,
            "--lateral-resolution", "2.0",
            "--no-warnings",
            "--ignore-route-errors"
        ])

    def doMainLoop(self, simulation_duration: int) -> None:
        while self.tick < simulation_duration:
            self.tricycleStateManager.updateTricycleStates(self.tick)
            self.tricycleDispatcher.dispatchTricycles(self.simulationLogger, self.tick)
            self.tick += 1
            if self.tick % 60 == 0:
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
        self.tick = 0