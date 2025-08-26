import map_builder.MapBuilder as mb
import traci

builder = (mb.MapBuilder().withType("spider").withNumberOfJunctions(5).withNumberOfDivisions(3))
builder.build()


traci.start([
    "sumo-gui",
    "-n", builder.getNetworkFilePath(),
    "-a", builder.getParkingFilePath(),
])