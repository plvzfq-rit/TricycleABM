from map_builder.RandomMapBuilder import RandomMapBuilder
from traci_handler.TraciHandler import TraciHandler
from model.traci_config.TraciConfig import TraciConfig
from model.map_config.MapConfig import MapConfig

traci_config = TraciConfig()
# map_config = MapConfig()

map_builder = (
    RandomMapBuilder().withType("spider").withNumberOfJunctions(3).withNumberOfDivisions(3).withBlockLength(50.0).withDivisionLength(50.0)
    )
map_config = map_builder.build()

duration = 1000

traci_loop = TraciHandler(map_config=map_config, traci_config=traci_config, duration=duration)
traci_loop.setPassengerBoundaries(2, 2)
traci_loop.doMainLoop(duration)
traci_loop.close()
