"""Module for the main simulation engine orchestrating ABMS execution.

Bridges custom vehicle and passenger events/flow to SUMO simulation instance.
"""

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


class SimulationEngine:
    """Control SUMO simulation through the main simulation loop.
    
    :ivar tick: Current simulation time in seconds.
    :ivar tricycleRepository: Repository of all tricycles.
    :ivar tricycleDispatcher: Dispatcher for assigning passengers to tricycles.
    :ivar simulationConfig: Simulation configuration parameters.
    :ivar tricycleStateManager: Manager for tricycle state transitions.
    :ivar simulationLogger: Logger for recording all trips.
    :ivar duration: Total simulation duration in seconds.
    :ivar first_run: Whether this is the first simulation run.
    :ivar todaRepository: Repository for TODA hub queues.
    """
    
    def __init__(self, toda_hub_descriptor: TodaHubDescriptor, simulation_config: SimulationConfig, 
                 tricycle_dispatcher: TricycleDispatcher, tricycle_repository: TricycleRepository, 
                 tricycle_state_manager: TricycleStateManager, logger: SimulationLogger, 
                 duration: int, first_run: bool = True) -> None:
        """Initialize the simulation engine.
        
        :param toda_hub_descriptor: TODA Information.
        :type toda_hub_descriptor: TodaHubDescriptor
        :param simulation_config: Configuration parameters.
        :type simulation_config: SimulationConfig
        :param tricycle_dispatcher: Dispatcher for passenger assignments.
        :type tricycle_dispatcher: TricycleDispatcher
        :param tricycle_repository: Repository of tricycles.
        :type tricycle_repository: TricycleRepository
        :param tricycle_state_manager: Manager for state updates.
        :type tricycle_state_manager: TricycleStateManager
        :param logger: Logger for recording data.
        :type logger: SimulationLogger
        :param duration: Simulation duration (ticks).
        :type duration: int
        :param first_run: Whether this is the first run (creates tricycles).
        :type first_run: bool
        """
        self.tick = 0
        self.tricycleRepository = tricycle_repository
        self.tricycleDispatcher = tricycle_dispatcher
        self.simulationConfig = simulation_config
        self.tricycleStateManager = tricycle_state_manager
        self.simulationLogger = logger
        self.duration = duration
        self.first_run = first_run
        if first_run:
            self.tricycleRepository.createTricycles(toda_hub_descriptor.getNumberOfTricycles(), toda_hub_descriptor.getHubDistribution())
        self.todaRepository = None

    def startTraci(self) -> None:
        """Initialize and start the SUMO TraCI connection.
        
        Loads routes and tricycle configurations, then starts the simulation in the shell.
        """
        additionalFiles = f"{self.simulationConfig.getParkingFilePath()},{self.simulationConfig.getDecalFilePath()}"
        additionalFiles = f"{self.simulationConfig.getParkingFilePath()}"
        traci.start([
            "sumo",
            "-n", self.simulationConfig.getNetworkFilePath(),
            "-r", self.simulationConfig.getRoutesFilePath(),
            "-a", additionalFiles,
            "--lateral-resolution", "2.0"
        ])

    def doMainLoop(self, simulation_duration: int) -> None:
        """Execute the main simulation loop.
        
        :param simulation_duration: Length of simulation (in ticks)
        :type simulation_duration: int
        """
        if self.first_run:
            self.startTraci()
        self.todaRepository = TodaRepository()
        # TODO: Add more specific loop logic
        while self.tick < simulation_duration:
            self.tricycleStateManager.updateTricycleStates(self.tick)
            self.todaRepository.manageTodaQueues()
            self.tricycleDispatcher.tryDispatchFromTodaQueues(self.simulationLogger, self.tick, self.todaRepository)
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
        self.simulationLogger.writeTripSummary()
        print(f"\nTrip summary: {self.simulationLogger.accepted_trips} accepted, {self.simulationLogger.rejected_trips} rejected out of {self.simulationLogger.accepted_trips + self.simulationLogger.rejected_trips} attempts")

    def close(self) -> None:
        self.tick = 0