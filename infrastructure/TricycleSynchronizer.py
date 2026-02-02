from .TricycleRepository import TricycleRepository
from .TraciUtils import getTricycleIds

class TricycleSynchronizer:
    """Synchronizer between Python/Traci program and Sumo simulation
    
    This is responsible for making sure that the tricycles inside the Python 
    program (as provided by a given TricycleRepository object) have the same 
    information as in the Sumo simulation.
    
    Attributes:
        tricycleRepository: TricycleRepository object.
        """
    def __init__(self, tricycle_repository: TricycleRepository):
        """Initializes the instance given a tricycle repository.
        
        Args:
            tricycle_repository: TricycleRepository object
        """
        self.tricycleRepository = tricycle_repository

    def sync(self) -> None:
        """Synchronizes information between the Sumo simulation and the Python 
        program (via tricycleRepository).
        """
        current_tricycles = set(getTricycleIds())
        tricycles_in_memory = set(self.tricycleRepository.getActiveTricycleIds())
        tricycles_to_kill = current_tricycles - tricycles_in_memory
        for tricycle_id in tricycles_to_kill:
            self.tricycleRepository.getTricycle(tricycle_id).kill()