from infrastructure.TricycleRepository import TricycleRepository
from infrastructure.TraciService import TraciService

class TricycleSynchronizer:
    def __init__(self, tricycle_repository: TricycleRepository | None = None, traci_service: TraciService | None = None):
        self.tricycleRepository = tricycle_repository
        self.traciService = traci_service

    def sync(self) -> None:
        current_tricycles = set(self.traciService.getTricycleIds())
        tricycles_in_memory = set(self.tricycleRepository.getActiveTricycleIds())
        tricycles_to_kill = current_tricycles - tricycles_in_memory
        for tricycle_id in tricycles_to_kill:
            self.tricycleRepository.getTricycle(tricycle_id).kill()