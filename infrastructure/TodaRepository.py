import traci
from collections import deque
from utils.TraciUtils import getListOfHubIds

class TodaRepository:
    """Repository for managing TODA queues in the simulation.

    Attributes:
        queues: A dictionary mapping TODA IDs to deques of tricycle IDs 
            currently in the TODA.
    """
    def __init__(self):
        """Initializes the TODA repository and sets up queues for each TODA."""
        todainmap = sorted(getListOfHubIds())
        self.queues = {toda: deque() for toda in todainmap}

    def manageTodaQueues(self) -> None:
        """Updates the TODA queues based on the current vehicles in each TODA."""
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
        """Get all TODA queues."""
        return self.queues

    def canTodaDispatch(self, queue) -> bool:
        """Check if TODA has any tricycles to dispatch.
        
        Args:
            queue: TODA ID whose queue is to be checked.
        """
        return len(self.queues[queue]) > 0

    def peekToda(self, queue) -> str:
        """Look at first tricycle in queue without removing it.

        Args:
            queue: TODA ID whose queue is to be peeked.
        """
        return self.queues[queue][0]

    def dequeToda(self, queue) -> str:
        """Remove and return first tricycle in queue.

        Args:
            queue: TODA ID whose queue is to be dequeued.
        """
        return self.queues[queue].popleft()

    def viewQueue(self, queue) -> str:
        """Get string representation of the TODA queue.

        Args:
            queue: TODA ID whose queue is to be viewed.
        """
        return f"{queue}: {list(self.queues[queue])}"