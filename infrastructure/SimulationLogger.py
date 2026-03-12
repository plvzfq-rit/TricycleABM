"""Module for logging a singular run data to a folder of CSVs.

This module provides the SimulationLogger class which handles all data
logging for a single simulation run, including transaction records, 
expense tracking, and driver data.
"""

import csv
import os
import threading


class SimulationLogger:
    """Logger for recording simulation data to CSV files.
    
    Manages thread-safe writing of transaction data, expenses, driver statistics,
    and trip summaries to CSV files in a run-specific directory.
    
    :ivar transactions_filename: Path to transactions CSV file.
    :ivar expenses_filename: Path to expenses CSV file.
    :ivar filedirectory: Directory where log files are stored.
    :ivar headers: List of column names for transaction records.
    :ivar accepted_trips: Number of accepted trip requests.
    :ivar rejected_trips: Number of rejected trip requests.
    """
    
    def __init__(self, sim_count: int, log_dir: str = "analysis") -> None:
        """Initialize the logger.
        
        Creates the necessary CSV files with headers if they don't exist.
        Sets up a thread lock for safe concurrent writes.
        
        :param sim_count: Simulation run number.
        :type sim_count: int
        :param log_dir: Root directory for logs. Defaults to "analysis" folder.
        :type log_dir: str
        """
        run_dir = os.path.join(log_dir, str(sim_count))
        os.makedirs(run_dir, exist_ok=True)

        # Construct filename
        self.transactions_filename = os.path.join(run_dir, f"transactions.csv")
        self.filedirectory = run_dir

        self.expenses_filename = os.path.join(run_dir, f"expenses.csv")

        # Define headers
        self.headers = ["run_id", "trike_id", "origin_edge", "dest_edge", "distance", 
                       "price", "tick", "driver_asp", "passenger_asp", "base_price", 
                       "init_driver_asp", "init_passenger_asp"]

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

    def add(self, run_id: str, taxi_id: str, origin_edge: str, dest_edge: str, 
            distance: float, price: float, tick: int, driver_asp: float, 
            passenger_asp: float, base_price: str, init_driver_asp: str, 
            init_passenger_asp: str) -> None:
        """Log a completed trip transaction.
        
        Appends transaction details to CSV, including distance, price, driver
        and passenger aspired prices, and base fare information.
        
        :param run_id: Simulation run count.
        :type run_id: str
        :param taxi_id: Tricycle identifier.
        :type taxi_id: str
        :param origin_edge: Starting edge ID.
        :type origin_edge: str
        :param dest_edge: Destination edge ID.
        :type dest_edge: str
        :param distance: Distance traveled in meters.
        :type distance: float
        :param price: Final price charged to passenger.
        :type price: float
        :param tick: Simulation time when trip occurred.
        :type tick: int
        :param driver_asp: Driver's aspired price.
        :type driver_asp: float
        :param passenger_asp: Passenger's aspired price.
        :type passenger_asp: float
        :param base_price: Base fare component.
        :type base_price: str
        :param init_driver_asp: Initial driver aspired price.
        :type init_driver_asp: str
        :param init_passenger_asp: Initial passenger aspired price.
        :type init_passenger_asp: str
        """
        row = [run_id, taxi_id, origin_edge, dest_edge, distance, price, tick, 
               driver_asp, passenger_asp, base_price, init_driver_asp, init_passenger_asp]
        with self._lock:
            with open(self.transactions_filename, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(row)

    def addDriverInfo(self, tricycles: list) -> None:
        """Log summary statistics for all drivers.
        
        Creates and appends to a drivers.csv file daily statistics
        for each tricycle (trips, income, start/end time, distance, etc.).
        
        :param tricycles: List of Tricycle objects.
        :type tricycles: list
        """
        drivers_path = os.path.join(os.path.dirname(self.transactions_filename), "drivers.csv")
        drivers_path = os.path.normpath(drivers_path)
        header = ["trike_id", "hub_id", "start_tick", "end_tick", "actual_start_tick", 
                 "actual_end_tick", "actual_duration", "daily_trips", "daily_income", 
                 "fixed_income", "daily_distance"]

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
                        daily_stats['fixed_income'],
                        daily_stats['distance']
                    ])

    def addExpenseToLog(self, tricycleId: str, expensetype: str, amount: float, 
                       tick: int) -> None:
        """Record an expense for a tricycle.
        
        At the end of day, logs operational expenses such as fuel for each tricycle.
        
        :param tricycleId: Tricycle identifier.
        :type tricycleId: str
        :param expensetype: Type of expense (e.g., "fuel").
        :type expensetype: str
        :param amount: Expense amount.
        :type amount: float
        :param tick: Simulation tick when expense occurred.
        :type tick: int
        """
        with self._lock:
            with open(self.expenses_filename, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([tricycleId, expensetype, amount, tick])

    def recordAcceptedTrip(self) -> None:
        """Increment the count of total accepted trip requests."""
        with self._lock:
            self.accepted_trips += 1

    def recordRejectedTrip(self) -> None:
        """Increment the count of total rejected trip requests."""
        with self._lock:
            self.rejected_trips += 1

    def writeTripSummary(self) -> None:
        """Write a summary of accepted vs rejected trip attempts.
        
        Creates a trip_summary.csv file with counts of accepted, rejected,
        and total trip attempts for the simulation run.
        """
        summary_path = os.path.join(self.filedirectory, "trip_summary.csv")
        with self._lock:
            with open(summary_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["metric", "count"])
                writer.writerow(["accepted_trips", self.accepted_trips])
                writer.writerow(["rejected_trips", self.rejected_trips])
                total = self.accepted_trips + self.rejected_trips
                writer.writerow(["total_attempts", total])