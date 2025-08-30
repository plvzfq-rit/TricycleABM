import traci
import random
from passenger_handler.PassengerRepository import PassengerRepository
from map_builder.RandomMapBuilder import RandomMapBuilder
from tricycle_handler.TricycleRepository import TricycleRepository
from model.tricycle.TricycleState import TricycleState

class TraciHandler:
    def __init__(self, map_builder: RandomMapBuilder, duration: int) -> None:
        self.tick = 0
        self.mapBuilder = map_builder
        self.network_file_path = map_builder.getNetworkFilePath()
        self.parking_file_path = map_builder.getParkingFilePath()
        self.passengerRepository = PassengerRepository()
        self.tricycleRepository = TricycleRepository()

        self.tricycleRepository.generateTricycles(self.mapBuilder.getNumberOfTricycles(), duration, self.mapBuilder.getHubDistribution())
        

    def startTraci(self) -> None:
        traci.start([
            "sumo-gui",
            "-n", self.network_file_path,
            "-a", self.parking_file_path,
        ])

    def toggleTricycles(self) -> None:
        print("In SUMO:")
        print(",".join(list(traci.vehicle.getIDList())))
        print("In Memory:")
        print(",".join(list(self.tricycleRepository.activeTricycles.keys())))
        print()
        for tricycle in self.tricycleRepository.getTricycles():
            if tricycle.startTime == self.tick:
                hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
                route_id = f"route_{tricycle.name}"
                traci.route.add(route_id, [hub_edge])
                traci.vehicle.add(tricycle.name, route_id, "trike")
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=99999)
                self.tricycleRepository.activateTricycle(tricycle.name)
            elif tricycle.endTime == self.tick and tricycle.status == TricycleState.FREE:
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=0)
                traci.vehicle.remove(tricycle.name)
                self.tricycleRepository.killTricycle(tricycle.name)
            elif tricycle.status == TricycleState.BUSY and self.tricycleRepository.hasTricycleArrived(tricycle.name):
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=99999)
                self.tricycleRepository.setTricycleDestination(tricycle.name, None)
                self.tricycleRepository.setTricycleStatus(tricycle.name, TricycleState.FREE)

    def generateRandomNumberOfPassengers(self) -> None:
        LOWER_BOUND = 0
        UPPER_BOUND = 5
        number_of_passengers = random.randint(LOWER_BOUND, UPPER_BOUND)
        for _ in range(number_of_passengers):
            self.passengerRepository.generateRandomPassenger()

    def assignPassengersToTricycles(self) -> None:
        active_passenger_ids = self.passengerRepository.getActivePassengerIds()
        active_tricycles = self.tricycleRepository.getActiveTricycles()

        for active_passenger_id in active_passenger_ids:
            active_passenger_location = self.passengerRepository.getPassengerLocation(active_passenger_id)
            for active_tricycle in active_tricycles:
                active_tricycle_location = self.tricycleRepository.getTricycleLocation(active_tricycle.name)

                if active_passenger_location.isNear(active_tricycle_location) and self.tricycleRepository.isTricycleFree(active_tricycle.name):
                    self.passengerRepository.killPassenger(active_passenger_id)
                    self.tricycleRepository.assignPassengerToTricycle(active_tricycle.name, active_passenger_location)
                    break


    def doMainLoop(self, simulation_duration: int) -> None:
        self.startTraci()
        while self.tick < simulation_duration:
            self.passengerRepository.auditPassengers()
            self.generateRandomNumberOfPassengers()
            self.toggleTricycles()
            self.assignPassengersToTricycles()
            self.tick += 1
            traci.simulationStep()

    def close(self) -> None:
        traci.close()