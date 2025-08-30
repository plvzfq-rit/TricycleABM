from map_builder.RandomMapBuilder import RandomMapBuilder
from traci_handler.TraciHandler import TraciHandler

map_builder = (
    RandomMapBuilder()
        .withType("spider")
        .withNumberOfJunctions(3)
        .withNumberOfDivisions(7)
        .withBlockLength(50.0)
    )
map_builder.build()

duration = 200

traci_loop = TraciHandler(map_builder, duration)
traci_loop.doMainLoop(duration)
traci_loop.close()
