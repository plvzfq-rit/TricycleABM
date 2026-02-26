import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import re

import sys

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.SimulationConfig import SimulationConfig

config = SimulationConfig()

# Set page config for a wider layout
st.set_page_config(layout="wide")

# Use a nice seaborn theme
sns.set_theme(style="whitegrid")

## --- Helper Functions ---

# Regex to find numbers in the amount column (handles floats, ints)
AMOUNT_REGEX = re.compile(r"[-+]?\d*\.\d+|\d+")

def extract_amount(amount_str):
    """
    Cleans the 'amount' column by extracting the first
    number found in a string (e.g., from "[310.96]").
    """
    if isinstance(amount_str, (int, float)):
        return amount_str
    if not isinstance(amount_str, str):
        return pd.NA

    match = AMOUNT_REGEX.search(amount_str)
    if match:
        return float(match.group(0))
    return pd.NA

def plot_distribution_with_stats(data, x_col, title, xlabel, ylabel="Count", color="skyblue", bins=30):
    """
    Plots a distribution using Seaborn and adds a text box with Mean, Median, Mode, and Std Dev.
    """
    if data.empty:
        st.write(f"No data to plot for {title}")
        return

    fig, ax = plt.subplots(figsize=(6, 4))

    # Plot histogram with KDE
    sns.histplot(data=data, x=x_col, bins=bins, color=color, kde=True, ax=ax, edgecolor="black")

    # Calculate stats
    mean_val = data[x_col].mean()
    median_val = data[x_col].median()
    std_val = data[x_col].std()

    # Mode calculation (approximate for continuous data)
    try:
        mode_series = data[x_col].round(2).mode()
        if len(mode_series) > 0:
            mode_val = mode_series[0]
            mode_str = f"{mode_val:,.2f}"
        else:
            mode_str = "N/A"
    except:
        mode_str = "N/A"

    # Create stats text block
    stats_text = (
        f"Mean: {mean_val:,.2f}\n"
        f"Median: {median_val:,.2f}\n"
        f"Mode: {mode_str}\n"
        f"Std Dev: {std_val:,.2f}"
    )

    ax.text(
        0.95, 0.95,
        stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment='top',
        horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
    )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    fig.tight_layout()
    st.pyplot(fig, use_container_width=True)


