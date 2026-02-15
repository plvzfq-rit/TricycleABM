import sqlite3
import os

from datetime import datetime
class SimulationLogger:
    def __init__(self):
        try:
             os.makedirs("../db", exist_ok=True)
        except Exception as e:
            pass
        if not os.path.isfile("../db/simulation_logs.db"):
            with open("../db/simulation_logs.db", "w") as f:
                pass
        self.conn = sqlite3.connect("../db/simulation_logs.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self._createTables()
        self._createRun(datetime.now().strftime("%Y%m%d-%H%M%S"))
        self.runId = self.cursor.lastrowid
        self.day = 0
        self.driverCache = dict()
        self.passengerCache = dict()

    def _createTables(self):

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS drivers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            trike_code TEXT,
            hub TEXT,
            start_tick INTEGER,
            end_tick INTEGER,
            max_gas REAL,
            gas_consumption_rate REAL,
            usual_gas_payment REAL,
            gets_full_tank BOOLEAN,
            farthest_distance REAL,
            daily_expense REAL,
            patience REAL,
            aspired_price REAL,
            minimum_price REAL,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS passengers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            passenger_code TEXT,
            day INTEGER,
            willingness_to_pay REAL,
            patience REAL,
            aspired_price REAL,
            destination_edge TEXT,
            destination_position REAL,
            destination_lane INTEGER,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
        ''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS passenger_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            driver_id INTEGER,
            passenger_id INTEGER,
            day INTEGER,
            distance REAL,
            tick INTEGER,
            result TEXT, 
            final_price REAL,
            FOREIGN KEY (run_id) REFERENCES runs(id),
            FOREIGN KEY (driver_id) REFERENCES drivers(id),
            FOREIGN KEY (passenger_id) REFERENCES passengers(id)
        );
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS negotiation_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER,
            current_offer REAL,
            driver_asp REAL,
            passenger_asp REAL,
            current_turn TEXT,
            iteration INTEGER,
            FOREIGN KEY (transaction_id) REFERENCES passenger_transactions(id)
        );''')

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            driver_id INTEGER,
            expense_type TEXT,
            amount REAL,
            FOREIGN KEY (run_id) REFERENCES runs(id),
            FOREIGN KEY (driver_id) REFERENCES drivers(id)
        )
        ''')
        self.conn.commit()

    def _createRun(self, timestamp: str):
        self.cursor.execute(
            "INSERT INTO runs (timestamp) VALUES (?)",
            (timestamp,)
        )
        self.conn.commit()
        self.runId = self.cursor.lastrowid

    def addDriver(self, trike):
        self.cursor.execute('''
            INSERT INTO drivers (
                run_id, trike_code, hub, start_tick, end_tick,
                max_gas, gas_consumption_rate, usual_gas_payment,
                gets_full_tank, farthest_distance, daily_expense,
                patience, aspired_price, minimum_price
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            int(self.runId),
            trike.name,
            trike.hub,
            int(trike.startTime),
            int(trike.endTime),
            float(trike.maxGas),
            float(trike.gasConsumptionRate),
            float(trike.usualGasPayment),
            trike.getsAFullTank,
            float(trike.farthestDistance),
            float(trike.dailyExpense),
            float(trike.patience),
            float(trike.aspiredPrice),
            float(trike.minimumPrice)
        ))
        self.conn.commit()

        driver_id = self.cursor.lastrowid
        self.driverCache[trike.name] = driver_id

    def addPassenger(self, passenger):
        self.cursor.execute('''
            INSERT INTO passengers (
                run_id, passenger_code, day,
                willingness_to_pay, patience, aspired_price,
                destination_edge, destination_position, destination_lane
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.runId,
            passenger.name,
            int(self.day),
            float(passenger.willingness_to_pay),
            float(passenger.patience),
            float(passenger.aspiredPrice),
            passenger.destination.edge,
            float(passenger.destination.position),
            int(passenger.destination.lane)
        ))
        self.conn.commit()

        passenger_id = self.cursor.lastrowid
        self.passengerCache[passenger.name] = passenger_id

    def recordTransaction(self, transaction, rounds):
        self._createTransaction(*transaction)
        index = self.cursor.lastrowid
        for _round in rounds:
            self._addNegotiationStep(index, *_round)

    def _createTransaction(self, trike_code, passenger_code, distance, tick, result, final_price):
        driver_id = self.driverCache[trike_code]
        passenger_id = self.passengerCache[passenger_code]

        self.cursor.execute('''
            INSERT INTO passenger_transactions (
                run_id, driver_id, passenger_id,
                day, distance, tick, result, final_price
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.runId,
            int(driver_id),
            int(passenger_id),
            int(self.day),
            float(distance),
            int(tick),
            result,
            float(final_price)
        ))
        self.conn.commit()

        return self.cursor.lastrowid
    
    def _addNegotiationStep(self, transaction_id, current_offer,
                         driver_asp, passenger_asp,
                         current_turn, iteration):

        self.cursor.execute('''
            INSERT INTO negotiation_steps (
                transaction_id, current_offer,
                driver_asp, passenger_asp,
                current_turn, iteration
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            int(transaction_id),
            float(current_offer),
            float(driver_asp),
            float(passenger_asp),
            current_turn,
            int(iteration)
        ))
        self.conn.commit()

    def addExpense(self, trike_code, expense_type, amount):
        driver_id = self.driverCache[trike_code]

        self.cursor.execute('''
            INSERT INTO expenses (
                run_id, driver_id, expense_type, amount
            )
            VALUES (?, ?, ?, ?)
        ''', (
            self.runId,
            int(driver_id),
            expense_type,
            float(amount)
        ))
        self.conn.commit()
    
    def commit(self):
        self.conn.commit()

    def nextDay(self):
        self.day += 1



