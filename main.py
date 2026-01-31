from domain import *
from infrastructure import *
from application import *

# PHASE 1: INITIALIZING THE MAP ENVIRONMENT

simulation_config = SimulationConfig()
parking_area_parser = ParkingAreaParser()

# PHASE 2: INITIALIZING SERVICES
traci_service = TraciService()
sumo_service = SumoService(simulation_config.getNetworkFilePath())
map_descriptor = ParkingAreaParser.parse(simulation_config.getParkingFilePath())

duration = 64800

# PHASE 3: INITIALIZING TRICYCLE REPOSITORY
tricycle_repository = TricycleRepository(traci_service, sumo_service, simulation_config)

# PHASE 4: INITIALIZING PASSENGER REPOSITORY
passenger_factory = PassengerFactory(sumo_service, traci_service)

# PHASE 5: INITIALIZING OTHER SERVICES
tricycle_dispatcher = TricycleDispatcher(tricycle_repository, passenger_factory)
tricycle_synchronizer = TricycleSynchronizer(tricycle_repository, traci_service)

for i in range(1):
    print(f"running run# {i}...")
    logger = SimulationLogger(i)
    tricycle_repository.changeLogger(logger)
    tricycle_state_manager = TricycleStateManager(tricycle_repository, traci_service, logger)
    simulation_loop = SimulationEngine(map_descriptor, simulation_config, tricycle_dispatcher, tricycle_repository, tricycle_synchronizer, tricycle_state_manager, logger, duration)
    simulation_loop.doMainLoop(duration)
    simulation_loop.close()
    tricycle_repository.startRefuelAllTricycles()
    tricycle_repository.startExpenseAllTricycles()