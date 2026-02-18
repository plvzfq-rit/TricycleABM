"""Generate a mock simulation_logs.db for testing the Streamlit dashboard."""
import sqlite3
import os
import random
import math
from datetime import datetime

random.seed(42)

DB_PATH = os.path.join(os.path.dirname(__file__), "simulation_logs.db")

# Remove existing DB so we start fresh
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("PRAGMA foreign_keys = ON;")

# --- Create tables ---
cur.executescript("""
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT
);

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
);

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
);

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

CREATE TABLE IF NOT EXISTS negotiation_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER,
    current_offer REAL,
    driver_asp REAL,
    passenger_asp REAL,
    current_turn TEXT,
    iteration INTEGER,
    FOREIGN KEY (transaction_id) REFERENCES passenger_transactions(id)
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    driver_id INTEGER,
    expense_type TEXT,
    amount REAL,
    FOREIGN KEY (run_id) REFERENCES runs(id),
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);
""")

# --- Configuration ---
NUM_RUNS = 5
DRIVERS_PER_RUN = 20
PASSENGERS_PER_DAY = 40
DAYS_PER_RUN = 3
HUBS = ["toda_A", "toda_B", "toda_C", "toda_D"]
EDGES = [f"edge_{i}" for i in range(30)]
GAS_PRICE = 58.9


def driver_matrix(distance, base_price=50):
    limit = 1000
    value = base_price
    increments = [20, 30]
    idx = 0
    while distance > limit:
        value += increments[idx]
        limit += 500
        idx = 1 - idx
    return value


driver_id_counter = 0
passenger_id_counter = 0
txn_id_counter = 0