# import csv
# import os
# import threading
# from datetime import datetime

# class SimulationLogger:
#     def __init__(self, sim_count: int, log_dir: str = "analysis"):
#         """
#         Creates a CSV logger with filename:
#         SIMCOUNT_TIMESTAMP/transactions.csv
#         """
#         # Use current time as timestamp
#         timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

#         run_dir = os.path.join(log_dir, f"{sim_count}_{timestamp}")
#         os.makedirs(run_dir, exist_ok=True)

#         # Construct filename
#         self.transactions_filename = os.path.join(run_dir, f"transactions.csv")
#         self.filedirectory = run_dir

#         self.expenses_filename = os.path.join(run_dir, f"expenses.csv")

#         # Define headers
#         self.headers = ["run_id", "trike_id", "origin_edge", "dest_edge", "distance", "price", "tick", "driver_asp", "passenger_asp"]

#         if not os.path.exists(self.transactions_filename):
#             with open(self.transactions_filename, mode="w", newline="", encoding="utf-8") as f:
#                 writer = csv.writer(f)
#                 writer.writerow(self.headers)

#         expense_headers = ["trike_id", "expense_type", "amount", "tick"]
#         if not os.path.exists(self.expenses_filename):
#             with open(self.expenses_filename, mode="w", newline="", encoding="utf-8") as f:
#                 writer = csv.writer(f)
#                 writer.writerow(expense_headers)

#         self._lock = threading.Lock()

#         # Trip acceptance/rejection counters
#         self.accepted_trips = 0
#         self.rejected_trips = 0

#     #include the driver's willingness to sell and passenger's willingness to pay
#     def add(self, run_id: str, taxi_id: str, origin_edge: str, dest_edge: str, distance: float, price: float, tick:int, driver_asp: float, passenger_asp: float) -> None:
#         row = [run_id, taxi_id, origin_edge, dest_edge, distance, price, tick, driver_asp, passenger_asp]
#         with self._lock:
#             with open(self.transactions_filename, mode="a", newline="", encoding="utf-8") as f:
#                 writer = csv.writer(f)
#                 writer.writerow(row)

#     def addDriverInfo(self, tricycles: list):
#         drivers_path = os.path.join(os.path.dirname(self.transactions_filename), "drivers.csv")
#         drivers_path = os.path.normpath(drivers_path)
#         header = ["trike_id", "hub_id", "start_tick", "end_tick", "actual_start_tick", "actual_end_tick", "actual_duration", "daily_trips", "daily_income", "daily_distance"]

#         with self._lock:
#             with open(drivers_path, mode="a", newline="", encoding="utf-8") as f:
#                 writer = csv.writer(f)
#                 writer.writerow(header)
#                 for tricycle in tricycles:
#                     daily_stats = tricycle.getDailyStats()
#                     writer.writerow([
#                         tricycle.name,
#                         tricycle.hub,
#                         tricycle.startTime,
#                         tricycle.endTime,
#                         tricycle.actualStartTick,
#                         tricycle.actualEndTick,
#                         daily_stats['actual_duration'],
#                         daily_stats['trips'],
#                         daily_stats['income'],
#                         daily_stats['distance']
#                     ])

#     def addExpenseToLog(self, tricycleId: str, expensetype: str, amount: float, tick: int) -> None:
#         with self._lock:
#             with open(self.expenses_filename, mode="a", newline="", encoding="utf-8") as f:
#                 writer = csv.writer(f)
#                 writer.writerow([tricycleId, expensetype, amount, tick])

#     def recordAcceptedTrip(self):
#         with self._lock:
#             self.accepted_trips += 1

#     def recordRejectedTrip(self):
#         with self._lock:
#             self.rejected_trips += 1

#     def writeTripSummary(self):
#         summary_path = os.path.join(self.filedirectory, "trip_summary.csv")
#         with self._lock:
#             with open(summary_path, mode="w", newline="", encoding="utf-8") as f:
#                 writer = csv.writer(f)
#                 writer.writerow(["metric", "count"])
#                 writer.writerow(["accepted_trips", self.accepted_trips])
#                 writer.writerow(["rejected_trips", self.rejected_trips])
#                 total = self.accepted_trips + self.rejected_trips
#                 writer.writerow(["total_attempts", total])

#     def getDirectory(self):
#         return self.filedirectory