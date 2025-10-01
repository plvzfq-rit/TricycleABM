import random
import traci
import uuid

from domain.location.Location import Location
from domain.tricycle.Tricycle import Tricycle
from domain.tricycle.TricycleState import TricycleState

class TricycleRepository:
    def __init__(self):
        self.tricycles = dict()
        self.activeTricycles = dict()
        self.busyTricycles = dict()
        self.killedTricycles = dict()

    def generateTricycles(self, number_of_tricycles: int, simulation_duration: int, hub_distribution: dict) -> None:
        hubs = []
        for hub, number_of_tricycles_in_hub in hub_distribution.items():
            for i in range(number_of_tricycles_in_hub):
                hubs.append(hub)

        for i in range(number_of_tricycles):
            trike_name = "trike" + str(i)
            start_time = random.randint(0, simulation_duration // 2)
            end_time = random.randint(start_time, simulation_duration)
            tricycle = Tricycle(trike_name, hubs.pop(), start_time, end_time)
            self.tricycles[trike_name] = tricycle

        for _ in self.tricycles.values():
            print(_)

    def killTricycle(self, tricycle_id: str) -> None:
        self.setTricycleStatus(tricycle_id, TricycleState.FREE)
        self.killedTricycles[tricycle_id] = self.tricycles[tricycle_id]
        del self.activeTricycles[tricycle_id]

    def activateTricycle(self, tricycle_id: str) -> None:
        self.activeTricycles[tricycle_id] = self.tricycles[tricycle_id]

    def getTricycles(self) -> list[Tricycle]:
        return list(self.tricycles.values())
    
    def getActiveTricycles(self) -> list[Tricycle]:
        return set(self.activeTricycles.values())
    
    def getTricycleLocation(self, tricycle_id: str) -> Location:
        current_edge = traci.vehicle.getRoadID(tricycle_id)
        current_position = traci.vehicle.getLanePosition(tricycle_id)
        return Location(current_edge, current_position)
    
    def setTricycleStatus(self, tricycle_id: str, status: TricycleState) -> None:
        if tricycle_id in self.tricycles.keys():
            self.tricycles[tricycle_id].status = status
        if tricycle_id in self.activeTricycles.keys():
            self.activeTricycles[tricycle_id].status = status
        if tricycle_id in self.killedTricycles.keys():
            self.killedTricycles[tricycle_id].status = status

    def setTricycleDestination(self, tricycle_id: str, destination: Location) -> None:
        if tricycle_id in self.tricycles.keys():
            self.tricycles[tricycle_id].destination = destination
        if tricycle_id in self.activeTricycles.keys():
            self.activeTricycles[tricycle_id].destination = destination
        if tricycle_id in self.killedTricycles.keys():
            self.killedTricycles[tricycle_id].destination = destination
    
    def assignPassengerToTricycle(self, tricycle_id: str, destination: Location) -> bool:
        tricycle = self.tricycles[tricycle_id]

        hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
        dest_edge = destination.location
        current_edge = traci.vehicle.getRoadID(tricycle_id)

        if current_edge == dest_edge:
            print("Failed to assign.")
            return False

        traci.vehicle.setParkingAreaStop(tricycle_id, self.tricycles[tricycle_id].hub, duration=0)

        to_route = traci.simulation.findRoute(current_edge, dest_edge)
        return_route = traci.simulation.findRoute(dest_edge, hub_edge)

        full_route = list(to_route.edges) + list(return_route.edges)[1:]
        # print("Created route: " + str(full_route))

        traci.vehicle.setRoute(tricycle_id, full_route)

        traci.vehicle.setStop(tricycle_id, dest_edge, laneIndex=1, pos=destination.position, duration=10)

        self.setTricycleStatus(tricycle_id, TricycleState.BUSY)
        self.setTricycleDestination(tricycle_id, destination)
        # print("Assigned with built-in return route:", tricycle, "with return route: ", str(full_route))
        # print("Assign Trike", tricycle_id, 
        # "edge:", traci.vehicle.getRoadID(tricycle_id), 
        # "route:", traci.vehicle.getRoute(tricycle_id), 
        # "stopstate:", traci.vehicle.getStopState(tricycle_id), 
        # "speed:", traci.vehicle.getSpeed(tricycle_id))
        # traci.vehicle.resume(tricycle_id)

        return True

    def hasTricycleArrived(self, tricycle_id: str) -> bool:
        return self.tricycles[tricycle_id].hasArrived()
    
    def isTricycleFree(self, tricycle_id: str) -> bool:
        return self.tricycles[tricycle_id].status == TricycleState.FREE
    
    def toggleTricycles(self, current_tick: int) -> None:
        for tricycle in self.getTricycles():
            if tricycle.startTime == current_tick:
                hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
                route_id = f"route_{tricycle.name}"
                traci.route.add(route_id, [hub_edge])
                traci.vehicle.add(tricycle.name, route_id, "trike")
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=99999)
                self.activateTricycle(tricycle.name)
            elif tricycle.endTime == current_tick and tricycle.status == TricycleState.FREE:
                traci.vehicle.remove(tricycle.name)
                self.killTricycle(tricycle.name)
            elif tricycle.status == TricycleState.BUSY and self.hasTricycleArrived(tricycle.name):
                hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
                # traci.vehicle.changeTarget(tricycle.name, hub_edge)
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=99999)
                self.setTricycleDestination(tricycle.name, None)
                self.setTricycleStatus(tricycle.name, TricycleState.FRgiEE)

    def syncTricycles(self) -> None:
        current_tricycles = set([tricycle_id for tricycle_id in list(traci.vehicle.getIDList()) if tricycle_id.startswith('trike')])
        tricycles_in_memory = set(self.activeTricycles.keys())
        tricycles_to_kill = current_tricycles - tricycles_in_memory
        for tricycle_id in tricycles_to_kill:
            self.killTricycle(tricycle_id)