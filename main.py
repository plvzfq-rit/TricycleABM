
import os

# os.dup2(os.open(os.devnull, os.O_WRONLY), 2)
from utils import *
from domain import *
from infrastructure import *
from application import *
from config.SimulationConfig import SimulationConfig
from utils.ParkingAreaParser import parseParkingAreaFile
from datetime import datetime
import traci

# PHASE 1: INITIALIZING THE MAP ENVIRONMENT

simulation_config = SimulationConfig()

# PHASE 2: INITIALIZING SERVICES
network_file_path = simulation_config.getNetworkFilePath()
parking_file_path = simulation_config.getParkingFilePath()
sumo_repository = SumoRepository(network_file_path)
toda_hub_descriptor = parseParkingAreaFile(parking_file_path)

duration = 57600
number_of_sims = 1
number_of_days = 10

for sim in range(number_of_sims):

    # PHASE 3: INITIALIZING TRICYCLE REPOSITORY
    tricycle_factory = TricycleFactory(simulation_config)

    # PHASE 4: INITIALIZING PASSENGER REPOSITORY
    logger = SimulationLogger()
    tricycle_repository = TricycleRepository(sumo_repository, tricycle_factory, simulation_config, logger)
    passenger_network_edges = sumo_repository.getNetworkPedestrianEdges()
    passenger_factory = PassengerFactory(sumo_repository, simulation_config, logger)

    # PHASE 5: INITIALIZING OTHER SERVICES
    tricycle_dispatcher = TricycleDispatcher(tricycle_repository, passenger_factory, simulation_config)
    tricycle_state_manager = TricycleStateManager(tricycle_repository, logger)

    for day in range(number_of_days):
        print(f"running sim# {sim + 1}, day# {day + 1}...")
        # tricycle_repository.changeLogger(logger)
        simulation_loop = SimulationEngine(toda_hub_descriptor, simulation_config, tricycle_dispatcher, tricycle_repository, tricycle_state_manager, logger, duration, first_run=(day == 0))
        simulation_loop.doMainLoop(duration)
        simulation_loop.close()
        tricycle_repository.startRefuelAllTricycles()
        tricycle_repository.startExpenseAllTricycles()
        logger.nextDay()

    # Close TRACI after all runs are complete
    traci.close()
