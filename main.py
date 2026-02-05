
import os

os.dup2(os.open(os.devnull, os.O_WRONLY), 2)
from infrastructure import *
from application import *
from utils.ParkingAreaParser import parseParkingAreaFile
import traci

# PHASE 1: INITIALIZING THE MAP ENVIRONMENT

simulation_config = SimulationConfig()

# PHASE 2: INITIALIZING SERVICES
network_file_path = simulation_config.getNetworkFilePath()
parking_file_path = simulation_config.getParkingFilePath()
sumo_repository = SumoRepository(network_file_path)
toda_hub_descriptor = parseParkingAreaFile(parking_file_path)

duration = 61200

# PHASE 3: INITIALIZING TRICYCLE REPOSITORY
tricycle_factory = TricycleFactory(simulation_config)
tricycle_repository = TricycleRepository(sumo_repository, tricycle_factory, simulation_config)

# PHASE 4: INITIALIZING PASSENGER REPOSITORY
passenger_network_edges = sumo_repository.getNetworkPedestrianEdges()
passenger_factory = PassengerFactory(sumo_repository, simulation_config)

# PHASE 5: INITIALIZING OTHER SERVICES
tricycle_dispatcher = TricycleDispatcher(tricycle_repository, passenger_factory, simulation_config)

for i in range(2):
    print(f"running run# {i}...")
    logger = SimulationLogger(i)
    tricycle_repository.changeLogger(logger)
    tricycle_state_manager = TricycleStateManager(tricycle_repository, logger)
    simulation_loop = SimulationEngine(toda_hub_descriptor, simulation_config, tricycle_dispatcher, tricycle_repository, tricycle_state_manager, logger, duration, first_run=(i == 0))
    simulation_loop.doMainLoop(duration)
    simulation_loop.close()
    tricycle_repository.startRefuelAllTricycles()
    tricycle_repository.startExpenseAllTricycles()

# Close TRACI after all runs are complete
traci.close()