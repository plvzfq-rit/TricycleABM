import csv
import os
import threading
from datetime import datetime

class SimulationLogger:
    def __init__(self, sim_count: int, log_dir: str = "analysis"):
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
        self.headers = ["run_id", "trike_id", "origin_edge", "dest_edge", "distance", "price", "tick", "driver_asp", "passenger_asp"]

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

        # Trip acceptance/rejection counters
        self.accepted_trips = 0
        self.rejected_trips = 0

    #include the driver's willingness to sell and passenger's willingness to pay
    def add(self, run_id: str, taxi_id: str, origin_edge: str, dest_edge: str, distance: float, price: float, tick:int, driver_asp: float, passenger_asp: float) -> None:
        row = [run_id, taxi_id, origin_edge, dest_edge, distance, price, tick, driver_asp, passenger_asp]
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

    def recordAcceptedTrip(self):
        with self._lock:
            self.accepted_trips += 1

    def recordRejectedTrip(self):
        with self._lock:
            self.rejected_trips += 1

    def writeTripSummary(self):
        summary_path = os.path.join(self.filedirectory, "trip_summary.csv")
        with self._lock:
            with open(summary_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["metric", "count"])
                writer.writerow(["accepted_trips", self.accepted_trips])
                writer.writerow(["rejected_trips", self.rejected_trips])
                total = self.accepted_trips + self.rejected_trips
                writer.writerow(["total_attempts", total])

    def getDirectory(self):
        return self.filedirectory