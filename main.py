
import os

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

number_of_runs = 10
number_of_days = 1
duration = 57600

# PHASE 3: INITIALIZING TRICYCLE REPOSITORY

for i in range(number_of_runs):
    tricycle_factory = TricycleFactory(simulation_config)
    tricycle_repository = TricycleRepository(sumo_repository, tricycle_factory, simulation_config)

    # PHASE 4: INITIALIZING PASSENGER REPOSITORY
    passenger_factory = PassengerFactory(sumo_repository, simulation_config)

    # PHASE 5: INITIALIZING OTHER SERVICES
    tricycle_dispatcher = TricycleDispatcher(tricycle_repository, passenger_factory, simulation_config)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    run_dir = os.path.join(".", "analysis", timestamp)

    for i in range(number_of_days):
        print(f"running day# {i + 1}...")
        logger = SimulationLogger(i, run_dir)
        tricycle_repository.changeLogger(logger)
        tricycle_repository.resetAllDailyStats()
        tricycle_state_manager = TricycleStateManager(tricycle_repository, logger)
        simulation_loop = SimulationEngine(toda_hub_descriptor, simulation_config, tricycle_dispatcher, tricycle_repository, tricycle_state_manager, logger, duration, first_run=(i == 0))
        simulation_loop.doMainLoop(duration)
        simulation_loop.close()
        tricycle_repository.startExpenseAllTricycles(simulation_config.getGasPricePerLiter())

    # Close TRACI after all runs are complete
    traci.close()