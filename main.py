from domain import *
from infrastructure import *
from application import *

import argparse

# hotfix
# Initialize logger
#parser = argparse.ArgumentParser()
#parser.add_argument("--sim_count", type=int, required=True)
#args = parser.parse_args()
#args.sim_count

## place temp (for multithreading, each thread gets a separate temp/assets dir)
# temp_directory = logger.getDirectory()

# PHASE 1: INITIALIZING THE MAP ENVIRONMENT

simulation_config = SimulationConfig()
file_system_descriptor = FileSystemDescriptor("")
parking_area_parser = ParkingAreaParser()
file_sync_service = FileSynchronizer()

# PHASE 2: INITIALIZING SERVICES
traci_service = TraciService()
sumo_service = SumoService(simulation_config.getNetworkFilePath())

map_builder = SpecificMapBuilder(simulation_config, file_system_descriptor, parking_area_parser, file_sync_service)
# map_builder = RandomMapBuilder(simulation_config, ParkingFileGenerator(sumo_service), MapGenerator())

map_descriptor = map_builder.build()

duration = 12000

# PHASE 3: INITIALIZING TRICYCLE REPOSITORY
lower_gas_bound = 50.0
upper_gas_bound = 52.0
tricycle_factory = TricycleFactory(lower_gas_bound, upper_gas_bound)
tricycle_repository = TricycleRepository(tricycle_factory, traci_service, sumo_service, simulation_config)

# PHASE 4: INITIALIZING PASSENGER REPOSITORY
passenger_factory = PassengerFactory(sumo_service, traci_service)
passenger_repository = PassengerRepository(simulation_config, sumo_service, traci_service, passenger_factory)

# PHASE 5: INITIALIZING OTHER SERVICES
tricycle_dispatcher = TricycleDispatcher(tricycle_repository, passenger_repository, passenger_factory)
passenger_synchronizer = PassengerSynchronizer(passenger_repository, traci_service)
tricycle_synchronizer = TricycleSynchronizer(tricycle_repository, traci_service)

for i in range(30):
    print(f"running run# {i}...")
    logger = SimulationLogger(i)
    tricycle_repository.changeLogger(logger)
    tricycle_state_manager = TricycleStateManager(tricycle_repository, traci_service, logger)
    simulation_loop = SimulationEngine(map_descriptor, simulation_config, tricycle_dispatcher, passenger_repository, tricycle_repository, passenger_synchronizer, tricycle_synchronizer, tricycle_state_manager, logger, duration)
    simulation_loop.doMainLoop(duration)
    simulation_loop.close()
    tricycle_repository.startRefuelAllTricycles()
    tricycle_repository.startExpenseAllTricycles()

# Delete temp files after sim
# file_sync_service.removeDirectory(file_system_descriptor.getOutputDirectory())