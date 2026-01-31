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
        self.transactions_filename = os.path.join(run_dir, f"transactions.csv")
        self.filedirectory = run_dir

        self.expenses_filename = os.path.join(run_dir, f"expenses.csv")

        # Define headers
        self.headers = ["run_id", "trike_id", "origin_edge", "dest_edge", "distance", "price", "tick"]

        if not os.path.exists(self.transactions_filename):
            with open(self.transactions_filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

        expense_headers = ["trike_id", "expense_type", "amount", "tick"]
        if not os.path.exists(self.expenses_filename):
            with open(self.expenses_filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(expense_headers)

        self._lock = threading.Lock()

    def add(self, run_id: str, taxi_id: str, origin_edge: str, dest_edge: str, distance: float, price: float, tick:int):
        row = [run_id, taxi_id, origin_edge, dest_edge, distance, price, tick]
        with self._lock:
            with open(self.transactions_filename, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def addDriverInfo(self, tricycles: list):
        drivers_path = os.path.join(os.path.dirname(self.transactions_filename), "drivers.csv")
        drivers_path = os.path.normpath(drivers_path)
        header = ["trike_id", "hub_id", "start_tick", "end_tick", "actual_start_tick", "actual_end_tick", "actual_duration", "daily_trips", "daily_income", "daily_distance"]

        with self._lock:
            with open(drivers_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                for tricycle in tricycles:
                    daily_stats = tricycle.getDailyStats()
                    writer.writerow([
                        tricycle.name,
                        tricycle.hub,
                        tricycle.startTime,
                        tricycle.endTime,
                        tricycle.actualStartTick,
                        tricycle.actualEndTick,
                        daily_stats['actual_duration'],
                        daily_stats['trips'],
                        daily_stats['income'],
                        daily_stats['distance']
                    ])

    def addExpenseToLog(self, tricycleId: str, expensetype: str, amount: float, tick: int) -> None:
        with self._lock:
            with open(self.expenses_filename, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([tricycleId, expensetype, amount, tick])

    def getDirectory(self):
        return self.filedirectory