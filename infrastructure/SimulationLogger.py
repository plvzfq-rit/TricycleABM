import csv
import os
import threading
from datetime import datetime

class SimulationLogger:
    def __init__(self, sim_count: int, log_dir: str = "logs"):
        """
        Creates a CSV logger with filename:
        SIMCOUNT_TIMESTAMP/transactions.csv
        """
        # Use current time as timestamp
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

        run_dir = os.path.join(log_dir, f"{sim_count}_{timestamp}")
        os.makedirs(run_dir, exist_ok=True)

        # Construct filename
        self.filename = os.path.join(run_dir, f"transactions.csv")
        self.filedirectory = run_dir

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

    def addDriverInfo(self, tricycles: list):
        drivers_path = os.path.join(os.path.dirname(self.filename), "drivers.csv")
        drivers_path = os.path.normpath(drivers_path)
        with self._lock:
            with open(drivers_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                for tricycle in tricycles:
                    writer.writerow([tricycle.name, tricycle.hub, tricycle.startTime, tricycle.endTime])

    def getDirectory(self):
        return self.filedirectory