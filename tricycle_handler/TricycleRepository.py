import random
import traci

from model.location.Location import Location
from model.tricycle.Tricycle import Tricycle
from model.tricycle.TricycleState import TricycleState

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

    def killTricycle(self, tricycle_id: str) -> None:
        self.killedTricycles[tricycle_id] = self.tricycles[tricycle_id]
        del self.activeTricycles[tricycle_id]

    def activateTricycle(self, tricycle_id: str) -> None:
        self.activeTricycles[tricycle_id] = self.tricycles[tricycle_id]

    def getTricycles(self) -> list[Tricycle]:
        return list(self.tricycles.values())
    
    def getActiveTricycles(self) -> list[Tricycle]:
        return set(self.activeTricycles.values())
    
    def getTricycleLocation(self, tricycle_id: str) -> Location:
        return Location(traci.vehicle.getRoadID(tricycle_id), traci.person.getLanePosition(tricycle_id))
    
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
    
    def assignPassengerToTricycle(self, tricycle_id: str, destination: Location) -> None:
        traci.vehicle.resume(tricycle_id)
        traci.vehicle.changeTarget(tricycle_id, destination.location)
        self.setTricycleStatus(tricycle_id, TricycleState.BUSY)
        self.setTricycleDestination(tricycle_id, destination)

    def hasTricycleArrived(self, tricycle_id: str) -> bool:
        return self.tricycles[tricycle_id].hasArrived()
    
    def isTricycleFree(self, tricycle_id: str) -> bool:
        return self.tricycles[tricycle_id].status == TricycleState.FREE