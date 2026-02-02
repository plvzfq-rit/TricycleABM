
import os

os.dup2(os.open(os.devnull, os.O_WRONLY), 2)
from infrastructure import *
from application import *
import traci

# PHASE 1: INITIALIZING THE MAP ENVIRONMENT

simulation_config = SimulationConfig()

# Start TRACI/SUMO early so all services can use it
traci.start([
    "sumo",
    "-n", simulation_config.getNetworkFilePath(),
    "-r", simulation_config.getRoutesFilePath(),
    "-a", simulation_config.getParkingFilePath(),
    "--lateral-resolution", "2.0",
    "--no-step-log"
])

# PHASE 2: INITIALIZING SERVICES
sumo_service = SumoRepository(simulation_config.getNetworkFilePath())
toda_hub_descriptor = parseParkingAreaFile(simulation_config.getParkingFilePath())

duration = 61200

# PHASE 3: INITIALIZING TRICYCLE REPOSITORY
tricycle_repository = TricycleRepository(sumo_service, simulation_config)

# PHASE 4: INITIALIZING PASSENGER REPOSITORY
passenger_factory = PassengerFactory(sumo_service)

# PHASE 5: INITIALIZING OTHER SERVICES
tricycle_dispatcher = TricycleDispatcher(tricycle_repository, passenger_factory)
tricycle_synchronizer = TricycleSynchronizer(tricycle_repository)

for i in range(2):
    print(f"running run# {i}...")
    logger = SimulationLogger(i)
    tricycle_repository.changeLogger(logger)
    tricycle_state_manager = TricycleStateManager(tricycle_repository, logger)
    simulation_loop = SimulationEngine(toda_hub_descriptor, simulation_config, tricycle_dispatcher, tricycle_repository, tricycle_synchronizer, tricycle_state_manager, logger, duration, first_run=(i == 0))
    simulation_loop.doMainLoop(duration)
    simulation_loop.close()
    tricycle_repository.startRefuelAllTricycles()
    tricycle_repository.startExpenseAllTricycles()

# Close TRACI after all runs are complete
traci.close()