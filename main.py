from map_builder.RandomMapBuilder import RandomMapBuilder
from traci_handler.TraciHandler import TraciHandler

map_builder = (
    RandomMapBuilder()
    )

duration = 1000

traci_loop = TraciHandler(map_builder, duration)
traci_loop.setPassengerBoundaries(2, 2)
traci_loop.doMainLoop(duration)
traci_loop.close()
