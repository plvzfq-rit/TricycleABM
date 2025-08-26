import map_builder.MapBuilder as mb
import traci

new_map = mb.MapBuilder().withType("grid").withNumberOfBlocks(3).withNumberOfDivisions(7).withBlockLength(30).build()

traci.start([
    "sumo-gui",
    "-n", "maps/net.net.xml",
    "-a", "maps/parking.add.xml"
])