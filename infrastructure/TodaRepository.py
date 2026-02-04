import traci
from collections import deque

class TodaRepository:
    def __init__(self):
        todainmap = sorted(traci.parkingarea.getIDList())
        self.queues = {toda: deque() for toda in todainmap}

    def manageTodaQueues(self) -> None:
        for toda, queue in self.queues.items():
            traci_vehicles = traci.parkingarea.getVehicleIDs(toda)
            traci_set = set(traci_vehicles)

            # 1. Remove vehicles that already left (keep order)
            self.queues[toda] = deque(
                v for v in queue if v in traci_set
            )

            # 2. Append newly arrived vehicles (in TraCI order)
            local_set = set(self.queues[toda])
            for v in traci_vehicles:
                if v not in local_set:
                    self.queues[toda].append(v)

    def getAllToda(self) -> dict:
        return self.queues

    def canTodaDispatch(self, queue) -> bool:
        return len(self.queues[queue]) > 0

    def peekToda(self, queue) -> str:
        """Look at first tricycle in queue without removing it"""
        return self.queues[queue][0]

    def dequeToda(self, queue) -> str:
        return self.queues[queue].popleft()

    def viewQueue(self, queue) -> str:
        return f"{queue}: {list(self.queues[queue])}"