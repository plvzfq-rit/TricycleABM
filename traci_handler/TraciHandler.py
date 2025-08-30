import traci
import random
import passenger_handler.Passenger as ph
import map_builder.RandomMapBuilder as rmb
import tricycle_handler.Tricycle as tg

class TraciHandler:
    def __init__(self, map_builder: rmb.RandomMapBuilder, duration: int) -> None:
        self.tick = 0
        self.mapBuilder = map_builder
        self.network_file_path = map_builder.getNetworkFilePath()
        self.parking_file_path = map_builder.getParkingFilePath()
        self.passengerRepository = ph.PassengerRepository()
        self.tricycleRepository = tg.TricycleRepository()

        self.tricycleRepository.generateTricycles(self.mapBuilder.getNumberOfTricycles(), duration, self.mapBuilder.getHubDistribution())
        

    def startTraci(self) -> None:
        traci.start([
            "sumo-gui",
            "-n", self.network_file_path,
            "-a", self.parking_file_path,
        ])

    def toggleTricycles(self) -> None:
        for tricycle in self.tricycleRepository.getTricycles():
            if tricycle.startTime == self.tick:
                hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
                route_id = f"route_{tricycle.name}"
                traci.route.add(route_id, [hub_edge])
                traci.vehicle.add(tricycle.name, route_id, "trike")
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=99999)
                self.tricycleRepository.activateTricycle(tricycle.name)
            elif tricycle.endTime == self.tick:
                traci.vehicle.remove(tricycle.name)
                self.tricycleRepository.killTricycle(tricycle.name)

    def generateRandomNumberOfPassengers(self) -> None:
        LOWER_BOUND = 0
        UPPER_BOUND = 5
        number_of_passengers = random.randint(LOWER_BOUND, UPPER_BOUND)
        for _ in range(number_of_passengers):
            self.passengerRepository.generateRandomPassenger()

    def assignPassengersToTricycles(self) -> None:
        pass

    def doMainLoop(self, simulation_duration: int) -> None:
        self.startTraci()
        while self.tick < simulation_duration:
            self.passengerRepository.auditPassengers()
            self.generateRandomNumberOfPassengers()
            self.toggleTricycles()
            self.tick += 1
            traci.simulationStep()

    def close(self) -> None:
        traci.close()