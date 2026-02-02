from .TricycleRepository import TricycleRepository
from .TraciManager import TraciManager

class TricycleSynchronizer:
    def __init__(self, tricycle_repository: TricycleRepository):
        self.tricycleRepository = tricycle_repository

    def sync(self) -> None:
        current_tricycles = set(TraciManager.getTricycleIds())
        tricycles_in_memory = set(self.tricycleRepository.getActiveTricycleIds())
        tricycles_to_kill = current_tricycles - tricycles_in_memory
        for tricycle_id in tricycles_to_kill:
            self.tricycleRepository.getTricycle(tricycle_id).kill()