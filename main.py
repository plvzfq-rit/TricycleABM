import map_builder.RandomMapBuilder as mb
import traci

builder = (mb.RandomMapBuilder().withType("spider").withNumberOfJunctions(10).withNumberOfDivisions(7))
builder.build()



traci.start([
    "sumo-gui",
    "-n", builder.getNetworkFilePath(),
    "-a", builder.getParkingFilePath(),
])