def ticks_to_time(ticks):
    """Convert simulation ticks to time format (starting at 06:00)"""
    if pd.isna(ticks) or ticks is None:
        return "N/A"
    ticks = int(ticks)
    hours = (ticks // 3600) + 6
    minutes = (ticks % 3600) // 60
    seconds = ticks % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def ticks_to_hours(ticks):
    """Convert ticks to hours (for duration display)"""
    if pd.isna(ticks) or ticks is None:
        return 0
    return ticks / 3600

def gini(series):
    """Compute Gini coefficient from a series of values."""
    values = np.asarray(series, dtype=float)
    if values.size == 0:
        return 0.0
    values = values - values.min()
    total = values.sum()
    if total == 0:
        return 0.0
    values = np.sort(values)
    n = values.size
    index = np.arange(1, n + 1)
    g = np.sum((2 * index - n - 1) * values) / (n * total)
    return float(g)

def lorenz_curve(data_series):
    """Compute Lorenz curve coordinates."""
    sorted_series = data_series.sort_values()
    cumulative = sorted_series.cumsum()
    total = sorted_series.sum()
    lorenz_y = cumulative / total
    lorenz_x = np.arange(1, len(lorenz_y) + 1) / len(lorenz_y)
    return lorenz_x, lorenz_y

def classify_driver(row):
    """Classify driver viability based on income vs expenses."""
    total_expenses = row['gas_expenses'] + row['daily_expenses']
    if row['daily_income'] >= total_expenses:
        return "Covers All Expenses"
    elif row['daily_income'] >= row['gas_expenses']:
        return "Covers Gas Only"
    else:
        return "Not Viable"


## --- Sidebar Configuration ---
st.sidebar.header("Analysis Configuration")

existing_logs = [
    d for d in os.listdir(".")
    if os.path.isdir(os.path.join(".", d))
]

if not existing_logs:
    st.error("No log directories found. Please check your folder structure.")
    st.stop()

LOG_DIRECTORY = st.sidebar.selectbox(
    "Select Log Directory to Analyze",
    options=existing_logs,
    index=0
)

all_folders = []
if os.path.isdir(LOG_DIRECTORY):
    try:
        all_items = sorted(os.listdir(LOG_DIRECTORY))
        all_folders = [item for item in all_items if os.path.isdir(os.path.join(LOG_DIRECTORY, item))]
    except Exception as e:
        st.error(f"Error reading directory {LOG_DIRECTORY}: {e}")
        st.stop()
else:
    st.error(f"Selected log directory '{LOG_DIRECTORY}' does not exist or is not a directory.")
    st.stop()

## --- DATA LOADING ---

df_all_list = []
df_expenses_list = []
df_drivers_list = []
df_trip_summary_list = []

sim_count = 0

for folder in all_folders:
    folder_path = os.path.join(LOG_DIRECTORY, folder)
    run_id = folder

    drivers_file = os.path.join(folder_path, "drivers.csv")
    transactions_file = os.path.join(folder_path, "transactions.csv")
    expenses_file = os.path.join(folder_path, "expenses.csv")

    if not os.path.exists(drivers_file):
        st.warning(f"Skipping folder {folder}: drivers.csv not found.")
        continue
    if not os.path.exists(transactions_file):
        st.warning(f"Skipping folder {folder}: transactions.csv not found.")
        continue
    if not os.path.exists(expenses_file):
        st.warning(f"Skipping folder {folder}: expenses.csv not found.")
        continue

    try:
        driver_df = pd.read_csv(drivers_file)
        transaction_df = pd.read_csv(transactions_file)
        expenses_df = pd.read_csv(expenses_file)

        driver_df["run_id"] = run_id
        df_drivers_list.append(driver_df)

        transaction_df["run_id"] = run_id
        merged_df = pd.merge(transaction_df, driver_df, on="trike_id", how="left")
        merged_df["run_id"] = run_id
        df_all_list.append(merged_df)

        expenses_df["run_id"] = run_id
        expenses_df["amount"] = expenses_df["amount"].apply(extract_amount)
        expenses_df.dropna(subset=['amount'], inplace=True)
        df_expenses_list.append(expenses_df)

        trip_summary_file = os.path.join(folder_path, "trip_summary.csv")
        if os.path.exists(trip_summary_file):
            summary_df = pd.read_csv(trip_summary_file)
            summary_df["run_id"] = run_id
            df_trip_summary_list.append(summary_df)

        sim_count += 1

    except Exception as e:
        st.error(f"Error processing folder {folder}: {e}")

if sim_count == 0:
    st.warning("No simulation data was successfully loaded. Check the log directory and file contents.")
    st.stop()

df_all = pd.concat(df_all_list, ignore_index=True)
df_all_expenses = pd.concat(df_expenses_list, ignore_index=True)
df_all_drivers = pd.concat(df_drivers_list, ignore_index=True) if df_drivers_list else pd.DataFrame()

df_all_expenses.dropna(subset=['amount'], inplace=True)

# Handle potential duplicate columns from merge
if 'run_id_x' in df_all.columns:
    df_all['run_id'] = df_all['run_id_x']
if 'run_id_y' in df_all.columns and 'run_id' not in df_all.columns:
    df_all['run_id'] = df_all['run_id_y']

# Config values for surplus calculations
GAS_PRICE = config.getGasPricePerLiter()
GAS_CONSUMPTION = config.getGasConsumption()

# Feature flags
has_duration_data = not df_all_drivers.empty and 'actual_duration' in df_all_drivers.columns
has_asp_data = 'driver_asp' in df_all.columns and 'passenger_asp' in df_all.columns
has_init_asp_data = 'init_driver_asp' in df_all.columns and 'init_passenger_asp' in df_all.columns
has_base_price = 'base_price' in df_all.columns
has_fixed_income = not df_all_drivers.empty and 'fixed_income' in df_all_drivers.columns
has_trip_summary = len(df_trip_summary_list) > 0

if has_trip_summary:
    df_trip_summary = pd.concat(df_trip_summary_list, ignore_index=True)
    summary_pivot = df_trip_summary.pivot(index='run_id', columns='metric', values='count').reset_index()

all_run_ids = sorted(df_all['run_id'].unique())

## --- PRECOMPUTE DAILY SUMMARY ---

daily_trips = df_all.groupby('run_id').agg({
    'price': ['sum', 'count'],
    'base_price': 'sum',
    'distance': 'sum'
}).reset_index()
daily_trips.columns = ['run_id', 'total_income', 'total_trips', 'total_fixed_income', 'total_distance']

daily_expenses_agg = df_all_expenses.groupby('run_id')['amount'].sum().reset_index()
daily_expenses_agg.columns = ['run_id', 'total_expenses']

daily_drivers_agg = df_all_drivers.groupby('run_id')['trike_id'].nunique().reset_index()
daily_drivers_agg.columns = ['run_id', 'active_drivers']

daily_summary = pd.merge(daily_trips, daily_expenses_agg, on='run_id', how='left')
daily_summary = pd.merge(daily_summary, daily_drivers_agg, on='run_id', how='left')
daily_summary.fillna(0, inplace=True)

daily_summary['total_profit'] = daily_summary['total_income'] - daily_summary['total_expenses']
daily_summary['total_fixed_profit'] = daily_summary['total_fixed_income'] - daily_summary['total_expenses']
daily_summary['avg_income_per_driver'] = daily_summary['total_income'] / daily_summary['active_drivers'].replace(0, np.nan)
daily_summary['avg_fixed_income_per_driver'] = daily_summary['total_fixed_income'] / daily_summary['active_drivers'].replace(0, np.nan)
daily_summary['avg_trips_per_driver'] = daily_summary['total_trips'] / daily_summary['active_drivers'].replace(0, np.nan)
daily_summary['avg_profit_per_driver'] = daily_summary['total_profit'] / daily_summary['active_drivers'].replace(0, np.nan)
daily_summary['avg_fixed_income_per_driver'] = daily_summary['total_fixed_income'] / daily_summary['active_drivers'].replace(0, np.nan)
daily_summary['avg_fixed_profit_per_driver'] = daily_summary['total_fixed_profit'] / daily_summary['active_drivers'].replace(0, np.nan)

daily_summary = daily_summary.sort_values('run_id').reset_index(drop=True)

## --- PRECOMPUTE PER-DAY GINI ---

daily_gini = []
for run in all_run_ids:
    run_transactions = df_all[df_all['run_id'] == run]
    run_income = run_transactions.groupby('trike_id')['price'].sum()
    daily_gini.append({'run_id': run, 'gini_gross_income': gini(run_income)})

daily_gini_df = pd.DataFrame(daily_gini)
daily_summary = pd.merge(daily_summary, daily_gini_df, on='run_id', how='left')

## --- PRECOMPUTE PER-DAY SURPLUS ---

# Consumer surplus
df_all['passenger_surplus'] = df_all['passenger_asp'] - df_all['price'] if has_asp_data else np.nan
# Producer surplus
df_all['marginal_cost'] = (df_all['distance'] * GAS_PRICE) / (1000 * GAS_CONSUMPTION)
df_all['producer_surplus'] = df_all['price'] - df_all['marginal_cost']

daily_surplus = df_all.groupby('run_id').agg(
    avg_consumer_surplus=('passenger_surplus', 'mean'),
    avg_producer_surplus=('producer_surplus', 'mean'),
).reset_index()
daily_summary = pd.merge(daily_summary, daily_surplus, on='run_id', how='left')

## --- PRECOMPUTE PER-DAY TRIP DISPATCH ---

if has_trip_summary and 'accepted_trips' in summary_pivot.columns and 'rejected_trips' in summary_pivot.columns:
    summary_pivot['total_attempts'] = summary_pivot['accepted_trips'] + summary_pivot['rejected_trips']
    summary_pivot['acceptance_rate'] = (summary_pivot['accepted_trips'] / summary_pivot['total_attempts'] * 100).round(1)
    daily_summary = pd.merge(daily_summary, summary_pivot[['run_id', 'accepted_trips', 'rejected_trips', 'total_attempts', 'acceptance_rate']], on='run_id', how='left')

## --- PRECOMPUTE PER-DAY PROFITABILITY ---

daily_profitability = []
for run in all_run_ids:
    run_transactions = df_all[df_all['run_id'] == run]
    run_expenses = df_all_expenses[df_all_expenses['run_id'] == run]

    run_income = run_transactions.groupby('trike_id')['price'].sum().reset_index(name='daily_income')
    run_fixed_income = run_transactions.groupby('trike_id')['base_price'].sum().reset_index(name='daily_income') if has_base_price else None
    run_gas = run_expenses[run_expenses['expense_type'] == 'gas'].groupby('trike_id')['amount'].sum().reset_index(name='gas_expenses')
    run_all_exp = run_expenses.groupby('trike_id')['amount'].sum().reset_index(name='daily_expenses')

    run_drivers = run_transactions['trike_id'].drop_duplicates()

    # Negotiated income profitability
    viability = run_drivers.to_frame()
    viability = pd.merge(viability, run_income, on='trike_id', how='left')
    viability = pd.merge(viability, run_gas, on='trike_id', how='left')
    viability = pd.merge(viability, run_all_exp, on='trike_id', how='left')
    viability.fillna(0, inplace=True)
    viability['viability_group'] = viability.apply(classify_driver, axis=1)

    ordered_groups = ["Covers All Expenses", "Covers Gas Only", "Not Viable"]
    counts = viability['viability_group'].value_counts().reindex(ordered_groups, fill_value=0)
    total = counts.sum()

    row_data = {
        'run_id': run,
        'covers_all': counts.get("Covers All Expenses", 0),
        'covers_gas': counts.get("Covers Gas Only", 0),
        'not_viable': counts.get("Not Viable", 0),
        'total_drivers': total,
        'pct_covers_all': (counts.get("Covers All Expenses", 0) / total * 100) if total > 0 else 0,
        'pct_covers_gas': (counts.get("Covers Gas Only", 0) / total * 100) if total > 0 else 0,
        'pct_not_viable': (counts.get("Not Viable", 0) / total * 100) if total > 0 else 0,
    }

    # Fixed income profitability
    if run_fixed_income is not None:
        viability_fixed = run_drivers.to_frame()
        viability_fixed = pd.merge(viability_fixed, run_fixed_income, on='trike_id', how='left')
        viability_fixed = pd.merge(viability_fixed, run_gas, on='trike_id', how='left')
        viability_fixed = pd.merge(viability_fixed, run_all_exp, on='trike_id', how='left')
        viability_fixed.fillna(0, inplace=True)
        viability_fixed['viability_group'] = viability_fixed.apply(classify_driver, axis=1)

        counts_fixed = viability_fixed['viability_group'].value_counts().reindex(ordered_groups, fill_value=0)
        row_data['fixed_covers_all'] = counts_fixed.get("Covers All Expenses", 0)
        row_data['fixed_covers_gas'] = counts_fixed.get("Covers Gas Only", 0)
        row_data['fixed_not_viable'] = counts_fixed.get("Not Viable", 0)
        row_data['fixed_pct_covers_all'] = (counts_fixed.get("Covers All Expenses", 0) / total * 100) if total > 0 else 0
        row_data['fixed_pct_covers_gas'] = (counts_fixed.get("Covers Gas Only", 0) / total * 100) if total > 0 else 0
        row_data['fixed_pct_not_viable'] = (counts_fixed.get("Not Viable", 0) / total * 100) if total > 0 else 0

    daily_profitability.append(row_data)

daily_profitability_df = pd.DataFrame(daily_profitability)


## ============================================================
## STREAMLIT APP LAYOUT
## ============================================================

st.title(f"Tricycle Simulation Analysis: {LOG_DIRECTORY}")
st.caption(f"Analyzing **{sim_count}** simulation day(s)")
st.divider()

## ============================================================
## SECTION A: CROSS-DAY COMPARISON OVERVIEW
## ============================================================

st.header("Cross-Day Comparison")

income_mode_cross = st.radio(
    "Income type",
    options=["Negotiated Income", "Fixed Income (Base Price)"],
    horizontal=True,
    key="cross_day_income_toggle"
)
use_fixed_cross = income_mode_cross == "Fixed Income (Base Price)"

cross_income_col = 'total_fixed_income' if use_fixed_cross else 'total_income'
cross_profit_col = 'total_fixed_profit' if use_fixed_cross else 'total_profit'
cross_avg_income_col = 'avg_fixed_income_per_driver' if use_fixed_cross else 'avg_income_per_driver'
cross_avg_profit_col = 'avg_fixed_profit_per_driver' if use_fixed_cross else 'avg_profit_per_driver'
cross_label = "Fixed" if use_fixed_cross else "Negotiated"

# --- A1: Income, Expenses, Profit trend ---
st.subheader(f"Income, Expenses & Profit Across Days ({cross_label})")
fig_trend, ax_trend = plt.subplots(figsize=(10, 5))
ax_trend.plot(daily_summary['run_id'], daily_summary[cross_income_col], marker='o', label='Total Income', color='#2a9d8f')
ax_trend.plot(daily_summary['run_id'], daily_summary['total_expenses'], marker='s', label='Total Expenses', color='#e76f51')
ax_trend.plot(daily_summary['run_id'], daily_summary[cross_profit_col], marker='^', label='Total Profit', color='#264653')
ax_trend.set_xlabel("Day (Run ID)")
ax_trend.set_ylabel("PHP")
ax_trend.set_title(f"Daily {cross_label} Income, Expenses & Profit")
ax_trend.legend()
ax_trend.tick_params(axis='x', rotation=45)
fig_trend.tight_layout()
st.pyplot(fig_trend, use_container_width=True)

# --- A2: Trip count and acceptance rate ---
st.subheader("Trip Count Across Days")
fig_trips, ax_trips = plt.subplots(figsize=(10, 4))
ax_trips.bar(daily_summary['run_id'], daily_summary['total_trips'], color='#2a9d8f', alpha=0.8, label='Total Trips')
ax_trips.set_xlabel("Day (Run ID)")
ax_trips.set_ylabel("Trip Count")
ax_trips.set_title("Trips Per Day")
ax_trips.tick_params(axis='x', rotation=45)

ax_trips.legend()

fig_trips.tight_layout()
st.pyplot(fig_trips, use_container_width=True)

# --- A3: Average driver income & profit per day ---
st.subheader(f"Average Driver Income & Profit Per Day ({cross_label})")
fig_avg, ax_avg = plt.subplots(figsize=(10, 4))
ax_avg.plot(daily_summary['run_id'], daily_summary[cross_avg_income_col], marker='o', label='Avg Income/Driver', color='#2a9d8f')
ax_avg.plot(daily_summary['run_id'], daily_summary[cross_avg_profit_col], marker='s', label='Avg Profit/Driver', color='#264653')
ax_avg.set_xlabel("Day (Run ID)")
ax_avg.set_ylabel("PHP")
ax_avg.set_title(f"Average Driver {cross_label} Income & Profit Per Day")
ax_avg.legend()
ax_avg.tick_params(axis='x', rotation=45)
fig_avg.tight_layout()
st.pyplot(fig_avg, use_container_width=True)

# --- A4: Gini coefficient per day ---
st.subheader("Income Inequality (Gini) Across Days")
fig_gini, ax_gini = plt.subplots(figsize=(10, 4))
ax_gini.plot(daily_summary['run_id'], daily_summary['gini_gross_income'], marker='o', color='#e76f51', linewidth=2)
ax_gini.set_xlabel("Day (Run ID)")
ax_gini.set_ylabel("Gini Coefficient")
ax_gini.set_title("Gini Coefficient (Gross Income) Per Day")
ax_gini.set_ylim(0, max(0.5, daily_summary['gini_gross_income'].max() * 1.2))
ax_gini.tick_params(axis='x', rotation=45)
fig_gini.tight_layout()
st.pyplot(fig_gini, use_container_width=True)

# --- A5: Consumer & Producer surplus per day ---
if has_asp_data:
    st.subheader("Average Surplus Across Days")
    fig_surplus, ax_surplus = plt.subplots(figsize=(10, 4))
    ax_surplus.plot(daily_summary['run_id'], daily_summary['avg_consumer_surplus'], marker='o', label='Avg Consumer Surplus', color='#2a9d8f')
    ax_surplus.plot(daily_summary['run_id'], daily_summary['avg_producer_surplus'], marker='s', label='Avg Producer Surplus', color='#e76f51')
    ax_surplus.set_xlabel("Day (Run ID)")
    ax_surplus.set_ylabel("PHP")
    ax_surplus.set_title("Average Consumer & Producer Surplus Per Day")
    ax_surplus.legend()
    ax_surplus.tick_params(axis='x', rotation=45)
    fig_surplus.tight_layout()
    st.pyplot(fig_surplus, use_container_width=True)

# --- A6: Driver profitability proportions per day ---
st.subheader(f"Driver Profitability Across Days ({cross_label})")

prof_prefix = 'fixed_' if use_fixed_cross and 'fixed_pct_covers_all' in daily_profitability_df.columns else ''
prof_pct_all = f'{prof_prefix}pct_covers_all'
prof_pct_gas = f'{prof_prefix}pct_covers_gas'
prof_pct_nv = f'{prof_prefix}pct_not_viable'

fig_prof, ax_prof = plt.subplots(figsize=(10, 4))
ax_prof.bar(daily_profitability_df['run_id'], daily_profitability_df[prof_pct_all], label='Covers All Expenses', color='#2a9d8f')
ax_prof.bar(daily_profitability_df['run_id'], daily_profitability_df[prof_pct_gas], bottom=daily_profitability_df[prof_pct_all], label='Covers Gas Only', color='#e9c46a')
ax_prof.bar(daily_profitability_df['run_id'], daily_profitability_df[prof_pct_nv],
            bottom=daily_profitability_df[prof_pct_all] + daily_profitability_df[prof_pct_gas],
            label='Not Viable', color='#e76f51')
ax_prof.set_xlabel("Day (Run ID)")
ax_prof.set_ylabel("% of Drivers")
ax_prof.set_title(f"Driver Profitability Classification Per Day ({cross_label})")
ax_prof.legend()
ax_prof.set_ylim(0, 105)
ax_prof.tick_params(axis='x', rotation=45)
fig_prof.tight_layout()
st.pyplot(fig_prof, use_container_width=True)

# --- Daily summary table ---
st.subheader("Daily Summary Table")
display_cols = ['run_id', 'total_trips', 'total_income', 'total_fixed_income', 'total_expenses',
                'total_profit', 'total_fixed_profit', 'total_distance', 'active_drivers',
                'avg_trips_per_driver', 'avg_income_per_driver', 'avg_profit_per_driver', 'gini_gross_income']
if has_trip_summary and 'acceptance_rate' in daily_summary.columns:
    display_cols.extend(['accepted_trips', 'rejected_trips', 'acceptance_rate'])
display_cols = [c for c in display_cols if c in daily_summary.columns]
st.dataframe(daily_summary[display_cols])

st.divider()

## ============================================================
## SECTION B: PER-DAY DEEP DIVE
## ============================================================

st.header("Daily View")

selected_day = st.selectbox("Select Day", options=all_run_ids, index=0, key="day_selector")

# Filter data for selected day
day_transactions = df_all[df_all['run_id'] == selected_day]
day_expenses = df_all_expenses[df_all_expenses['run_id'] == selected_day]
day_drivers = df_all_drivers[df_all_drivers['run_id'] == selected_day] if not df_all_drivers.empty else pd.DataFrame()
day_summary_row = daily_summary[daily_summary['run_id'] == selected_day]

## --- B1: Day Summary Metrics ---
st.subheader(f"Day {selected_day} — Summary")

if not day_summary_row.empty:
    row = day_summary_row.iloc[0]
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Trips", f"{int(row['total_trips']):,}")
    col2.metric("Active Drivers", f"{int(row['active_drivers']):,}")

    col_n1, col_n2, col_n3, col_n4, col_n5 = st.columns(5)
    col_n1.metric("Total Income (Negotiated)", f"PHP {row['total_income']:,.2f}")
    col_n2.metric("Total Profit (Negotiated)", f"PHP {row['total_profit']:,.2f}")
    col_n3.metric("Total Expenses", f"PHP {row['total_expenses']:,.2f}")


    col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
    col_b1.metric("Total Income (Base Price)", f"PHP {row['total_fixed_income']:,.2f}")
    col_b2.metric("Total Profit (Base Price)", f"PHP {row['total_fixed_profit']:,.2f}")
    profit_diff = row['total_profit'] - row['total_fixed_profit']
    col_b3.metric("Profit Difference (Neg. - Base)", f"PHP {profit_diff:,.2f}")

## --- B2: Driver Ranking Table ---
st.subheader(f"Day {selected_day} — Driver Rankings")
st.markdown(
    "Each driver's income, expenses, and profit for this day. "
    "**Fixed income** represents what each driver would earn under the regulated fare matrix "
    "(base price), without any bargaining adjustments."
)

day_driver_income = day_transactions.groupby('trike_id')['price'].sum().reset_index(name='income')
day_driver_fixed = day_transactions.groupby('trike_id')['base_price'].sum().reset_index(name='fixed_income') if has_base_price else pd.DataFrame()
day_driver_expenses = day_expenses.groupby('trike_id')['amount'].sum().reset_index(name='expenses')
day_driver_trips = day_transactions.groupby('trike_id').size().reset_index(name='trips')
day_driver_distance = day_transactions.groupby('trike_id')['distance'].sum().reset_index(name='total_distance')

day_driver_table = day_driver_income.copy()
if not day_driver_fixed.empty:
    day_driver_table = pd.merge(day_driver_table, day_driver_fixed, on='trike_id', how='left')
day_driver_table = pd.merge(day_driver_table, day_driver_expenses, on='trike_id', how='left')
day_driver_table = pd.merge(day_driver_table, day_driver_trips, on='trike_id', how='left')
day_driver_table = pd.merge(day_driver_table, day_driver_distance, on='trike_id', how='left')
day_driver_table.fillna(0, inplace=True)
day_driver_table['profit'] = day_driver_table['income'] - day_driver_table['expenses']

# Add duration info if available
if has_duration_data and not day_drivers.empty:
    duration_cols = ['trike_id']
    if 'actual_duration' in day_drivers.columns:
        day_drivers_copy = day_drivers.copy()
        day_drivers_copy['duration_hours'] = day_drivers_copy['actual_duration'].apply(ticks_to_hours)
        duration_cols.append('duration_hours')
    if 'actual_start_tick' in day_drivers.columns:
        day_drivers_copy['start_time'] = day_drivers_copy['actual_start_tick'].apply(ticks_to_time)
        duration_cols.append('start_time')
    if 'actual_end_tick' in day_drivers.columns:
        day_drivers_copy['end_time'] = day_drivers_copy['actual_end_tick'].apply(ticks_to_time)
        duration_cols.append('end_time')
    duration_cols = [c for c in duration_cols if c in day_drivers_copy.columns]
    day_driver_table = pd.merge(day_driver_table, day_drivers_copy[duration_cols], on='trike_id', how='left')

st.dataframe(day_driver_table.sort_values('profit', ascending=False))

## --- B3: Driver Income/Profit Distributions ---
st.subheader(f"Day {selected_day} — Driver Distributions")

col_d1, col_d2 = st.columns(2)

with col_d1:
    if not day_driver_table.empty:
        fig_inc, ax_inc = plt.subplots(figsize=(6, 4))
        sns.histplot(data=day_driver_table, x='income', bins=20, color='#2a9d8f', kde=True, ax=ax_inc, edgecolor='black')
        ax_inc.set_title("Driver Income Distribution")
        ax_inc.set_xlabel("Income (PHP)")
        ax_inc.set_ylabel("Count")
        st.pyplot(fig_inc, use_container_width=True)

with col_d2:
    if not day_driver_table.empty and 'fixed_income' in day_driver_table.columns:
        fig_fi, ax_fi = plt.subplots(figsize=(6, 4))
        sns.histplot(data=day_driver_table, x='fixed_income', bins=20, color='#e9c46a', kde=True, ax=ax_fi, edgecolor='black')
        ax_fi.set_title("Driver Fixed Income Distribution")
        ax_fi.set_xlabel("Fixed Income (PHP)")
        ax_fi.set_ylabel("Count")
        st.pyplot(fig_fi, use_container_width=True)

col_d3, col_d4 = st.columns(2)

with col_d3:
    if not day_driver_table.empty:
        fig_prof_d, ax_prof_d = plt.subplots(figsize=(6, 4))
        sns.histplot(data=day_driver_table, x='profit', bins=20, color='#264653', kde=True, ax=ax_prof_d, edgecolor='black')
        ax_prof_d.set_title("Driver Profit Distribution")
        ax_prof_d.set_xlabel("Profit (PHP)")
        ax_prof_d.set_ylabel("Count")
        st.pyplot(fig_prof_d, use_container_width=True)

with col_d4:
    if not day_driver_table.empty and 'fixed_income' in day_driver_table.columns:
        day_driver_table['fixed_profit'] = day_driver_table['fixed_income'] - day_driver_table['expenses']
        fig_fp, ax_fp = plt.subplots(figsize=(6, 4))
        sns.histplot(data=day_driver_table, x='fixed_profit', bins=20, color='#bc6c25', kde=True, ax=ax_fp, edgecolor='black')
        ax_fp.set_title("Driver Fixed Profit Distribution")
        ax_fp.set_xlabel("Fixed Profit (PHP)")
        ax_fp.set_ylabel("Count")
        st.pyplot(fig_fp, use_container_width=True)

if has_duration_data and not day_drivers.empty and 'actual_duration' in day_drivers.columns:
    col_dur1, col_dur2 = st.columns(2)
    day_drivers_plot = day_drivers.copy()
    day_drivers_plot['duration_hours_plot'] = day_drivers_plot['actual_duration'] / 3600

    with col_dur1:
        fig_dur, ax_dur = plt.subplots(figsize=(6, 4))
        sns.histplot(data=day_drivers_plot, x='duration_hours_plot', bins=20, color='#264653', kde=True, ax=ax_dur, edgecolor='black')
        ax_dur.set_title("Driver Duration Distribution")
        ax_dur.set_xlabel("Duration (hours)")
        ax_dur.set_ylabel("Count")
        st.pyplot(fig_dur, use_container_width=True)

    with col_dur2:
        if 'daily_income' in day_drivers_plot.columns:
            day_drivers_plot['income_per_hour'] = day_drivers_plot.apply(
                lambda x: x['daily_income'] / (x['actual_duration'] / 3600) if x['actual_duration'] > 0 else 0,
                axis=1
            )
            iph_data = day_drivers_plot[day_drivers_plot['income_per_hour'] > 0]
            if not iph_data.empty:
                fig_iph, ax_iph = plt.subplots(figsize=(6, 4))
                sns.histplot(data=iph_data, x='income_per_hour', bins=20, color='#e9c46a', kde=True, ax=ax_iph, edgecolor='black')
                ax_iph.set_title("Income per Hour Distribution")
                ax_iph.set_xlabel("Income per Hour (PHP)")
                ax_iph.set_ylabel("Count")
                st.pyplot(fig_iph, use_container_width=True)

## --- B4: Trip-Level Analytics ---
st.subheader(f"Day {selected_day} — Trip-Level Analytics")

trip_display_cols = ['trike_id', 'hub_id', 'origin_edge', 'dest_edge', 'distance', 'price', 'tick',
                     'driver_asp', 'passenger_asp', 'base_price', 'init_driver_asp', 'init_passenger_asp']
trip_display_cols = [c for c in trip_display_cols if c in day_transactions.columns]

# Filters
trip_filter_col1, trip_filter_col2, trip_filter_col3 = st.columns(3)

with trip_filter_col1:
    trip_day_drivers = sorted(day_transactions['trike_id'].unique())
    trip_sel_drivers = st.multiselect("Filter by Driver", options=trip_day_drivers, default=[], placeholder="All drivers", key="trip_driver_filter")

with trip_filter_col2:
    if 'hub_id' in day_transactions.columns:
        trip_day_hubs = sorted(day_transactions['hub_id'].dropna().unique())
        trip_sel_hubs = st.multiselect("Filter by Hub", options=trip_day_hubs, default=[], placeholder="All hubs", key="trip_hub_filter")
    else:
        trip_sel_hubs = []

with trip_filter_col3:
    row_limit = st.selectbox("Rows to display", options=[20, 50, 100, 250, 500, "All"], index=0, key="trip_row_limit")

filtered_day_trips = day_transactions.copy()
if trip_sel_drivers:
    filtered_day_trips = filtered_day_trips[filtered_day_trips['trike_id'].isin(trip_sel_drivers)]
if trip_sel_hubs and 'hub_id' in filtered_day_trips.columns:
    filtered_day_trips = filtered_day_trips[filtered_day_trips['hub_id'].isin(trip_sel_hubs)]

if row_limit == "All":
    display_trips = filtered_day_trips[trip_display_cols].sort_values(by='tick')
else:
    display_trips = filtered_day_trips[trip_display_cols].sort_values(by='tick').head(row_limit)

st.caption(f"Showing {len(display_trips)} of {len(filtered_day_trips)} filtered trips ({len(day_transactions)} total for this day)")
st.dataframe(display_trips)

# Trip distribution graphs
col_t1, col_t2 = st.columns(2)

with col_t1:
    plot_distribution_with_stats(
        day_transactions, 'price',
        "Trip Price Distribution (Negotiated)", "Price (PHP)",
        color="skyblue"
    )

with col_t2:
    plot_distribution_with_stats(
        day_transactions, 'base_price',
        "Trip Price Distribution (Base Price)", "Price (PHP)",
        color="lightgreen"
    )

col_t1, col_t2 = st.columns(2)

with col_t1:
    plot_distribution_with_stats(
        day_transactions, 'distance',
        "Trip Distance Distribution", "Distance (meters)",
        color="skyblue"
    )

with col_t2:
    plot_distribution_with_stats(
        day_transactions, 'tick',
        "Trips Over Time (by Tick)", "Tick",
        color="violet"
    )

## --- B5: Bargaining Analytics ---
if has_asp_data:
    st.subheader(f"Day {selected_day} — Bargaining Analytics")
    st.write("Aspiration prices represent the driver's willingness-to-sell and the passenger's willingness-to-pay during fare negotiation.")

    asp_data = day_transactions.dropna(subset=['driver_asp', 'passenger_asp']).copy()

    if not asp_data.empty:
        asp_data['asp_gap'] = asp_data['driver_asp'] - asp_data['passenger_asp']

        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
        col_b1.metric("Avg Driver ASP", f"PHP {asp_data['driver_asp'].mean():,.2f}")
        col_b2.metric("Avg Passenger ASP", f"PHP {asp_data['passenger_asp'].mean():,.2f}")
        col_b3.metric("Avg Agreed Price", f"PHP {asp_data['price'].mean():,.2f}")
        col_b4.metric("Avg Bargaining Gap", f"PHP {asp_data['asp_gap'].mean():,.2f}")

        col_asp1, col_asp2 = st.columns(2)
        with col_asp1:
            plot_distribution_with_stats(asp_data, 'driver_asp', "Driver ASP Distribution", "Driver ASP (PHP)", color="#e76f51")
        with col_asp2:
            plot_distribution_with_stats(asp_data, 'passenger_asp', "Passenger ASP Distribution", "Passenger ASP (PHP)", color="#2a9d8f")

        plot_distribution_with_stats(asp_data, 'asp_gap', "Bargaining Gap Distribution", "Gap (PHP)", color="#f4a261")

        # Scatter: Driver ASP vs Passenger ASP
        fig_scatter, ax_scatter = plt.subplots(figsize=(6, 5))
        scatter = ax_scatter.scatter(
            asp_data['passenger_asp'], asp_data['driver_asp'],
            c=asp_data['price'], cmap='viridis', alpha=0.6,
            edgecolors='black', linewidths=0.3, s=20
        )
        plt.colorbar(scatter, ax=ax_scatter, label='Agreed Price (PHP)')
        asp_min = min(asp_data['passenger_asp'].min(), asp_data['driver_asp'].min())
        asp_max = max(asp_data['passenger_asp'].max(), asp_data['driver_asp'].max())
        ax_scatter.plot([asp_min, asp_max], [asp_min, asp_max], 'r--', alpha=0.5, label='Equal ASP line')
        ax_scatter.set_xlabel("Passenger ASP (PHP)")
        ax_scatter.set_ylabel("Driver ASP (PHP)")
        ax_scatter.set_title("Driver vs Passenger Aspiration Prices")
        ax_scatter.legend()
        fig_scatter.tight_layout()
        st.pyplot(fig_scatter, use_container_width=True)

        if has_base_price:
            base_price_data = asp_data.dropna(subset=['base_price'])
            if not base_price_data.empty:
                plot_distribution_with_stats(base_price_data, 'base_price', "Base Price Distribution", "Base Price (PHP)", color="#264653")
                col_bp1, col_bp2, col_bp3 = st.columns(3)
                col_bp1.metric("Avg Base Price", f"PHP {base_price_data['base_price'].mean():,.2f}")
                col_bp2.metric("Avg Agreed vs Base", f"PHP {(base_price_data['price'] - base_price_data['base_price']).mean():,.2f}")
                col_bp3.metric("Avg Markup over Base", f"{((base_price_data['price'] / base_price_data['base_price'] - 1) * 100).mean():,.1f}%")

        if has_init_asp_data:
            init_asp_data = asp_data.dropna(subset=['init_driver_asp', 'init_passenger_asp'])
            if not init_asp_data.empty:
                init_asp_data['driver_asp_change'] = init_asp_data['driver_asp'] - init_asp_data['init_driver_asp']
                init_asp_data['passenger_asp_change'] = init_asp_data['passenger_asp'] - init_asp_data['init_passenger_asp']
                init_asp_data['init_asp_gap'] = init_asp_data['init_driver_asp'] - init_asp_data['init_passenger_asp']

                col_i1, col_i2, col_i3, col_i4 = st.columns(4)
                col_i1.metric("Avg Init Driver ASP", f"PHP {init_asp_data['init_driver_asp'].mean():,.2f}")
                col_i2.metric("Avg Init Passenger ASP", f"PHP {init_asp_data['init_passenger_asp'].mean():,.2f}")
                col_i3.metric("Avg Driver ASP Change", f"PHP {init_asp_data['driver_asp_change'].mean():,.2f}")
                col_i4.metric("Avg Passenger ASP Change", f"PHP {init_asp_data['passenger_asp_change'].mean():,.2f}")

                col_init1, col_init2 = st.columns(2)
                with col_init1:
                    plot_distribution_with_stats(init_asp_data, 'init_driver_asp', "Initial Driver ASP Distribution", "Init Driver ASP (PHP)", color="#e9c46a")
                with col_init2:
                    plot_distribution_with_stats(init_asp_data, 'init_passenger_asp', "Initial Passenger ASP Distribution", "Init Passenger ASP (PHP)", color="#606c38")

                plot_distribution_with_stats(init_asp_data, 'init_asp_gap', "Initial Bargaining Gap Distribution", "Init Gap (PHP)", color="#bc6c25")
    else:
        st.info("No aspiration price data available for this day.")

## --- B6: Surplus ---
st.subheader(f"Day {selected_day} — Surplus")

st.markdown(
    "**Passenger (Consumer) Surplus** measures the difference between a passenger's maximum "
    "willingness to pay (`passenger_asp`) and the final negotiated fare (`price`). "
    "It represents the economic benefit passengers obtain from successful rides. \n\n"

    "**Computation**: \n"
    "`Passenger Surplus = passenger_asp - price` \n\n"

    "- **Positive Surplus**: The passenger paid less than their WTP. \n"
    "- **Negative Surplus**: The passenger paid more than their WTP. \n\n"

    "**Driver (Producer) Surplus** measures the difference between the fare received (`price`) "
    "and the marginal cost of completing the trip (`marginal_cost`). "
    "It represents the profit drivers obtain from successful rides. \n\n"

    "**Computation**: \n"
    "`Driver Surplus = price - marginal_cost` \n\n"

    "- **Positive Surplus**: The driver earned more than the cost of completing the trip. \n"
    "- **Negative Surplus**: The driver earned less than the cost of completing the trip."
)

day_with_surplus = day_transactions.copy()

# Consumer surplus
if has_asp_data:
    day_with_surplus['passenger_surplus'] = day_with_surplus['passenger_asp'] - day_with_surplus['price']
    cs_total = day_with_surplus['passenger_surplus'].sum()
    cs_avg = day_with_surplus['passenger_surplus'].mean()
    cs_median = day_with_surplus['passenger_surplus'].median()

    col_cs1, col_cs2, col_cs3 = st.columns(3)
    col_cs1.metric("Total Consumer Surplus", f"PHP {cs_total:,.2f}")
    col_cs2.metric("Avg Consumer Surplus", f"PHP {cs_avg:,.2f}")
    col_cs3.metric("Median Consumer Surplus", f"PHP {cs_median:,.2f}")

    plot_distribution_with_stats(day_with_surplus.dropna(subset=['passenger_surplus']), 'passenger_surplus',
                                 "Consumer Surplus Distribution", "Consumer Surplus (PHP)", color="#2a9d8f")

# Producer surplus
day_with_surplus['marginal_cost'] = (day_with_surplus['distance'] * GAS_PRICE) / (1000 * GAS_CONSUMPTION)
day_with_surplus['producer_surplus'] = day_with_surplus['price'] - day_with_surplus['marginal_cost']

ps_total = day_with_surplus['producer_surplus'].sum()
ps_avg = day_with_surplus['producer_surplus'].mean()
ps_median = day_with_surplus['producer_surplus'].median()

col_ps1, col_ps2, col_ps3 = st.columns(3)
col_ps1.metric("Total Producer Surplus", f"PHP {ps_total:,.2f}")
col_ps2.metric("Avg Producer Surplus", f"PHP {ps_avg:,.2f}")
col_ps3.metric("Median Producer Surplus", f"PHP {ps_median:,.2f}")

plot_distribution_with_stats(day_with_surplus, 'producer_surplus',
                             "Producer Surplus Distribution", "Producer Surplus (PHP)", color="#e76f51")

## --- B7: Profitability Classification ---
st.subheader(f"Day {selected_day} — Driver Profitability")
st.markdown(
    "This section categorizes drivers based on how much they profit from their trips after "
    "accounting for gas and daily expenses:\n\n"
    "- **Profitable**: The driver earns enough to cover gas and daily expenses.\n"
    "- **Break-even**: The driver earns enough to cover gas, but not daily expenses.\n"
    "- **Not Profitable**: The driver earns less than the cost of gas."
)

income_mode_prof = st.radio(
    "Income type",
    options=["Negotiated Income", "Fixed Income (Base Price)"],
    horizontal=True,
    key="perday_prof_income_toggle"
)
use_fixed_prof = income_mode_prof == "Fixed Income (Base Price)"

day_prof = daily_profitability_df[daily_profitability_df['run_id'] == selected_day]
if not day_prof.empty:
    prof_row = day_prof.iloc[0]
    total_d = int(prof_row['total_drivers'])

    day_prof_prefix = 'fixed_' if use_fixed_prof and 'fixed_covers_all' in prof_row.index else ''

    fig_viab, ax_viab = plt.subplots(figsize=(8, 1.8))
    colors_viab = {
        "Covers All Expenses": "#2a9d8f",
        "Covers Gas Only": "#e9c46a",
        "Not Viable": "#e76f51"
    }

    left = 0
    for group, count_key, pct_key in [
        ("Covers All Expenses", f'{day_prof_prefix}covers_all', f'{day_prof_prefix}pct_covers_all'),
        ("Covers Gas Only", f'{day_prof_prefix}covers_gas', f'{day_prof_prefix}pct_covers_gas'),
        ("Not Viable", f'{day_prof_prefix}not_viable', f'{day_prof_prefix}pct_not_viable'),
    ]:
        pct = prof_row[pct_key] / 100
        count = int(prof_row[count_key])
        ax_viab.barh(0, pct, left=left, color=colors_viab[group], label=group)
        if pct > 0:
            ax_viab.text(left + pct / 2, 0, f"{count}/{total_d}",
                         va='center', ha='center', fontsize=9,
                         color="white" if group != "Covers Gas Only" else "black")
        left += pct

    prof_label = "Fixed" if use_fixed_prof and day_prof_prefix else "Negotiated"
    ax_viab.set_xlim(0, 1)
    ax_viab.set_yticks([])
    ax_viab.set_title(f"Proportion of Drivers by Viability Group ({prof_label})", fontsize=10)
    ax_viab.legend()
    st.pyplot(fig_viab)

## --- B8: Income Inequality ---
st.subheader(f"Day {selected_day} — Income Inequality")
st.markdown(
    "The Gini coefficient measures how unevenly income is distributed among drivers. "
    "It is derived from the Lorenz curve, which plots cumulative share of drivers against cumulative share of income. \n\n"

    "**Computation:**\n"
    "`Gini = Area between line of equality and Lorenz curve / Total area under equality line`\n\n"

    "- **0 → Perfect equality** (all drivers earn the same income).\n"
    "- **1 → Maximum inequality** (one driver earns all the income).\n\n"

    "Three variants are shown:\n"
    "- **Gross Income**: Total income before any expenses.\n"
    "- **After Gas**: Income minus gas expenses only.\n"
    "- **Net Profit**: Income minus all expenses (gas + daily)."
)

# Compute gini for this day
day_gross_income = day_transactions.groupby('trike_id')['price'].sum().reset_index(name='gross_income')
day_gas_exp = day_expenses[day_expenses['expense_type'] == 'gas'].groupby('trike_id')['amount'].sum().reset_index(name='gas_expenses')
day_all_exp = day_expenses.groupby('trike_id')['amount'].sum().reset_index(name='all_expenses')

day_inequality = day_gross_income.copy()
day_inequality = pd.merge(day_inequality, day_gas_exp, on='trike_id', how='left')
day_inequality = pd.merge(day_inequality, day_all_exp, on='trike_id', how='left')
day_inequality.fillna(0, inplace=True)
day_inequality['after_gas_profit'] = day_inequality['gross_income'] - day_inequality['gas_expenses']
day_inequality['net_profit'] = day_inequality['gross_income'] - day_inequality['all_expenses']

gini_gross = gini(day_inequality['gross_income'])
gini_after_gas = gini(day_inequality['after_gas_profit'])
gini_net = gini(day_inequality['net_profit'])

col_g1, col_g2, col_g3 = st.columns(3)
col_g1.metric("Gini (Gross Income)", f"{gini_gross:.3f}")
col_g2.metric("Gini (After Gas)", f"{gini_after_gas:.3f}")
col_g3.metric("Gini (Net Profit)", f"{gini_net:.3f}")

# Combined Lorenz curves
fig_lorenz, ax_lorenz = plt.subplots(figsize=(7, 7))

datasets_lorenz = [
    (day_inequality['gross_income'], "Gross Income", gini_gross),
    (day_inequality['after_gas_profit'], "After Gas", gini_after_gas),
    (day_inequality['net_profit'], "Net Profit", gini_net),
]

colors_lorenz = ['blue', 'orange', 'green']

for (data, label, g_val), color in zip(datasets_lorenz, colors_lorenz):
    if data.sum() > 0:
        x, y = lorenz_curve(data)
        ax_lorenz.plot(x, y, label=f"{label} (Gini: {g_val:.3f})", color=color)

ax_lorenz.plot([0, 1], [0, 1], linestyle="--", color='black', label="Perfect Equality")
ax_lorenz.set_xlabel("Cumulative Share of Drivers")
ax_lorenz.set_ylabel("Cumulative Share of Income / Profit")
ax_lorenz.set_title(f"Lorenz Curves — Day {selected_day}")
ax_lorenz.legend()
ax_lorenz.grid(True)
fig_lorenz.tight_layout()

st.pyplot(fig_lorenz, use_container_width=True)
