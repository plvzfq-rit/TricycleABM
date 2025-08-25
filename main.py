import map_builder.MapBuilder as mb

new_map = mb.MapBuilder()
new_map.withType("spider").withNumberOfBlocks(3).withNumberOfDivisions(7).withBlockLength(30).build()