for run_idx in range(1, NUM_RUNS + 1):
    ts = f"2025010{run_idx}-120000"
    cur.execute("INSERT INTO runs (timestamp) VALUES (?)", (ts,))
    run_id = cur.lastrowid

    # --- Drivers ---
    run_driver_ids = []
    run_driver_meta = []
    for d in range(DRIVERS_PER_RUN):
        hub = random.choice(HUBS)
        trike_code = f"trike_{run_idx}_{d}"
        start_tick = random.randint(0, 7200)        # first 2 hours
        end_tick = random.randint(43200, 57600)      # last 4 hours
        max_gas = round(random.uniform(3.0, 8.0), 2)
        gas_consumption_rate = round(random.uniform(0.00003, 0.00008), 6)
        usual_gas_payment = round(random.choice([50, 100, 150, 200, 300]), 2)
        gets_full_tank = random.random() < 0.73
        farthest_distance = round(random.lognormvariate(8.2, 0.3), 2)  # ~3600m median
        daily_expense = round(random.lognormvariate(4.5, 0.5), 2)
        patience = round(random.uniform(0.3, 0.95), 3)
        aspired_price = round(random.choice([50, 60, 70, 100]), 2)
        minimum_price = round(random.choice([40, 50, 60, 80, 100, 150]), 2)

        cur.execute("""
            INSERT INTO drivers (
                run_id, trike_code, hub, start_tick, end_tick,
                max_gas, gas_consumption_rate, usual_gas_payment,
                gets_full_tank, farthest_distance, daily_expense,
                patience, aspired_price, minimum_price
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (run_id, trike_code, hub, start_tick, end_tick,
              max_gas, gas_consumption_rate, usual_gas_payment,
              int(gets_full_tank), farthest_distance, daily_expense,
              patience, aspired_price, minimum_price))
        did = cur.lastrowid
        run_driver_ids.append(did)
        run_driver_meta.append({
            "id": did, "hub": hub, "gas_consumption_rate": gas_consumption_rate,
            "aspired_price": aspired_price, "minimum_price": minimum_price,
            "patience": patience, "daily_expense": daily_expense,
            "farthest_distance": farthest_distance,
        })

    # --- Per day ---
    for day in range(DAYS_PER_RUN):
        pax_ids_this_day = []

        # Create passengers
        for p in range(PASSENGERS_PER_DAY):
            pax_code = f"pax_{run_idx}_{day}_{p}"
            wtp = round(random.lognormvariate(3.6, 0.713), 2)  # ~38 PHP/km median
            pax_patience = round(random.uniform(0.3, 0.95), 3)
            pax_asp = round(random.lognormvariate(3.2, 0.5), 2)
            dest_edge = random.choice(EDGES)
            dest_pos = round(random.uniform(0, 200), 2)
            dest_lane = random.randint(0, 2)

            cur.execute("""
                INSERT INTO passengers (
                    run_id, passenger_code, day,
                    willingness_to_pay, patience, aspired_price,
                    destination_edge, destination_position, destination_lane
                ) VALUES (?,?,?,?,?,?,?,?,?)
            """, (run_id, pax_code, day, wtp, pax_patience, pax_asp,
                  dest_edge, dest_pos, dest_lane))
            pax_ids_this_day.append((cur.lastrowid, wtp, pax_patience, pax_asp))

        # --- Transactions: each passenger gets matched to a random driver ---
        for pid, wtp, pax_patience, pax_asp in pax_ids_this_day:
            drv = random.choice(run_driver_meta)
            distance = round(random.uniform(500, 5000), 2)
            tick = random.randint(0, 57600)

            # Check if destination is too far (reject)
            if distance > drv["farthest_distance"]:
                cur.execute("""
                    INSERT INTO passenger_transactions (
                        run_id, driver_id, passenger_id,
                        day, distance, tick, result, final_price
                    ) VALUES (?,?,?,?,?,?,?,?)
                """, (run_id, drv["id"], pid, day, distance, tick, "reject", 0))
                continue

            # Simulate negotiation
            driver_price_1 = driver_matrix(distance, drv["aspired_price"])
            driver_price_2 = driver_matrix(distance, drv["minimum_price"])
            drv_asp = max(driver_price_1, driver_price_2)
            min_price = min(driver_price_1, driver_price_2)

            max_price = round(wtp * distance / 1000, 2)
            passenger_asp_abs = round(pax_asp * distance / 1000, 2)
            curr_offer = driver_matrix(distance, 50)

            drv_patience = drv["patience"]

            rounds_data = []
            turn = random.choice(["driver", "passenger"])
            rounds_data.append((curr_offer, drv_asp, passenger_asp_abs, turn, 0))

            agree = False
            for i in range(3):
                drv_asp_i = round(min_price + (drv_asp - min_price) * (drv_patience ** i), 2)
                passenger_asp_i = round(max_price - (max_price - passenger_asp_abs) * (pax_patience ** i), 2)

                if turn == "driver":
                    turn = "passenger"
                else:
                    turn = "driver"

                if turn == "driver":
                    if curr_offer >= drv_asp_i:
                        agree = True
                        break
                    else:
                        curr_offer = drv_asp_i
                        rounds_data.append((curr_offer, drv_asp_i, passenger_asp_i, "driver", i))
                else:
                    if curr_offer <= passenger_asp_i:
                        agree = True
                        break
                    else:
                        curr_offer = passenger_asp_i
                        rounds_data.append((curr_offer, drv_asp_i, passenger_asp_i, "passenger", i))

            result = "agree" if agree else "failed"
            final_price = round(curr_offer, 2) if agree else 0

            cur.execute("""
                INSERT INTO passenger_transactions (
                    run_id, driver_id, passenger_id,
                    day, distance, tick, result, final_price
                ) VALUES (?,?,?,?,?,?,?,?)
            """, (run_id, drv["id"], pid, day, distance, tick, result, final_price))
            txn_id = cur.lastrowid

            for rd in rounds_data:
                cur.execute("""
                    INSERT INTO negotiation_steps (
                        transaction_id, current_offer,
                        driver_asp, passenger_asp,
                        current_turn, iteration
                    ) VALUES (?,?,?,?,?,?)
                """, (txn_id, rd[0], rd[1], rd[2], rd[3], rd[4]))

        # --- Expenses at end of each day ---
        for drv in run_driver_meta:
            # End-of-day gas
            gas_amount = round(random.uniform(50, 300), 2)
            cur.execute("""
                INSERT INTO expenses (run_id, driver_id, expense_type, amount)
                VALUES (?,?,?,?)
            """, (run_id, drv["id"], "end_gas", gas_amount))

            # Daily expense
            cur.execute("""
                INSERT INTO expenses (run_id, driver_id, expense_type, amount)
                VALUES (?,?,?,?)
            """, (run_id, drv["id"], "daily_expense", drv["daily_expense"]))

            # Some drivers get midday gas
            if random.random() < 0.2:
                midday = round(random.uniform(30, 100), 2)
                cur.execute("""
                    INSERT INTO expenses (run_id, driver_id, expense_type, amount)
                    VALUES (?,?,?,?)
                """, (run_id, drv["id"], "midday_gas", midday))

conn.commit()

# Print summary
for table in ["runs", "drivers", "passengers", "passenger_transactions", "negotiation_steps", "expenses"]:
    count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"{table}: {count} rows")

conn.close()
print(f"\nMock database written to {DB_PATH}")
