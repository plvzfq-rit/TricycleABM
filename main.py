
import os

from utils import *
from domain import *
from infrastructure import *
from application import *
from config.SimulationConfig import SimulationConfig
from utils.ParkingAreaParser import parseParkingAreaFile
from datetime import datetime
import argparse
import traci

parser = argparse.ArgumentParser()
parser.add_argument("--matrix", default="default")
parser.add_argument("--gas_price", default="default")

args = parser.parse_args()

# PHASE 1: INITIALIZING THE MAP ENVIRONMENT
simulation_config = SimulationConfig(gas_price_select=args.gas_price, matrix_select=args.matrix)

# PHASE 2: INITIALIZING SERVICES
network_file_path = simulation_config.getNetworkFilePath()
parking_file_path = simulation_config.getParkingFilePath()
sumo_repository = SumoRepository(network_file_path)
toda_hub_descriptor = parseParkingAreaFile(parking_file_path)

number_of_runs = 30
number_of_days = 1
duration = 57600
run_name = args.matrix + "_" + args.gas_price

startTime = datetime.now().strftime("%Y%m%d-%H%M%S")

# PHASE 3: INITIALIZING TRICYCLE REPOSITORY

for run in range(number_of_runs):
    tricycle_factory = TricycleFactory(simulation_config)
    tricycle_repository = TricycleRepository(sumo_repository, tricycle_factory, simulation_config)

    # PHASE 4: INITIALIZING PASSENGER REPOSITORY
    passenger_factory = PassengerFactory(sumo_repository, simulation_config)

    # PHASE 5: INITIALIZING OTHER SERVICES
    tricycle_dispatcher = TricycleDispatcher(tricycle_repository, passenger_factory, simulation_config)

    run_dir = os.path.join(".", "analysis", run_name)

    for day in range(number_of_days):
        print(f"running run# {run + 1}, day# {day + 1}...")
        logger = SimulationLogger(run, run_dir)
        tricycle_repository.changeLogger(logger)
        tricycle_repository.resetAllDailyStats()
        tricycle_state_manager = TricycleStateManager(tricycle_repository, logger)
        simulation_loop = SimulationEngine(toda_hub_descriptor, simulation_config, tricycle_dispatcher, tricycle_repository, tricycle_state_manager, logger, duration, first_run=(day == 0))
        simulation_loop.doMainLoop(duration)
        simulation_loop.close()
        tricycle_repository.startExpenseAllTricycles(simulation_config.getGasPricePerLiter())

    # Close TRACI after all runs are complete
    traci.close()

print("All runs completed.")
print("start time: ", startTime)
print("end time: ", datetime.now().strftime("%Y%m%d-%H%M%S"))