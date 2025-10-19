from domain import *
from infrastructure import *
from application import *


# PHASE 1: INITIALIZING THE MAP ENVIRONMENT

simulation_config = SimulationConfig()
file_system_descriptor = FileSystemDescriptor()
parking_area_parser = ParkingAreaParser()
file_sync_service = FileSynchronizer()

map_builder = SpecificMapBuilder(simulation_config, file_system_descriptor, parking_area_parser, file_sync_service)
map_descriptor = map_builder.build()


duration = 1080

# PHASE 2: INITIALIZING SERVICES
traci_service = TraciService()
sumo_service = SumoService(simulation_config.getNetworkFilePath())

# PHASE 3: INITIALIZING TRICYCLE REPOSITORY
lower_gas_bound = 50.0
upper_gas_bound = 52.0
tricycle_factory = TricycleFactory(lower_gas_bound, upper_gas_bound)
tricycle_repository = TricycleRepository(tricycle_factory, traci_service, sumo_service, simulation_config)

# PHASE 4: INITIALIZING PASSENGER REPOSITORY
passenger_factory = PassengerFactory(sumo_service, traci_service)
passenger_repository = PassengerRepository(simulation_config, sumo_service, traci_service, passenger_factory)

# PHASE 5: INITIALIZING OTHER SERVICES
tricycle_dispatcher = TricycleDispatcher(tricycle_repository, passenger_repository)
passenger_synchronizer = PassengerSynchronizer(passenger_repository, traci_service)
tricycle_synchronizer = TricycleSynchronizer(tricycle_repository, traci_service)
tricycle_state_manager = TricycleStateManager(tricycle_repository, traci_service)

# PHASE 6: RUNNING SIMULATION LOOP
simulation_loop = SimulationEngine(map_descriptor, simulation_config, tricycle_dispatcher, passenger_repository, tricycle_repository, passenger_synchronizer, tricycle_synchronizer, tricycle_state_manager, duration)
simulation_loop.setPassengerBoundaries(2, 2)
simulation_loop.doMainLoop(duration)
simulation_loop.close()
