import traci
import random
import math
from infrastructure.TricycleRepository import TricycleRepository
from domain.TodaHubDescriptor import TodaHubDescriptor
from config.SimulationConfig import SimulationConfig
from infrastructure.TricycleDispatcher import TricycleDispatcher
from infrastructure.TricycleStateManager import TricycleStateManager
from infrastructure.SimulationLogger import SimulationLogger
from infrastructure.TodaRepository import TodaRepository
from utils.TraciUtils import getVehiclesInSimulation

class SimulationEngine:
    def __init__(self, toda_hub_descriptor: TodaHubDescriptor, simulation_config: SimulationConfig, tricycle_dispatcher: TricycleDispatcher, tricycle_repository: TricycleRepository, tricycle_state_manager: TricycleStateManager, logger: SimulationLogger, duration: int, first_run: bool = True) -> None:
        self.tick = 0
        self.tricycleRepository = tricycle_repository
        self.tricycleDispatcher = tricycle_dispatcher
        self.todaHubDescriptor = toda_hub_descriptor
        self.simulationConfig = simulation_config
        self.tricycleStateManager = tricycle_state_manager
        self.simulationLogger = logger
        self.duration = duration
        self.first_run = first_run
        if first_run:
            self.tricycleRepository.createTricycles(toda_hub_descriptor.getNumberOfTricycles(), toda_hub_descriptor.getHubDistribution())
            for tricycle in self.tricycleRepository.getTricycles():
                self.simulationLogger.addDriver(tricycle)
        self.todaRepository = None

    def startTraci(self) -> None:
        additionalFiles = f"{self.simulationConfig.getParkingFilePath()},{self.simulationConfig.getDecalFilePath()}"
        additionalFiles = f"{self.simulationConfig.getParkingFilePath()}"
        traci.start([
            "sumo",
            "-n", self.simulationConfig.getNetworkFilePath(),
            "-r", self.simulationConfig.getRoutesFilePath(),
            "-a", additionalFiles,
            "--lateral-resolution", "2.0",
            "--collision.action", "none",
            "--time-to-teleport", "-1",
            "--no-step-log", "true",
            "--duration-log.disable", "true",
            "--no-warnings", "true",
            "--verbose", "false",
            "--error-log", "tmp.txt"
        ])

    def doMainLoop(self, simulation_duration: int) -> None:
        if self.first_run:
            self.startTraci()
        self.todaRepository = TodaRepository()
        
        while self.tick < simulation_duration:
            vehicles_in_sim = getVehiclesInSimulation()
            for trike in self.tricycleRepository.getTricycles():
                if trike.name not in vehicles_in_sim and trike.startTime - self.tick > 1:
                    trike.kill()
            self.tricycleStateManager.updateTricycleStates(self.tick)
            self.todaRepository.manageTodaQueues()
            self.tricycleDispatcher.tryDispatchFromTodaQueues(self.simulationLogger, self.tick, self.todaRepository)
            self.tick += 1
            if self.tick % 60 == 0:
                print(f"\rCurrent time: {math.floor(self.tick / 3600) + 6:02d}:{math.floor((self.tick % 3600) / 60):02d}:{self.tick % 60:02d}                 ", end="")
            traci.simulationStep()

    def close(self) -> None:
        self.tick = 0