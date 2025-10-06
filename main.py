from builders.specific_map_builder.SpecificMapBuilder import SpecificMapBuilder
from builders.random_map_builder.RandomMapBuilder import RandomMapBuilder
from handlers.traci_handler.TraciHandler import TraciHandler
from config.traci_config.TraciConfig import TraciConfig
from config.map_config.MapConfig import MapConfig
from config.source_config.SourceConfig import SourceConfig
from config.destination_config.DestinationConfig import DestinationConfig

traci_config = TraciConfig()
map_config = MapConfig()
source_config = SourceConfig()
destination_config = DestinationConfig()

map_builder = SpecificMapBuilder(map_config, traci_config, source_config, destination_config)
#map_builder = RandomMapBuilder().withType("spider").withParkings(5).withNumberOfDivisions(3).withNumberOfJunctions(3).withBlockLength(50).withDivisionLength(30)


map_config = map_builder.build()

duration = 1000

traci_loop = TraciHandler(map_config=map_config, traci_config=traci_config, duration=duration)
traci_loop.setPassengerBoundaries(2, 2)
traci_loop.doMainLoop(duration)
traci_loop.close()
