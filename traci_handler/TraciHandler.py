import traci
import random
import passenger_handler.Passenger as ph

class TraciHandler:
    def __init__(self, network_file_path: str, parking_file_path: str, tricycles: set) -> None:
        self.tricycles = tricycles
        self.network_file_path = network_file_path
        self.parking_file_path = parking_file_path
        self.passengerGenerator = ph.PassengerGenerator()
        self.tick = 0

    def startTraci(self) -> None:
        traci.start([
            "sumo-gui",
            "-n", self.network_file_path,
            "-a", self.parking_file_path,
        ])

    def toggleTricycles(self) -> None:
        to_remove = set()
        for tricycle in self.tricycles:
            if tricycle.startTime == self.tick:
                hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
                route_id = f"route_{tricycle.name}"
                traci.route.add(route_id, [hub_edge])
                traci.vehicle.add(tricycle.name, route_id, "trike")
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=99999)
            elif tricycle.endTime == self.tick:
                traci.vehicle.remove(tricycle.name)
                to_remove.add(tricycle)
        self.tricycles = [tricycle for tricycle in self.tricycles if tricycle not in to_remove]

    def generateRandomNumberOfPassengers(self) -> None:
        number_of_passengers = random.randint(0, 5)
        for _ in range(number_of_passengers):
            self.passengerGenerator.generateRandomPassenger()

    def doMainLoop(self, simulation_duration: int) -> None:
        self.startTraci()
        while self.tick < simulation_duration:
            self.passengerGenerator.auditPassengers()
            self.generateRandomNumberOfPassengers()
            self.toggleTricycles()
            self.tick += 1
            traci.simulationStep()

    def close(self) -> None:
        traci.close()