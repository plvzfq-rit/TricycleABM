"""Module for managing TODA queue management in the simulation.

Provides the TodaRepository class which maintains queues of tricycles
automatically assigned to each TODA hub.
"""

import traci
from collections import deque
from utils.TraciUtils import getListOfHubIds


class TodaRepository:
    """Manager for TODA queues and tricycle dispatch ordering.
    
    Maintains FIFO queues for each TODA hub for realistic dispatch.
    Also updates queue from current SUMO network data.

    :ivar queues: Dictionary mapping TODA hub IDs to deques of tricycle IDs.
    """
    
    def __init__(self) -> None:
        """Initialize by creating empty queues for all TODA hubs.
        """
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

    def canTodaDispatch(self, queue: str) -> bool:
        """Check if a TODA hub is not empty.
        
        :param queue: TODA hub to check.
        :type queue: str
        :return: True if the queue has at least one tricycle, False otherwise.
        :rtype: bool
        """
        return len(self.queues[queue]) > 0

    def peekToda(self, queue: str) -> str:
        """Get the first tricycle in a TODA queue.
        
        :param queue: TODA hub to query.
        :type queue: str
        :return: ID of tricycle in front of queue.
        :rtype: str
        """
        return self.queues[queue][0]

    def dequeToda(self, queue: str) -> str:
        """Remove and return the first tricycle from a TODA queue, for dispatch
        
        :param queue: TODA hub to dequeue from.
        :type queue: str
        :return: ID of tricycle removed from the queue.
        :rtype: str
        """
        return self.queues[queue].popleft()