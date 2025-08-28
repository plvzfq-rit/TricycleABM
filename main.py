import map_builder.RandomMapBuilder as mb
import tricycle_handler.TricycleGenerator as tg
import traci_handler.TraciHandler as th

builder = (mb.RandomMapBuilder().withType("spider").withNumberOfJunctions(3).withNumberOfDivisions(7).withBlockLength(50.0))
builder.build()

duration = 1000

gen = tg.TricycleGenerator()
gen.generateTricycles(builder.getNumberOfTricycles(), duration, builder.getHubDistribution())

traci_loop = th.TraciHandler(builder.getNetworkFilePath(), builder.getParkingFilePath(), gen.spawnedTricycles)
traci_loop.doMainLoop(duration)
traci_loop.close()
