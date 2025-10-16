import random
import traci
import uuid

from domain.Location import Location
from domain.Tricycle import Tricycle
from domain.TricycleFactory import TricycleFactory
from domain.TricycleState import TricycleState
from infrastructure.SumoService import SumoService
from infrastructure.TraciService import TraciService


class TricycleRepository:
    def __init__(self, tricycle_factory: TricycleFactory | None = None, traci_service: TraciService | None = None):
        self.tricycles = dict()
        self.tricycleFactory = tricycle_factory or TricycleFactory()
        self.traciService = traci_service or TraciService()

    def createTricycles(self, number_of_tricycles: int, simulation_duration: int, hub_distribution: dict) -> None:
        # create list of hub tags; each would be assigned to a new tricycle
        hubs = []
        for hub, number_of_tricycles_in_hub in hub_distribution.items():
            for i in range(number_of_tricycles_in_hub):
                hubs.append(hub)

        for i in range(number_of_tricycles):
            assigned_hub = hubs.pop()
            assigned_id = i
            trike_name, tricycle = self.tricycleFactory.createRandomTricycle(assigned_id, simulation_duration, assigned_hub)
            self.tricycles[trike_name] = tricycle

    def getTricycle(self, tricycle_id: str) -> Tricycle:
        return self.tricycles[tricycle_id]
    
    def getTricycles(self) -> list[Tricycle]:
        return list(self.tricycles.values())

    def killTricycle(self, tricycle_id: str) -> None:
        self.getTricycle(tricycle_id).kill()

    def activateTricycle(self, tricycle_id: str) -> None:
        self.getTricycle(tricycle_id).activate()
    
    def getActiveTricycles(self) -> set[Tricycle]:
        return set([tricycle for tricycle in self.tricycles.values() if tricycle.isActive()])
    
    def getTricycleLocation(self, tricycle_id: str) -> Location:
        return self.traciService.getTricycleLocation(tricycle_id)
    
    def setTricycleDestination(self, tricycle_id: str, destination: Location) -> None:
        if tricycle_id in self.tricycles.keys():
            self.getTricycle(tricycle_id).setDestination(destination)
    
    def assignPassengerToTricycle(self, tricycle_id: str, destination: Location, traci_config) -> bool:
        tricycle = self.tricycles[tricycle_id]

        hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
        dest_edge = destination.location
        current_edge = traci.vehicle.getRoadID(tricycle_id)

        if current_edge == dest_edge:
            #print("Failed to assign.")
            return False

        net = SumoService.getNetwork(traci_config.getNetworkFilePath())
        edge = net.getEdge(dest_edge)
        if edge.getLaneNumber() <= 1:
            return False

        traci.vehicle.setParkingAreaStop(tricycle_id, self.tricycles[tricycle_id].hub, duration=0)

        to_route = traci.simulation.findRoute(current_edge, dest_edge)
        return_route = traci.simulation.findRoute(dest_edge, hub_edge)

        full_route = list(to_route.edges) + list(return_route.edges)[1:]

        traci.vehicle.setRoute(tricycle_id, full_route)

        traci.vehicle.setStop(tricycle_id, dest_edge, laneIndex=1, pos=destination.position, duration=10)

        self.setTricycleState(tricycle_id, TricycleState.HAS_PASSENGER)
        self.setTricycleDestination(tricycle_id, destination)

        return True

    def hasTricycleArrived(self, tricycle_id: str) -> bool:
        return self.getTricycle(tricycle_id).hasArrived()
    
    def isTricycleFree(self, tricycle_id: str) -> bool:
        return self.getTricycle(tricycle_id).isFree()
    
    def simulateConsumption(self, tricycle_id: str) -> None:
        if tricycle_id in self.tricycles.keys():
            current_location = self.traciService.getTricycleLocation(tricycle_id)
            return self.getTricycle(tricycle_id).consumeGas(current_location)
    
    def toggleTricycles(self, current_tick: int) -> None:
        for tricycle in self.getTricycles():
            if tricycle.startTime == current_tick and tricycle.state == TricycleState.TO_SPAWN:
                hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
                route_id = f"route_{tricycle.name}"
                traci.route.add(route_id, [hub_edge])
                traci.vehicle.add(tricycle.name, route_id, "trike")
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=99999)
                self.activateTricycle(tricycle.name)


            elif tricycle.endTime == current_tick and tricycle.state == TricycleState.FREE:
                traci.vehicle.remove(tricycle.name)
                self.killTricycle(tricycle.name)
            elif tricycle.state == TricycleState.HAS_PASSENGER and self.hasTricycleArrived(tricycle.name):
                hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
                # traci.vehicle.changeTarget(tricycle.name, hub_edge)
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=99999)
                self.setTricycleDestination(tricycle.name, None)
                self.setTricycleState(tricycle.name, TricycleState.FREE)

    def syncTricycles(self) -> None:
        current_tricycles = set([tricycle_id for tricycle_id in list(traci.vehicle.getIDList()) if tricycle_id.startswith('trike')])
        tricycles_in_memory = set([tricycle_id for tricycle_id in self.tricycles.keys() if self.tricycles[tricycle_id].state not in [TricycleState.DEAD, TricycleState.TO_SPAWN]])
        tricycles_to_kill = current_tricycles - tricycles_in_memory
        for tricycle_id in tricycles_to_kill:
            self.killTricycle(tricycle_id)
        for tricycle_id in tricycles_in_memory:
            current_edge = traci.vehicle.getRoadID(tricycle_id)
            current_position = traci.vehicle.getLanePosition(tricycle_id)
            current_location = Location(current_edge, current_position)

            if current_edge == '':
                self.setTricycleState(tricycle_id, TricycleState.PARKED)
                self.tricycles[tricycle_id].lastLocation = current_location
            else:
                has_consumed = self.simulateConsumption(tricycle_id, current_location)

                if not has_consumed:
                    self.killTricycle(tricycle_id)
                    print(tricycle_id, "has run out of gas")
                else:
                    self.tricycles[tricycle_id].lastLocation = current_location

                # if self.tricycles[tricycle_id].currentGas <= self.tricycles[tricycle_id].gasThreshold:


