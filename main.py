
"""FairFare (main.py)

Entry point for running the program with custom user-input parameters.

Under default inputs, the simulation will use *DEFAULT* gas price (check
config/SimulationConfig) and a fare matrix:

*16* for trip distances less than or equal to *1000*m
*5* increase for each distance increase of *500*m or fraction thereof

Each param can be changed through user args with flags --gas_price,
--base_price, --base_distance, --added_price, and --added_distance,
respectively.

"""

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
# import random
# import numpy as np

# random.seed(42)
# np.random.seed(42)

parser = argparse.ArgumentParser()
parser.add_argument("--base_price", type=int, default=16)
parser.add_argument("--base_distance", type=int, default=1000)
parser.add_argument("--added_price", type=int, default=5)
parser.add_argument("--added_distance", type=int, default=500)
parser.add_argument("--gas_price", default="DEFAULT")

args = parser.parse_args()

"""Initialize Map Environment"""
simulation_config = SimulationConfig(
    gas_price_select=args.gas_price, 
    base_price=args.base_price, 
    base_distance=args.base_distance, 
    added_price=args.added_price, 
    added_distance=args.added_distance
)

# PHASE 2: INITIALIZING SERVICES
"""Initialize Services"""
network_file_path = simulation_config.getNetworkFilePath()
parking_file_path = simulation_config.getParkingFilePath()
sumo_repository = SumoRepository(network_file_path)
toda_hub_descriptor = parseParkingAreaFile(parking_file_path)

number_of_runs = 30
number_of_days = 1
duration = 57600
run_name = (str(args.base_price) + "_" + str(args.base_distance) + "_" + 
           str(args.added_price) + "_" + str(args.added_distance) + "_" + args.gas_price)

startTime = datetime.now().strftime("%Y%m%d-%H%M%S")

# PHASE 3: INITIALIZING TRICYCLE REPOSITORY
"""Initialize infrastructure/TricycleRepository"""
for run in range(number_of_runs):
    tricycle_factory = TricycleFactory(simulation_config)
    tricycle_repository = TricycleRepository(sumo_repository, tricycle_factory, simulation_config)

    """Initialize infrastructure/PassengerFactory"""
    passenger_factory = PassengerFactory(sumo_repository, simulation_config)

    """Initialize infrastructure/TricycleDispatcher"""
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

    traci.close()

print("All runs completed.")
print("start time: ", startTime)
print("end time: ", datetime.now().strftime("%Y%m%d-%H%M%S"))
