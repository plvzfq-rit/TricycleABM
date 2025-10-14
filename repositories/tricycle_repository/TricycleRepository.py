import random
import traci
import uuid
import sumolib

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
            lower_max_gas = 50.0
            upper_max_gas = 52.0
            max_gas = lower_max_gas + (upper_max_gas - lower_max_gas) * random.random()
            gas_consumption = random.random()
            gas_threshold = max_gas * random.random()
            tricycle = Tricycle(trike_name, hubs.pop(), start_time, end_time, max_gas, gas_consumption, gas_threshold)
            self.tricycles[trike_name] = tricycle

        # for _ in self.tricycles.values():
        #     print(_)

    def killTricycle(self, tricycle_id: str) -> None:
        self.setTricycleStatus(tricycle_id, TricycleState.DEAD)
        # self.killedTricycles[tricycle_id] = self.tricycles[tricycle_id]
        # if tricycle_id in self.activeTricycles.keys():
        #     del self.activeTricycles[tricycle_id]

    def activateTricycle(self, tricycle_id: str) -> None:
        # self.activeTricycles[tricycle_id] = self.tricycles[tricycle_id]
        self.tricycles[tricycle_id].status = TricycleState.FREE

    def getTricycles(self) -> list[Tricycle]:
        return list(self.tricycles.values())
    
    def getActiveTricycles(self) -> list[Tricycle]:
        return set([tricycle for tricycle in self.tricycles.values() if tricycle.status not in [TricycleState.DEAD, TricycleState.TO_SPAWN]])
    
    def getTricycleLocation(self, tricycle_id: str) -> Location:
        current_edge = traci.vehicle.getRoadID(tricycle_id)
        current_position = traci.vehicle.getLanePosition(tricycle_id)
        return Location(current_edge, current_position)
    
    def setTricycleStatus(self, tricycle_id: str, status: TricycleState) -> None:
        if tricycle_id in self.tricycles.keys():
            self.tricycles[tricycle_id].status = status
        # if tricycle_id in self.activeTricycles.keys():
        #     self.activeTricycles[tricycle_id].status = status
        # if tricycle_id in self.killedTricycles.keys():
        #     self.killedTricycles[tricycle_id].status = status

    def setTricycleDestination(self, tricycle_id: str, destination: Location) -> None:
        if tricycle_id in self.tricycles.keys():
            self.tricycles[tricycle_id].destination = destination
        # if tricycle_id in self.activeTricycles.keys():
        #     self.activeTricycles[tricycle_id].destination = destination
        # if tricycle_id in self.killedTricycles.keys():
        #     self.killedTricycles[tricycle_id].destination = destination
    
    def assignPassengerToTricycle(self, tricycle_id: str, destination: Location, traci_config) -> bool:
        tricycle = self.tricycles[tricycle_id]

        hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
        dest_edge = destination.location
        current_edge = traci.vehicle.getRoadID(tricycle_id)

        if current_edge == dest_edge:
            #print("Failed to assign.")
            return False

        net = sumolib.net.readNet(traci_config.getNetworkFilePath())
        edge = net.getEdge(dest_edge)
        if edge.getLaneNumber() <= 1:
            return False

        traci.vehicle.setParkingAreaStop(tricycle_id, self.tricycles[tricycle_id].hub, duration=0)

        to_route = traci.simulation.findRoute(current_edge, dest_edge)
        return_route = traci.simulation.findRoute(dest_edge, hub_edge)

        full_route = list(to_route.edges) + list(return_route.edges)[1:]
        # print("Created route: " + str(full_route))

        traci.vehicle.setRoute(tricycle_id, full_route)

        traci.vehicle.setStop(tricycle_id, dest_edge, laneIndex=1, pos=destination.position, duration=10)

        self.setTricycleStatus(tricycle_id, TricycleState.HAS_PASSENGER)
        self.setTricycleDestination(tricycle_id, destination)

        return True

    def hasTricycleArrived(self, tricycle_id: str) -> bool:
        return self.tricycles[tricycle_id].hasArrived()
    
    def isTricycleFree(self, tricycle_id: str) -> bool:
        return self.tricycles[tricycle_id].status == TricycleState.FREE
    
    def toggleTricycles(self, current_tick: int) -> None:
        for tricycle in self.getTricycles():
            if tricycle.startTime == current_tick and tricycle.status == TricycleState.TO_SPAWN:
                hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
                route_id = f"route_{tricycle.name}"
                traci.route.add(route_id, [hub_edge])
                traci.vehicle.add(tricycle.name, route_id, "trike")
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=99999)
                self.activateTricycle(tricycle.name)


            elif tricycle.endTime == current_tick and tricycle.status == TricycleState.FREE:
                traci.vehicle.remove(tricycle.name)
                self.killTricycle(tricycle.name)
            elif tricycle.status == TricycleState.HAS_PASSENGER and self.hasTricycleArrived(tricycle.name):
                hub_edge = traci.parkingarea.getLaneID(tricycle.hub).split("_")[0]
                # traci.vehicle.changeTarget(tricycle.name, hub_edge)
                traci.vehicle.setParkingAreaStop(tricycle.name, tricycle.hub, duration=99999)
                self.setTricycleDestination(tricycle.name, None)
                self.setTricycleStatus(tricycle.name, TricycleState.FREE)

    def syncTricycles(self) -> None:
        current_tricycles = set([tricycle_id for tricycle_id in list(traci.vehicle.getIDList()) if tricycle_id.startswith('trike')])
        tricycles_in_memory = set([tricycle_id for tricycle_id in self.tricycles.keys() if self.tricycles[tricycle_id].status not in [TricycleState.DEAD, TricycleState.TO_SPAWN]])
        tricycles_to_kill = current_tricycles - tricycles_in_memory
        for tricycle_id in tricycles_to_kill:
            self.killTricycle(tricycle_id)
        for tricycle_id in tricycles_in_memory:
            current_edge = traci.vehicle.getRoadID(tricycle_id)
            current_position = traci.vehicle.getLanePosition(tricycle_id)
            current_location = Location(current_edge, current_position)
            # print(str(current_location))

            if current_edge == '':
                self.setTricycleStatus(tricycle_id, TricycleState.PARKED)
                self.tricycles[tricycle_id].lastLocation = current_location
            else:
                has_consumed = self.simulateConsumption(tricycle_id, current_location)

                if not has_consumed:
                    self.killTricycle(tricycle_id)
                    print(tricycle_id, "has run out of gas")
                else:
                    self.tricycles[tricycle_id].lastLocation = current_location
            
    def simulateConsumption(self, tricycle_id: str, current_location: Location) -> None:
        distance_travelled = current_location.distanceTo(self.tricycles[tricycle_id].lastLocation)
        if tricycle_id in self.tricycles.keys():
            return self.tricycles[tricycle_id].consumeGas(distance_travelled)