import map_builder.RandomMapBuilder as mb
import tricycle_handler.Tricycle as tg
import traci_handler.TraciHandler as th

map_builder = (
    mb.RandomMapBuilder()
        .withType("spider")
        .withNumberOfJunctions(3)
        .withNumberOfDivisions(7)
        .withBlockLength(50.0)
    )
map_builder.build()

duration = 1000

traci_loop = th.TraciHandler(map_builder, duration)
traci_loop.doMainLoop(duration)
traci_loop.close()
