import random
from domain.MapDescriptor import MapDescriptor
from infrastructure.SumoService import SumoService
class ParkingFileGenerator:
    def __init__(self, sumo_service: SumoService | None):
        self.sumoService = sumo_service or SumoService()

    def createParkingFile(self, network_file_path:str, parking_file_path: str, number_of_parking: int) -> MapDescriptor:
        map_descriptor = MapDescriptor()
        network = self.sumoService.getNetwork(network_file_path)
        output_file = parking_file_path

        edges = list(network.getEdges())
        random_edges = random.sample(edges, number_of_parking)

        with open(output_file, "w") as file:
            file.write("<additional>\n")

            # Put in custom tricycle and passenger types
            file.write("<vType id=\"trike\" accel=\"0.8\" decel=\"4.5\" sigma=\"0.5\" length=\"2.5\" maxSpeed=\"10.0\" guiShape=\"bicycle\"/>\n")
            file.write(f"<vType id=\"fatPed\" vClass=\"pedestrian\" guiShape=\"pedestrian\" color=\"yellow\" width=\"1\" length=\"1\"/>\n")

            for i, edge in enumerate(random_edges):
                lane = edge.getLanes()[1]  
                lane_id = lane.getID()
                lane_length = lane.getLength()

                start_pos = 5
                end_pos = min(25, lane_length - 1)

                file.write(f"\t<parkingArea id=\"hub{i}\" lane=\"{lane_id}\" startPos=\"{start_pos}\" endPos=\"{end_pos}\" lines=\"3\" roadsideCapacity=\"3\"/>\n")

                map_descriptor.addHub(f"hub{i}", 3)

            file.write("</additional>\n")
        
        print(f"Wrote parking areas to {parking_file_path}")
        return map_descriptor