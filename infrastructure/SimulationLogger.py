import csv
import os
import threading
from datetime import datetime

class SimulationLogger:
    def __init__(self, sim_count: int, sim_type: str, log_dir: str = "logs"):
        """
        Creates a CSV logger with filename:
        SIMCOUNT_TYPE_TIMESTAMP.csv
        Example: 1_montecarlo_20251021-154530.csv
        """
        os.makedirs(log_dir, exist_ok=True)

        # Use current time as timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        # Construct filename
        self.filename = os.path.join(log_dir, f"{sim_count}_{sim_type}_{timestamp}.csv")

        # Define headers
        self.headers = ["run_id", "taxi_id", "origin_edge", "dest_edge", "distance", "price"]

        if not os.path.exists(self.filename):
            with open(self.filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

        self._lock = threading.Lock()

    def add(self, run_id: str, taxi_id: str, origin_edge: str, dest_edge: str, distance: float, price: float):
        row = [run_id, taxi_id, origin_edge, dest_edge, distance, price]
        with self._lock:
            with open(self.filename, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)