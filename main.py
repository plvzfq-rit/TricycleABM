from map_builder.RandomMapBuilder import RandomMapBuilder
from traci_handler.TraciHandler import TraciHandler

map_builder = (
    RandomMapBuilder()
        .withType("spider")
        .withNumberOfJunctions(3)
        .withNumberOfDivisions(3)
        .withBlockLength(40.0)
        .withParkings(10)
    )
map_builder.build()

duration = 1000

traci_loop = TraciHandler(map_builder, duration)
traci_loop.setPassengerBoundaries(10, 10)
traci_loop.doMainLoop(duration)
traci_loop.close()
