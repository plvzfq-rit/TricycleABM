from application.SpecificMapBuilder import SpecificMapBuilder
from application.RandomMapBuilder import RandomMapBuilder
from handlers.TraciHandler import TraciHandler
from config.TraciConfig import TraciConfig

from infrastructure.ParkingAreaParser import ParkingAreaParser
from infrastructure.FileSystemDescriptor import FileSystemDescriptor
from infrastructure.FileSyncService import FileSyncService

traci_config = TraciConfig()
file_system_descriptor = FileSystemDescriptor()
parking_area_parser = ParkingAreaParser()
file_sync_service = FileSyncService()

map_builder = SpecificMapBuilder(traci_config, file_system_descriptor, parking_area_parser, file_sync_service)
#map_builder = RandomMapBuilder().withType("spider").withParkings(5).withNumberOfDivisions(3).withNumberOfJunctions(3).withBlockLength(50).withDivisionLength(30)


map_config = map_builder.build()

duration = 1080

traci_loop = TraciHandler(map_config=map_config, traci_config=traci_config, duration=duration)
traci_loop.setPassengerBoundaries(2, 2)
traci_loop.doMainLoop(duration)
traci_loop.close()
