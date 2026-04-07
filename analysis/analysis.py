"""Module for analyzing and visualizing simulation results.

This module provides an exploration dashboard from the output simulation data,
which saves in the *analysis* folder by default. By default, this dashboard
shows data by-run and by-scenario, and also runs it through analysis by
means of statistical metrics and economic indicators.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import re

from scipy import stats

# Set page config for a wider layout
st.set_page_config(layout="wide")

# Use a nice seaborn theme
sns.set_theme(style="whitegrid")

## --- Helper Functions ---

# Regex to find numbers in the amount column (handles floats, ints)
AMOUNT_REGEX = re.compile(r"[-+]?\d*\.\d+|\d+")


def extract_amount(amount_str: str | float | int):
    """Extract number from a string formatted with brackets or other text.
    
    :param amount_str: String, int, or float amount value.
    :type amount_str: str | float | int
    :return: Float value of the amount, or pd.NA if extraction fails.
    :rtype: float
    """
    if isinstance(amount_str, (int, float)):
        return amount_str
    if not isinstance(amount_str, str):
        return pd.NA

    match = AMOUNT_REGEX.search(amount_str)
    if match:
        return float(match.group(0))
    return pd.NA


def plot_distribution_with_stats(data: pd.DataFrame, x_col: str, title: str, 
                                 xlabel: str, ylabel: str = "Count", 
                                 color: str = "skyblue", bins: int = 30) -> None:
    """Plot a distribution histogram.
    
    Creates a histogram with KDE overlay and adds a text box showing
    mean, median, mode, and standard deviation.
    
    :param data: DataFrame containing the data.
    :type data: pd.DataFrame
    :param x_col: Column name to plot.
    :type x_col: str
    :param title: Plot title.
    :type title: str
    :param xlabel: Label for x-axis.
    :type xlabel: str
    :param ylabel: Label for y-axis. Defaults to "Count".
    :type ylabel: str
    :param color: Color for histogram bars. Defaults to "skyblue".
    :type color: str
    :param bins: Number of histogram bins. Defaults to 30.
    :type bins: int
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


def ticks_to_time(ticks: int) -> str:
    """Convert simulation ticks (seconds) to human-readable time format.
    
    :param ticks: Number of ticks/seconds.
    :type ticks: int
    :return: String in HH:MM:SS format.
    :rtype: str
    """

    if pd.isna(ticks) or ticks is None:
        return "N/A"
    ticks = int(ticks)
    hours = (ticks // 3600) + 6
    minutes = (ticks % 3600) // 60
    seconds = ticks % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def ticks_to_hours(ticks):
    """Convert ticks to hours (for duration display).
    
    :param ticks: Number of ticks/seconds.
    :return: Duration in hours as a float.
    :rtype: float
    """
    if pd.isna(ticks) or ticks is None:
        return 0
    return ticks / 3600

def gini(series):
    """Compute Gini coefficient from a series of values.
    
    :param series: Series of numerical values.
    :return: Gini coefficient as a float.
    :rtype: float
    """
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
    """Compute Lorenz curve coordinates.
    
    :param data_series: Series of values to compute for.
    :return: Tuple of (x_coordinates, y_coordinates) for Lorenz curve.
    :rtype: tuple
    """
    sorted_series = data_series.sort_values()
    cumulative = sorted_series.cumsum()
    total = sorted_series.sum()
    lorenz_y = cumulative / total
    lorenz_x = np.arange(1, len(lorenz_y) + 1) / len(lorenz_y)
    return lorenz_x, lorenz_y

def classify_driver(row):
    """Classify driver viability based on income vs expenses.
    
    :param row: Data row with income and expense columns.
    :return: Classification string indicating driver viability.
    :rtype: str
    """
    if row['daily_income'] >= row['daily_expenses']:
        return "Covers All Expenses"
    elif row['daily_income'] >= row['gas_expenses']:
        return "Covers Gas Only"
    else:
        return "Not Viable"

# Default values for surplus calculations
DEFAULT_GAS_PRICE = 1.50
DEFAULT_GAS_CONSUMPTION = 24.41


## --- Data Loading Functions ---

def load_scenario_data(log_directory):
    """Load all simulation data from a scenario directory.
    
    :param log_directory: Path to the directory containing simulation logs.
    :type log_directory: str
    :return: Tuple of (df_all, df_expenses, df_drivers, df_trip_summary_list, sim_count, feature_flags).
    :rtype: tuple
    """
    all_folders = []
    if os.path.isdir(log_directory):
        all_items = sorted(os.listdir(log_directory))
        all_folders = [item for item in all_items if os.path.isdir(os.path.join(log_directory, item))]

    df_all_list = []
    df_expenses_list = []
    df_drivers_list = []
    df_trip_summary_list = []
    sim_count = 0

    for folder in all_folders:
        folder_path = os.path.join(log_directory, folder)
        run_id = folder

        drivers_file = os.path.join(folder_path, "drivers.csv")
        transactions_file = os.path.join(folder_path, "transactions.csv")
        expenses_file = os.path.join(folder_path, "expenses.csv")

        if not all(os.path.exists(f) for f in [drivers_file, transactions_file, expenses_file]):
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
        except Exception:
            continue

    if sim_count == 0:
        return None, None, None, [], 0

    df_all = pd.concat(df_all_list, ignore_index=True)
    df_all_expenses = pd.concat(df_expenses_list, ignore_index=True)
    df_all_drivers = pd.concat(df_drivers_list, ignore_index=True) if df_drivers_list else pd.DataFrame()

    df_all_expenses.dropna(subset=['amount'], inplace=True)

    # Handle potential duplicate columns from merge
    if 'run_id_x' in df_all.columns:
        df_all['run_id'] = df_all['run_id_x']
    if 'run_id_y' in df_all.columns and 'run_id' not in df_all.columns:
        df_all['run_id'] = df_all['run_id_y']

    return df_all, df_all_expenses, df_all_drivers, df_trip_summary_list, sim_count


def compute_daily_summary(df_all, df_all_expenses, df_all_drivers, df_trip_summary_list,
                           gas_price=DEFAULT_GAS_PRICE, gas_consumption=DEFAULT_GAS_CONSUMPTION):
    """Compute daily summary, gini, surplus, profitability from loaded data.
    Returns (daily_summary, daily_profitability_df, feature_flags_dict)
    """
    has_asp_data = 'driver_asp' in df_all.columns and 'passenger_asp' in df_all.columns
    has_base_price = 'base_price' in df_all.columns
    has_trip_summary = len(df_trip_summary_list) > 0

    all_run_ids = sorted(df_all['run_id'].unique())

    # Daily trips aggregation
    agg_dict = {'price': ['sum', 'count'], 'distance': 'sum'}
    if has_base_price:
        agg_dict['base_price'] = 'sum'

    daily_trips = df_all.groupby('run_id').agg(agg_dict).reset_index()
    if has_base_price:
        daily_trips.columns = ['run_id', 'total_income', 'total_trips', 'total_distance', 'total_fixed_income']
    else:
        daily_trips.columns = ['run_id', 'total_income', 'total_trips', 'total_distance']
        daily_trips['total_fixed_income'] = 0

    # Recalculate gas expenses from driver distance using sidebar gas_price and fixed 24.41 km/L
    driver_gas = df_all_drivers.copy()
    driver_gas['recalc_gas'] = driver_gas['daily_distance'] / 1000 / gas_consumption * gas_price
    daily_gas_agg = driver_gas.groupby('run_id')['recalc_gas'].sum().reset_index()
    daily_gas_agg.columns = ['run_id', 'total_gas_expenses']

    # Non-gas (daily fixed) expenses from logged data
    daily_non_gas = df_all_expenses[df_all_expenses['expense_type'] == 'daily_expense'].groupby('run_id')['amount'].sum().reset_index()
    daily_non_gas.columns = ['run_id', 'total_daily_expenses']

    daily_drivers_agg = df_all_drivers.groupby('run_id')['trike_id'].nunique().reset_index()
    daily_drivers_agg.columns = ['run_id', 'active_drivers']

    daily_summary = pd.merge(daily_trips, daily_gas_agg, on='run_id', how='left')
    daily_summary = pd.merge(daily_summary, daily_non_gas, on='run_id', how='left')
    daily_summary = pd.merge(daily_summary, daily_drivers_agg, on='run_id', how='left')
    daily_summary.fillna(0, inplace=True)

    daily_summary['total_expenses'] = daily_summary['total_gas_expenses'] + daily_summary['total_daily_expenses']
    daily_summary['total_profit'] = daily_summary['total_income'] - daily_summary['total_expenses']
    daily_summary['total_fixed_profit'] = daily_summary['total_fixed_income'] - daily_summary['total_expenses']
    daily_summary['avg_income_per_driver'] = daily_summary['total_income'] / daily_summary['active_drivers'].replace(0, np.nan)
    daily_summary['avg_fixed_income_per_driver'] = daily_summary['total_fixed_income'] / daily_summary['active_drivers'].replace(0, np.nan)
    daily_summary['avg_trips_per_driver'] = daily_summary['total_trips'] / daily_summary['active_drivers'].replace(0, np.nan)
    daily_summary['avg_profit_per_driver'] = daily_summary['total_profit'] / daily_summary['active_drivers'].replace(0, np.nan)
    daily_summary['avg_fixed_profit_per_driver'] = daily_summary['total_fixed_profit'] / daily_summary['active_drivers'].replace(0, np.nan)

    daily_summary = daily_summary.sort_values('run_id').reset_index(drop=True)

    # Gini per day
    daily_gini = []
    for run in all_run_ids:
        run_transactions = df_all[df_all['run_id'] == run]
        run_income = run_transactions.groupby('trike_id')['price'].sum()
        row_data = {'run_id': run, 'gini_gross_income': gini(run_income)}
        if has_base_price:
            run_fixed_income = run_transactions.groupby('trike_id')['base_price'].sum()
            row_data['gini_fixed_income'] = gini(run_fixed_income)
        else:
            row_data['gini_fixed_income'] = 0.0
        daily_gini.append(row_data)

    daily_gini_df = pd.DataFrame(daily_gini)
    daily_summary = pd.merge(daily_summary, daily_gini_df, on='run_id', how='left')

    # Gini of bargaining gaps per day
    if has_asp_data:
        daily_bargaining_gini = []
        for run in all_run_ids:
            run_transactions = df_all[df_all['run_id'] == run]
            asp_valid = run_transactions.dropna(subset=['driver_asp', 'passenger_asp'])
            if not asp_valid.empty:
                gaps = asp_valid['driver_asp'] - asp_valid['passenger_asp']
                daily_bargaining_gini.append({'run_id': run, 'gini_bargaining_gap': gini(gaps)})
            else:
                daily_bargaining_gini.append({'run_id': run, 'gini_bargaining_gap': np.nan})
        daily_bargaining_gini_df = pd.DataFrame(daily_bargaining_gini)
        daily_summary = pd.merge(daily_summary, daily_bargaining_gini_df, on='run_id', how='left')

    # Surplus per day
    if has_asp_data:
        df_all['passenger_surplus'] = df_all['passenger_asp'] - df_all['price']
    else:
        df_all['passenger_surplus'] = np.nan

    df_all['marginal_cost'] = (df_all['distance'] * gas_price) / (1000 * gas_consumption)
    df_all['producer_surplus'] = df_all['price'] - df_all['marginal_cost']
    if has_base_price:
        df_all['fixed_producer_surplus'] = df_all['base_price'] - df_all['marginal_cost']

    daily_surplus = df_all.groupby('run_id').agg(
        avg_consumer_surplus=('passenger_surplus', 'mean'),
        avg_producer_surplus=('producer_surplus', 'mean'),
        total_consumer_surplus=('passenger_surplus', 'sum'),
        total_producer_surplus=('producer_surplus', 'sum'),
    ).reset_index()
    if has_base_price:
        daily_fixed_surplus = df_all.groupby('run_id').agg(
            avg_fixed_producer_surplus=('fixed_producer_surplus', 'mean'),
            total_fixed_producer_surplus=('fixed_producer_surplus', 'sum'),
        ).reset_index()
        daily_surplus = pd.merge(daily_surplus, daily_fixed_surplus, on='run_id', how='left')
    daily_summary = pd.merge(daily_summary, daily_surplus, on='run_id', how='left')

    # Gini of producer and consumer surplus per day
    daily_surplus_gini = []
    for run in all_run_ids:
        run_transactions = df_all[df_all['run_id'] == run]
        ps_by_driver = run_transactions.groupby('trike_id')['producer_surplus'].sum()
        row_data = {'run_id': run, 'gini_producer_surplus': gini(ps_by_driver)}
        if has_base_price:
            fps_by_driver = run_transactions.groupby('trike_id')['fixed_producer_surplus'].sum()
            row_data['gini_fixed_producer_surplus'] = gini(fps_by_driver)
        if has_asp_data:
            cs_valid = run_transactions.dropna(subset=['passenger_surplus'])
            row_data['gini_consumer_surplus'] = gini(cs_valid['passenger_surplus']) if not cs_valid.empty else np.nan
        daily_surplus_gini.append(row_data)
    daily_surplus_gini_df = pd.DataFrame(daily_surplus_gini)
    daily_summary = pd.merge(daily_summary, daily_surplus_gini_df, on='run_id', how='left')

    # Trip dispatch
    if has_trip_summary:
        df_trip_summary = pd.concat(df_trip_summary_list, ignore_index=True)
        summary_pivot = df_trip_summary.pivot(index='run_id', columns='metric', values='count').reset_index()
        if 'accepted_trips' in summary_pivot.columns and 'rejected_trips' in summary_pivot.columns:
            summary_pivot['total_attempts'] = summary_pivot['accepted_trips'] + summary_pivot['rejected_trips']
            summary_pivot['acceptance_rate'] = (summary_pivot['accepted_trips'] / summary_pivot['total_attempts'] * 100).round(1)
            daily_summary = pd.merge(daily_summary, summary_pivot[['run_id', 'accepted_trips', 'rejected_trips', 'total_attempts', 'acceptance_rate']], on='run_id', how='left')

    # Profitability per day
    daily_profitability = []
    for run in all_run_ids:
        run_transactions = df_all[df_all['run_id'] == run]
        run_expenses = df_all_expenses[df_all_expenses['run_id'] == run]

        run_income = run_transactions.groupby('trike_id')['price'].sum().reset_index(name='daily_income')
        run_fixed_income = run_transactions.groupby('trike_id')['base_price'].sum().reset_index(name='daily_income') if has_base_price else None

        # Recalculate gas expenses from driver distance
        run_driver_data = df_all_drivers[df_all_drivers['run_id'] == run]
        run_gas = run_driver_data[['trike_id', 'daily_distance']].copy()
        run_gas['gas_expenses'] = run_gas['daily_distance'] / 1000 / gas_consumption * gas_price
        run_gas = run_gas[['trike_id', 'gas_expenses']]

        # Non-gas (daily fixed) expenses from logged data
        run_daily_exp = run_expenses[run_expenses['expense_type'] == 'daily_expense'].groupby('trike_id')['amount'].sum().reset_index(name='fixed_daily_expenses')
        run_all_exp = pd.merge(run_gas, run_daily_exp, on='trike_id', how='outer')
        run_all_exp.fillna(0, inplace=True)
        run_all_exp['daily_expenses'] = run_all_exp['gas_expenses'] + run_all_exp['fixed_daily_expenses']
        run_all_exp = run_all_exp[['trike_id', 'daily_expenses']]

        run_drivers = run_transactions['trike_id'].drop_duplicates()

        viability = run_drivers.to_frame()
        viability = pd.merge(viability, run_income, on='trike_id', how='left')
        viability = pd.merge(viability, run_gas, on='trike_id', how='left')
        viability = pd.merge(viability, run_all_exp, on='trike_id', how='left')
        viability.fillna(0, inplace=True)
        viability['net_profit'] = viability['daily_income'] - viability['daily_expenses']
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
            'gini_net_profit': gini(viability['net_profit']),
        }

        if run_fixed_income is not None:
            viability_fixed = run_drivers.to_frame()
            viability_fixed = pd.merge(viability_fixed, run_fixed_income, on='trike_id', how='left')
            viability_fixed = pd.merge(viability_fixed, run_gas, on='trike_id', how='left')
            viability_fixed = pd.merge(viability_fixed, run_all_exp, on='trike_id', how='left')
            viability_fixed.fillna(0, inplace=True)
            viability_fixed['net_profit'] = viability_fixed['daily_income'] - viability_fixed['daily_expenses']
            viability_fixed['viability_group'] = viability_fixed.apply(classify_driver, axis=1)

            counts_fixed = viability_fixed['viability_group'].value_counts().reindex(ordered_groups, fill_value=0)
            row_data['fixed_covers_all'] = counts_fixed.get("Covers All Expenses", 0)
            row_data['fixed_covers_gas'] = counts_fixed.get("Covers Gas Only", 0)
            row_data['fixed_not_viable'] = counts_fixed.get("Not Viable", 0)
            row_data['fixed_pct_covers_all'] = (counts_fixed.get("Covers All Expenses", 0) / total * 100) if total > 0 else 0
            row_data['fixed_pct_covers_gas'] = (counts_fixed.get("Covers Gas Only", 0) / total * 100) if total > 0 else 0
            row_data['fixed_pct_not_viable'] = (counts_fixed.get("Not Viable", 0) / total * 100) if total > 0 else 0
            row_data['gini_fixed_net_profit'] = gini(viability_fixed['net_profit'])

        daily_profitability.append(row_data)

    daily_profitability_df = pd.DataFrame(daily_profitability)

    return daily_summary, daily_profitability_df


## --- Sidebar Configuration ---
st.sidebar.header("Analysis Configuration")

gas_price = st.sidebar.number_input(
    "Gas Price (per liter)",
    min_value=0.0,
    value=DEFAULT_GAS_PRICE,
    step=0.10,
    format="%.2f",
    key="gas_price_input"
)
gas_consumption = st.sidebar.number_input(
    "Gas Consumption (km/L)",
    min_value=0.01,
    value=DEFAULT_GAS_CONSUMPTION,
    step=0.5,
    format="%.2f",
    key="gas_consumption_input"
)

existing_logs = [
    d for d in os.listdir(".")
    if os.path.isdir(os.path.join(".", d))
]

if not existing_logs:
    st.error("No log directories found. Please check your folder structure.")
    st.stop()

view_mode = st.sidebar.radio(
    "View Mode",
    options=["Per-Scenario View", "Cross-Scenario Comparison"],
    key="view_mode_toggle"
)

## ============================================================
## PER-SCENARIO VIEW
## ============================================================

if view_mode == "Per-Scenario View":
    LOG_DIRECTORY = st.sidebar.selectbox(
        "Select Log Directory to Analyze",
        options=existing_logs,
        index=0
    )

    if not os.path.isdir(LOG_DIRECTORY):
        st.error(f"Selected log directory '{LOG_DIRECTORY}' does not exist or is not a directory.")
        st.stop()

    df_all, df_all_expenses, df_all_drivers, df_trip_summary_list, sim_count = load_scenario_data(LOG_DIRECTORY)

    if sim_count == 0:
        st.warning("No simulation data was successfully loaded. Check the log directory and file contents.")
        st.stop()

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

    daily_summary, daily_profitability_df = compute_daily_summary(df_all, df_all_expenses, df_all_drivers, df_trip_summary_list, gas_price, gas_consumption)

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

    # --- Overall Averages ---
    trips_per_driver = daily_summary['total_trips'] / daily_summary['active_drivers']

    with st.expander("Overall Averages Across All Days", expanded=False):
        st.markdown("**Negotiated Income**")
        oa_n1, oa_n2, oa_n3, oa_n4, oa_n5 = st.columns(5)
        oa_n1.metric("Avg Total Income", f"PHP {daily_summary['total_income'].mean():,.2f}")
        oa_n2.metric("Avg Total Expenses", f"PHP {daily_summary['total_expenses'].mean():,.2f}")
        oa_n3.metric("Avg Total Profit", f"PHP {daily_summary['total_profit'].mean():,.2f}")
        oa_n4.metric("Avg Trips/Driver/Day", f"{trips_per_driver.mean():,.1f}")
        oa_n5.metric("Avg Active Drivers/Day", f"{daily_summary['active_drivers'].mean():,.1f}")

        oa_n6, oa_n7 = st.columns(2)
        oa_n6.metric("Avg Income/Driver", f"PHP {daily_summary['avg_income_per_driver'].mean():,.2f}")
        oa_n7.metric("Avg Profit/Driver", f"PHP {daily_summary['avg_profit_per_driver'].mean():,.2f}")

        st.markdown("**Fixed Income (Base Price)**")
        oa_f1, oa_f2, oa_f3, oa_f4, oa_f5 = st.columns(5)
        oa_f1.metric("Avg Total Income", f"PHP {daily_summary['total_fixed_income'].mean():,.2f}")
        oa_f2.metric("Avg Total Expenses", f"PHP {daily_summary['total_expenses'].mean():,.2f}")
        oa_f3.metric("Avg Total Profit", f"PHP {daily_summary['total_fixed_profit'].mean():,.2f}")
        oa_f4.metric("Avg Trips/Driver/Day", f"{trips_per_driver.mean():,.1f}")
        oa_f5.metric("Avg Active Drivers/Day", f"{daily_summary['active_drivers'].mean():,.1f}")

        oa_f6, oa_f7 = st.columns(2)
        oa_f6.metric("Avg Income/Driver", f"PHP {daily_summary['avg_fixed_income_per_driver'].mean():,.2f}")
        oa_f7.metric("Avg Profit/Driver", f"PHP {daily_summary['avg_fixed_profit_per_driver'].mean():,.2f}")

        oa2_col1, oa2_col2, oa2_col3, oa2_col4, oa2_col5, oa2_col6 = st.columns(6)
        oa2_col1.metric("Avg Gini (Gross)", f"{daily_summary['gini_gross_income'].mean():.4f}")
        oa2_col2.metric("Avg Gini (Fixed)", f"{daily_summary['gini_fixed_income'].mean():.4f}")
        oa2_col3.metric("Avg Gini (Net Profit)", f"{daily_profitability_df['gini_net_profit'].mean():.4f}")
        if 'gini_fixed_net_profit' in daily_profitability_df.columns:
            oa2_col4.metric("Avg Gini (Fixed Net Profit)", f"{daily_profitability_df['gini_fixed_net_profit'].mean():.4f}")
        if 'gini_producer_surplus' in daily_summary.columns:
            oa2_col5.metric("Avg Gini (Producer Surplus)", f"{daily_summary['gini_producer_surplus'].mean():.4f}")
        if 'gini_consumer_surplus' in daily_summary.columns:
            oa2_col6.metric("Avg Gini (Consumer Surplus)", f"{daily_summary['gini_consumer_surplus'].mean():.4f}")

        if 'gini_fixed_producer_surplus' in daily_summary.columns:
            oa2c_col1, = st.columns(1)
            oa2c_col1.metric("Avg Gini (Fixed Producer Surplus)", f"{daily_summary['gini_fixed_producer_surplus'].mean():.4f}")

        oa2b_col1, = st.columns(1)
        if 'gini_bargaining_gap' in daily_summary.columns:
            oa2b_col1.metric("Avg Gini (Bargaining Gap)", f"{daily_summary['gini_bargaining_gap'].mean():.4f}")

        oa3_col1, oa3_col2, oa3_col3, oa3_col4 = st.columns(4)
        if 'total_consumer_surplus' in daily_summary.columns:
            oa3_col1.metric("Avg Total Consumer Surplus", f"PHP {daily_summary['total_consumer_surplus'].mean():,.2f}")
        if 'total_producer_surplus' in daily_summary.columns:
            oa3_col2.metric("Avg Total Producer Surplus", f"PHP {daily_summary['total_producer_surplus'].mean():,.2f}")
        if 'total_fixed_producer_surplus' in daily_summary.columns:
            oa3_col3.metric("Avg Total Fixed Producer Surplus", f"PHP {daily_summary['total_fixed_producer_surplus'].mean():,.2f}")
        if 'total_producer_surplus' in daily_summary.columns and 'total_consumer_surplus' in daily_summary.columns:
            avg_total_surplus = (daily_summary['total_producer_surplus'] + daily_summary['total_consumer_surplus']).mean()
            oa3_col4.metric("Avg Total Surplus", f"PHP {avg_total_surplus:,.2f}")

    # Compute per-driver profit per day (used by multiple sections)
    driver_income = df_all.groupby(['run_id', 'trike_id']).agg(
        negotiated_income=('price', 'sum'),
        fixed_income=('base_price', 'sum') if has_base_price else ('price', 'sum'),
        trips=('price', 'count'),
    ).reset_index()
    # Recalculate gas expenses from driver distance
    driver_gas = df_all_drivers[['run_id', 'trike_id', 'daily_distance']].copy()
    driver_gas['gas_expenses'] = driver_gas['daily_distance'] / 1000 / gas_consumption * gas_price
    driver_fixed_exp = df_all_expenses[df_all_expenses['expense_type'] == 'daily_expense'].groupby(['run_id', 'trike_id'])['amount'].sum().reset_index(name='fixed_daily_expenses')
    driver_expenses = pd.merge(driver_gas[['run_id', 'trike_id', 'gas_expenses']], driver_fixed_exp, on=['run_id', 'trike_id'], how='outer')
    driver_expenses.fillna(0, inplace=True)
    driver_expenses['expenses'] = driver_expenses['gas_expenses'] + driver_expenses['fixed_daily_expenses']
    driver_daily = pd.merge(driver_income, driver_expenses[['run_id', 'trike_id', 'gas_expenses', 'expenses']], on=['run_id', 'trike_id'], how='left')
    driver_daily['expenses'] = driver_daily['expenses'].fillna(0)
    driver_daily['gas_expenses'] = driver_daily['gas_expenses'].fillna(0)
    driver_daily['negotiated_profit'] = driver_daily['negotiated_income'] - driver_daily['expenses']
    driver_daily['fixed_profit'] = driver_daily['fixed_income'] - driver_daily['expenses']
    driver_daily['negotiated_profit_gas_only'] = driver_daily['negotiated_income'] - driver_daily['gas_expenses']
    driver_daily['fixed_profit_gas_only'] = driver_daily['fixed_income'] - driver_daily['gas_expenses']

    # Best and worst driver overall
    best_neg = driver_daily.loc[driver_daily['negotiated_profit'].idxmax()]
    worst_neg = driver_daily.loc[driver_daily['negotiated_profit'].idxmin()]
    best_fix = driver_daily.loc[driver_daily['fixed_profit'].idxmax()]
    worst_fix = driver_daily.loc[driver_daily['fixed_profit'].idxmin()]

    with st.expander("Best & Worst Performing Drivers", expanded=False):
        perf_table = pd.DataFrame({
            'Day': [
                best_neg['run_id'], worst_neg['run_id'],
                best_fix['run_id'], worst_fix['run_id'],
            ],
            'Driver': [
                best_neg['trike_id'], worst_neg['trike_id'],
                best_fix['trike_id'], worst_fix['trike_id'],
            ],
            'Income': [
                f"PHP {best_neg['negotiated_income']:,.2f}",
                f"PHP {worst_neg['negotiated_income']:,.2f}",
                f"PHP {best_fix['fixed_income']:,.2f}",
                f"PHP {worst_fix['fixed_income']:,.2f}",
            ],
            'Expenses': [
                f"PHP {best_neg['expenses']:,.2f}",
                f"PHP {worst_neg['expenses']:,.2f}",
                f"PHP {best_fix['expenses']:,.2f}",
                f"PHP {worst_fix['expenses']:,.2f}",
            ],
            'Profit': [
                f"PHP {best_neg['negotiated_profit']:,.2f}",
                f"PHP {worst_neg['negotiated_profit']:,.2f}",
                f"PHP {best_fix['fixed_profit']:,.2f}",
                f"PHP {worst_fix['fixed_profit']:,.2f}",
            ],
            'Trips': [
                f"{best_neg['trips']:.0f}",
                f"{worst_neg['trips']:.0f}",
                f"{best_fix['trips']:.0f}",
                f"{worst_fix['trips']:.0f}",
            ],
        }, index=[
            'Best (Negotiated)',
            'Worst (Negotiated)',
            'Best (Fixed)',
            'Worst (Fixed)',
        ])
        st.table(perf_table)

    with st.expander("Avg Driver Profitability Per Day", expanded=False):
        oa3_col1, oa3_col2, oa3_col3 = st.columns(3)
        oa3_col1.metric("Covers All (Negotiated)", f"{daily_profitability_df['pct_covers_all'].mean():,.1f}%")
        oa3_col2.metric("Covers Gas Only (Negotiated)", f"{daily_profitability_df['pct_covers_gas'].mean():,.1f}%")
        oa3_col3.metric("Not Viable (Negotiated)", f"{daily_profitability_df['pct_not_viable'].mean():,.1f}%")

        if 'fixed_pct_covers_all' in daily_profitability_df.columns:
            oa4_col1, oa4_col2, oa4_col3 = st.columns(3)
            oa4_col1.metric("Covers All (Fixed)", f"{daily_profitability_df['fixed_pct_covers_all'].mean():,.1f}%")
            oa4_col2.metric("Covers Gas Only (Fixed)", f"{daily_profitability_df['fixed_pct_covers_gas'].mean():,.1f}%")
            oa4_col3.metric("Not Viable (Fixed)", f"{daily_profitability_df['fixed_pct_not_viable'].mean():,.1f}%")

    st.divider()

    # --- A1: Income, Expenses, Profit trend (both Negotiated and Fixed) ---
    st.subheader("Income, Expenses & Profit Across Days")

    col_trend_neg, col_trend_fix = st.columns(2)

    with col_trend_neg:
        fig_trend_n, ax_trend_n = plt.subplots(figsize=(6, 4))
        ax_trend_n.plot(daily_summary['run_id'], daily_summary['total_income'], marker='o', label='Total Income', color='#2a9d8f')
        ax_trend_n.plot(daily_summary['run_id'], daily_summary['total_expenses'], marker='s', label='Total Expenses', color='#e76f51')
        ax_trend_n.plot(daily_summary['run_id'], daily_summary['total_profit'], marker='^', label='Total Profit', color='#264653')
        ax_trend_n.set_xlabel("Day (Run ID)")
        ax_trend_n.set_ylabel("PHP")
        ax_trend_n.set_title("Daily Negotiated Income, Expenses & Profit")
        ax_trend_n.legend()
        ax_trend_n.tick_params(axis='x', rotation=45)
        fig_trend_n.tight_layout()
        st.pyplot(fig_trend_n, use_container_width=True)

    with col_trend_fix:
        fig_trend_f, ax_trend_f = plt.subplots(figsize=(6, 4))
        ax_trend_f.plot(daily_summary['run_id'], daily_summary['total_fixed_income'], marker='o', label='Total Income', color='#2a9d8f')
        ax_trend_f.plot(daily_summary['run_id'], daily_summary['total_expenses'], marker='s', label='Total Expenses', color='#e76f51')
        ax_trend_f.plot(daily_summary['run_id'], daily_summary['total_fixed_profit'], marker='^', label='Total Profit', color='#264653')
        ax_trend_f.set_xlabel("Day (Run ID)")
        ax_trend_f.set_ylabel("PHP")
        ax_trend_f.set_title("Daily Fixed Income, Expenses & Profit")
        ax_trend_f.legend()
        ax_trend_f.tick_params(axis='x', rotation=45)
        fig_trend_f.tight_layout()
        st.pyplot(fig_trend_f, use_container_width=True)

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

    # --- A3: Average driver income & profit per day (both types) ---
    st.subheader("Average Driver Income & Profit Per Day")

    col_avg_neg, col_avg_fix = st.columns(2)

    with col_avg_neg:
        fig_avg_n, ax_avg_n = plt.subplots(figsize=(6, 4))
        ax_avg_n.plot(daily_summary['run_id'], daily_summary['avg_income_per_driver'], marker='o', label='Avg Income/Driver', color='#2a9d8f')
        ax_avg_n.plot(daily_summary['run_id'], daily_summary['avg_profit_per_driver'], marker='s', label='Avg Profit/Driver', color='#264653')
        ax_avg_n.set_xlabel("Day (Run ID)")
        ax_avg_n.set_ylabel("PHP")
        ax_avg_n.set_title("Average Driver Negotiated Income & Profit Per Day")
        ax_avg_n.legend()
        ax_avg_n.tick_params(axis='x', rotation=45)
        fig_avg_n.tight_layout()
        st.pyplot(fig_avg_n, use_container_width=True)

    with col_avg_fix:
        fig_avg_f, ax_avg_f = plt.subplots(figsize=(6, 4))
        ax_avg_f.plot(daily_summary['run_id'], daily_summary['avg_fixed_income_per_driver'], marker='o', label='Avg Income/Driver', color='#2a9d8f')
        ax_avg_f.plot(daily_summary['run_id'], daily_summary['avg_fixed_profit_per_driver'], marker='s', label='Avg Profit/Driver', color='#264653')
        ax_avg_f.set_xlabel("Day (Run ID)")
        ax_avg_f.set_ylabel("PHP")
        ax_avg_f.set_title("Average Driver Fixed Income & Profit Per Day")
        ax_avg_f.legend()
        ax_avg_f.tick_params(axis='x', rotation=45)
        fig_avg_f.tight_layout()
        st.pyplot(fig_avg_f, use_container_width=True)

    # --- A4: Gini coefficient per day ---
    st.subheader("Income Inequality (Gini) Across Days")
    col_gini1, col_gini2 = st.columns(2)

    with col_gini1:
        fig_gini, ax_gini = plt.subplots(figsize=(6, 4))
        ax_gini.plot(daily_summary['run_id'], daily_summary['gini_gross_income'], marker='o', color='#e76f51', linewidth=2)
        ax_gini.set_xlabel("Day (Run ID)")
        ax_gini.set_ylabel("Gini Coefficient")
        ax_gini.set_title("Gini Coefficient (Gross Income) Per Day")
        ax_gini.set_ylim(0, max(0.5, daily_summary['gini_gross_income'].max() * 1.2))
        ax_gini.tick_params(axis='x', rotation=45)
        fig_gini.tight_layout()
        st.pyplot(fig_gini, use_container_width=True)

    with col_gini2:
        fig_gini_fixed, ax_gini_fixed = plt.subplots(figsize=(6, 4))
        ax_gini_fixed.plot(daily_summary['run_id'], daily_summary['gini_fixed_income'], marker='o', color='#2a9d8f', linewidth=2)
        ax_gini_fixed.set_xlabel("Day (Run ID)")
        ax_gini_fixed.set_ylabel("Gini Coefficient")
        ax_gini_fixed.set_title("Gini Coefficient (Fixed Income) Per Day")
        ax_gini_fixed.set_ylim(0, max(0.5, daily_summary['gini_fixed_income'].max() * 1.2))
        ax_gini_fixed.tick_params(axis='x', rotation=45)
        fig_gini_fixed.tight_layout()
        st.pyplot(fig_gini_fixed, use_container_width=True)

    if 'gini_fixed_net_profit' in daily_profitability_df.columns:
        col_gini3, col_gini4 = st.columns(2)

        with col_gini3:
            fig_gini_np, ax_gini_np = plt.subplots(figsize=(6, 4))
            ax_gini_np.plot(daily_profitability_df['run_id'], daily_profitability_df['gini_net_profit'], marker='o', color='#264653', linewidth=2)
            ax_gini_np.set_xlabel("Day (Run ID)")
            ax_gini_np.set_ylabel("Gini Coefficient")
            ax_gini_np.set_title("Gini Coefficient (Net Profit) Per Day")
            ax_gini_np.set_ylim(0, max(0.5, daily_profitability_df['gini_net_profit'].max() * 1.2))
            ax_gini_np.tick_params(axis='x', rotation=45)
            fig_gini_np.tight_layout()
            st.pyplot(fig_gini_np, use_container_width=True)

        with col_gini4:
            fig_gini_fnp, ax_gini_fnp = plt.subplots(figsize=(6, 4))
            ax_gini_fnp.plot(daily_profitability_df['run_id'], daily_profitability_df['gini_fixed_net_profit'], marker='o', color='#bc6c25', linewidth=2)
            ax_gini_fnp.set_xlabel("Day (Run ID)")
            ax_gini_fnp.set_ylabel("Gini Coefficient")
            ax_gini_fnp.set_title("Gini Coefficient (Fixed Net Profit) Per Day")
            ax_gini_fnp.set_ylim(0, max(0.5, daily_profitability_df['gini_fixed_net_profit'].max() * 1.2))
            ax_gini_fnp.tick_params(axis='x', rotation=45)
            fig_gini_fnp.tight_layout()
            st.pyplot(fig_gini_fnp, use_container_width=True)

    # --- A4b: Surplus Gini per day ---
    if 'gini_producer_surplus' in daily_summary.columns:
        st.subheader("Surplus Inequality (Gini) Across Days")
        col_sgini1, col_sgini2 = st.columns(2)

        with col_sgini1:
            fig_sg, ax_sg = plt.subplots(figsize=(6, 4))
            ax_sg.plot(daily_summary['run_id'], daily_summary['gini_producer_surplus'], marker='o', color='#e76f51', linewidth=2)
            ax_sg.set_xlabel("Day (Run ID)")
            ax_sg.set_ylabel("Gini Coefficient")
            ax_sg.set_title("Gini Coefficient (Producer Surplus) Per Day")
            ax_sg.set_ylim(0, max(0.5, daily_summary['gini_producer_surplus'].max() * 1.2))
            ax_sg.tick_params(axis='x', rotation=45)
            fig_sg.tight_layout()
            st.pyplot(fig_sg, use_container_width=True)

        with col_sgini2:
            if 'gini_fixed_producer_surplus' in daily_summary.columns:
                fig_fsg, ax_fsg = plt.subplots(figsize=(6, 4))
                ax_fsg.plot(daily_summary['run_id'], daily_summary['gini_fixed_producer_surplus'], marker='o', color='#bc6c25', linewidth=2)
                ax_fsg.set_xlabel("Day (Run ID)")
                ax_fsg.set_ylabel("Gini Coefficient")
                ax_fsg.set_title("Gini Coefficient (Fixed Producer Surplus) Per Day")
                ax_fsg.set_ylim(0, max(0.5, daily_summary['gini_fixed_producer_surplus'].max() * 1.2))
                ax_fsg.tick_params(axis='x', rotation=45)
                fig_fsg.tight_layout()
                st.pyplot(fig_fsg, use_container_width=True)

    # --- A5: Consumer & Producer surplus per day ---
    if has_asp_data:
        st.subheader("Average Surplus Across Days")
        fig_surplus, ax_surplus = plt.subplots(figsize=(10, 4))
        ax_surplus.plot(daily_summary['run_id'], daily_summary['avg_consumer_surplus'], marker='o', label='Avg Consumer Surplus', color='#2a9d8f')
        ax_surplus.plot(daily_summary['run_id'], daily_summary['avg_producer_surplus'], marker='s', label='Avg Producer Surplus', color='#e76f51')
        if 'avg_fixed_producer_surplus' in daily_summary.columns:
            ax_surplus.plot(daily_summary['run_id'], daily_summary['avg_fixed_producer_surplus'], marker='^', label='Avg Fixed Producer Surplus', color='#bc6c25')
        ax_surplus.set_xlabel("Day (Run ID)")
        ax_surplus.set_ylabel("PHP")
        ax_surplus.set_title("Average Consumer & Producer Surplus Per Day")
        ax_surplus.legend()
        ax_surplus.tick_params(axis='x', rotation=45)
        fig_surplus.tight_layout()
        st.pyplot(fig_surplus, use_container_width=True)

    # --- A5b: Cross-Day Bargaining Analytics Summary ---
    if has_asp_data:
        st.subheader("Bargaining Analytics Summary (All Days)")

        all_asp = df_all.dropna(subset=['driver_asp', 'passenger_asp']).copy()

        if not all_asp.empty:
            all_asp['asp_gap'] = all_asp['driver_asp'] - all_asp['passenger_asp']

            col_ba1, col_ba2, col_ba3, col_ba4 = st.columns(4)
            col_ba1.metric("Avg Driver ASP", f"PHP {all_asp['driver_asp'].mean():,.2f}")
            col_ba2.metric("Avg Passenger ASP", f"PHP {all_asp['passenger_asp'].mean():,.2f}")
            col_ba3.metric("Avg Agreed Price", f"PHP {all_asp['price'].mean():,.2f}")
            col_ba4.metric("Avg Bargaining Gap", f"PHP {all_asp['asp_gap'].mean():,.2f}")

            if has_init_asp_data:
                all_init = all_asp.dropna(subset=['init_driver_asp', 'init_passenger_asp'])
                if not all_init.empty:
                    all_init = all_init.copy()
                    all_init['driver_asp_change'] = all_init['driver_asp'] - all_init['init_driver_asp']
                    all_init['passenger_asp_change'] = all_init['passenger_asp'] - all_init['init_passenger_asp']
                    col_ia1, col_ia2, col_ia3, col_ia4 = st.columns(4)
                    col_ia1.metric("Avg Init Driver ASP", f"PHP {all_init['init_driver_asp'].mean():,.2f}")
                    col_ia2.metric("Avg Init Passenger ASP", f"PHP {all_init['init_passenger_asp'].mean():,.2f}")
                    col_ia3.metric("Avg Driver ASP Change", f"PHP {all_init['driver_asp_change'].mean():,.2f}")
                    col_ia4.metric("Avg Passenger ASP Change", f"PHP {all_init['passenger_asp_change'].mean():,.2f}")

            if has_base_price:
                base_data = all_asp.dropna(subset=['base_price'])
                if not base_data.empty:
                    col_bp1, col_bp2, col_bp3 = st.columns(3)
                    col_bp1.metric("Avg Base Price", f"PHP {base_data['base_price'].mean():,.2f}")
                    col_bp2.metric("Avg Agreed vs Base", f"PHP {(base_data['price'] - base_data['base_price']).mean():,.2f}")
                    col_bp3.metric("Avg Markup over Base", f"{((base_data['price'] / base_data['base_price'] - 1) * 100).mean():,.1f}%")

            # Sufficientarianism: Passenger Satisfaction Rate
            # Proportion of passengers whose willingness to pay (passenger_asp) >= agreed price
            all_asp['satisfied'] = all_asp['passenger_asp'] >= all_asp['price']
            satisfaction_rate = all_asp['satisfied'].mean() * 100

            # Per-day satisfaction rates for trend chart
            daily_satisfaction = all_asp.groupby('run_id')['satisfied'].mean().reset_index()
            daily_satisfaction.columns = ['run_id', 'satisfaction_rate']
            daily_satisfaction['satisfaction_rate'] *= 100

            st.markdown("---")
            st.markdown("**Sufficientarianism Metrics**")

            # Driver break-even rate (income >= total expenses)
            avg_breakeven = daily_profitability_df['pct_covers_all'].mean()

            col_sf1, col_sf2 = st.columns(2)
            col_sf1.metric("Passenger Satisfaction Rate", f"{satisfaction_rate:,.1f}%",
                           help="Average proportion of passengers whose willingness to pay exceeds the final agreed trip price.")
            col_sf2.metric("Driver Operational Break-even Rate", f"{avg_breakeven:,.1f}%",
                           help="Average proportion of drivers whose income exceeds their total expenses (gas + daily).")

            # Trend chart for both metrics
            fig_suf, ax_suf = plt.subplots(figsize=(10, 4))
            ax_suf.plot(daily_satisfaction['run_id'], daily_satisfaction['satisfaction_rate'],
                        marker='o', label='Passenger Satisfaction Rate', color='#2a9d8f')
            ax_suf.plot(daily_profitability_df['run_id'], daily_profitability_df['pct_covers_all'],
                        marker='s', label='Driver Break-even Rate', color='#264653')
            ax_suf.set_xlabel("Day (Run ID)")
            ax_suf.set_ylabel("%")
            ax_suf.set_title("Sufficientarianism Metrics Across Days")
            ax_suf.legend()
            ax_suf.set_ylim(0, 105)
            ax_suf.tick_params(axis='x', rotation=45)
            fig_suf.tight_layout()
            st.pyplot(fig_suf, use_container_width=True)

    # --- A6: Driver profitability proportions per day (both types) ---
    st.subheader("Driver Profitability Across Days")

    col_prof_neg, col_prof_fix = st.columns(2)

    with col_prof_neg:
        fig_prof_n, ax_prof_n = plt.subplots(figsize=(6, 4))
        ax_prof_n.bar(daily_profitability_df['run_id'], daily_profitability_df['pct_covers_all'], label='Covers All Expenses', color='#2a9d8f')
        ax_prof_n.bar(daily_profitability_df['run_id'], daily_profitability_df['pct_covers_gas'], bottom=daily_profitability_df['pct_covers_all'], label='Covers Gas Only', color='#e9c46a')
        ax_prof_n.bar(daily_profitability_df['run_id'], daily_profitability_df['pct_not_viable'],
                    bottom=daily_profitability_df['pct_covers_all'] + daily_profitability_df['pct_covers_gas'],
                    label='Not Viable', color='#e76f51')
        ax_prof_n.set_xlabel("Day (Run ID)")
        ax_prof_n.set_ylabel("% of Drivers")
        ax_prof_n.set_title("Driver Profitability Per Day (Negotiated)")
        ax_prof_n.legend()
        ax_prof_n.set_ylim(0, 105)
        ax_prof_n.tick_params(axis='x', rotation=45)
        fig_prof_n.tight_layout()
        st.pyplot(fig_prof_n, use_container_width=True)

    with col_prof_fix:
        if 'fixed_pct_covers_all' in daily_profitability_df.columns:
            fig_prof_f, ax_prof_f = plt.subplots(figsize=(6, 4))
            ax_prof_f.bar(daily_profitability_df['run_id'], daily_profitability_df['fixed_pct_covers_all'], label='Covers All Expenses', color='#2a9d8f')
            ax_prof_f.bar(daily_profitability_df['run_id'], daily_profitability_df['fixed_pct_covers_gas'], bottom=daily_profitability_df['fixed_pct_covers_all'], label='Covers Gas Only', color='#e9c46a')
            ax_prof_f.bar(daily_profitability_df['run_id'], daily_profitability_df['fixed_pct_not_viable'],
                        bottom=daily_profitability_df['fixed_pct_covers_all'] + daily_profitability_df['fixed_pct_covers_gas'],
                        label='Not Viable', color='#e76f51')
            ax_prof_f.set_xlabel("Day (Run ID)")
            ax_prof_f.set_ylabel("% of Drivers")
            ax_prof_f.set_title("Driver Profitability Per Day (Fixed)")
            ax_prof_f.legend()
            ax_prof_f.set_ylim(0, 105)
            ax_prof_f.tick_params(axis='x', rotation=45)
            fig_prof_f.tight_layout()
            st.pyplot(fig_prof_f, use_container_width=True)

    # --- A7: Profitable Drivers Metrics ---
    st.subheader("Profitable Drivers — Average Metrics Across Days")
    st.markdown(
        "Metrics computed only from drivers who made a profit on each day, "
        "under four definitions of profitability."
    )

    profit_definitions = [
        ('negotiated_profit', 'Negotiated Income − All Expenses'),
        ('negotiated_profit_gas_only', 'Negotiated Income − Gas Only'),
        ('fixed_profit', 'Fixed Income − All Expenses'),
        ('fixed_profit_gas_only', 'Fixed Income − Gas Only'),
    ]

    profitable_summary_rows = []
    for profit_col, label in profit_definitions:
        if profit_col not in driver_daily.columns:
            continue
        profitable = driver_daily[driver_daily[profit_col] > 0]
        per_day = profitable.groupby('run_id').agg(
            count=(profit_col, 'size'),
            avg_profit=(profit_col, 'mean'),
            median_profit=(profit_col, 'median'),
        ).reset_index()

        profitable_summary_rows.append({
            'Profit Definition': label,
            'Avg Profitable Drivers/Day': f"{per_day['count'].mean():,.1f}" if not per_day.empty else "0",
            'Avg Profit (profitable only)': f"PHP {per_day['avg_profit'].mean():,.2f}" if not per_day.empty else "PHP 0.00",
            'Std Dev Profit (profitable only)': f"PHP {per_day['avg_profit'].std():,.2f}" if not per_day.empty and len(per_day) > 1 else "N/A",
            'Median Profit (profitable only)': f"PHP {per_day['median_profit'].mean():,.2f}" if not per_day.empty else "PHP 0.00",
        })

    if profitable_summary_rows:
        st.table(pd.DataFrame(profitable_summary_rows).set_index('Profit Definition'))

    st.subheader("Unprofitable Drivers — Average Metrics Across Days")
    st.markdown(
        "Metrics computed only from drivers who did **not** make a profit (profit <= 0) on each day, "
        "under four definitions of profitability."
    )

    unprofitable_summary_rows = []
    for profit_col, label in profit_definitions:
        if profit_col not in driver_daily.columns:
            continue
        unprofitable = driver_daily[driver_daily[profit_col] <= 0]
        per_day = unprofitable.groupby('run_id').agg(
            count=(profit_col, 'size'),
            avg_loss=(profit_col, 'mean'),
            median_loss=(profit_col, 'median'),
        ).reset_index()

        unprofitable_summary_rows.append({
            'Profit Definition': label,
            'Avg Unprofitable Drivers/Day': f"{per_day['count'].mean():,.1f}" if not per_day.empty else "0",
            'Avg Loss (unprofitable only)': f"PHP {per_day['avg_loss'].mean():,.2f}" if not per_day.empty else "PHP 0.00",
            'Std Dev Loss (unprofitable only)': f"PHP {per_day['avg_loss'].std():,.2f}" if not per_day.empty and len(per_day) > 1 else "N/A",
            'Median Loss (unprofitable only)': f"PHP {per_day['median_loss'].mean():,.2f}" if not per_day.empty else "PHP 0.00",
        })

    if unprofitable_summary_rows:
        st.table(pd.DataFrame(unprofitable_summary_rows).set_index('Profit Definition'))

    # --- Daily summary table ---
    st.subheader("Daily Summary Table")
    display_cols = ['run_id', 'total_trips', 'total_income', 'total_fixed_income', 'total_expenses',
                    'total_profit', 'total_fixed_profit', 'total_distance', 'active_drivers',
                    'avg_trips_per_driver', 'avg_income_per_driver', 'avg_profit_per_driver', 'gini_gross_income', 'gini_fixed_income']
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

    tab_summary, tab_distributions, tab_trips, tab_bargaining, tab_surplus, tab_profitability, tab_inequality = st.tabs([
        "Summary", "Distributions", "Trips", "Bargaining", "Surplus", "Profitability", "Inequality"
    ])

    # --- Data preparation for per-day views (computed once, used across tabs) ---
    day_driver_income = day_transactions.groupby('trike_id')['price'].sum().reset_index(name='income')
    day_driver_fixed = day_transactions.groupby('trike_id')['base_price'].sum().reset_index(name='fixed_income') if has_base_price else pd.DataFrame()
    day_driver_gas = day_drivers[['trike_id', 'daily_distance']].copy() if not day_drivers.empty else pd.DataFrame(columns=['trike_id', 'daily_distance'])
    day_driver_gas['gas_expenses'] = day_driver_gas['daily_distance'] / 1000 / gas_consumption * gas_price
    day_driver_fixed_exp = day_expenses[day_expenses['expense_type'] == 'daily_expense'].groupby('trike_id')['amount'].sum().reset_index(name='fixed_daily_expenses')
    day_driver_expenses = pd.merge(day_driver_gas[['trike_id', 'gas_expenses']], day_driver_fixed_exp, on='trike_id', how='outer')
    day_driver_expenses.fillna(0, inplace=True)
    day_driver_expenses['expenses'] = day_driver_expenses['gas_expenses'] + day_driver_expenses['fixed_daily_expenses']
    day_driver_expenses = day_driver_expenses[['trike_id', 'expenses']]
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
    if 'fixed_income' in day_driver_table.columns:
        day_driver_table['fixed_profit'] = day_driver_table['fixed_income'] - day_driver_table['expenses']

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

    ## ============================================================
    ## TAB: Summary
    ## ============================================================
    with tab_summary:
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

        st.subheader(f"Day {selected_day} — Driver Rankings")
        st.markdown(
            "Each driver's income, expenses, and profit for this day. "
            "**Fixed income** represents what each driver would earn under the regulated fare matrix "
            "(base price), without any bargaining adjustments."
        )
        st.dataframe(day_driver_table.sort_values('profit', ascending=False))

    ## ============================================================
    ## TAB: Distributions
    ## ============================================================
    with tab_distributions:
        st.subheader(f"Day {selected_day} — Driver Distributions")

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            if not day_driver_table.empty:
                plot_distribution_with_stats(day_driver_table, 'income',
                                             "Driver Income Distribution (Negotiated)", "Income (PHP)",
                                             color="#2a9d8f", bins=20)

        with col_d2:
            if not day_driver_table.empty and 'fixed_income' in day_driver_table.columns:
                plot_distribution_with_stats(day_driver_table, 'fixed_income',
                                             "Driver Income Distribution (Fixed)", "Fixed Income (PHP)",
                                             color="#e9c46a", bins=20)

        col_d3, col_d4 = st.columns(2)

        with col_d3:
            if not day_driver_table.empty:
                plot_distribution_with_stats(day_driver_table, 'profit',
                                             "Driver Profit Distribution (Negotiated)", "Profit (PHP)",
                                             color="#264653", bins=20)

        with col_d4:
            if not day_driver_table.empty and 'fixed_income' in day_driver_table.columns:
                day_driver_table['fixed_profit'] = day_driver_table['fixed_income'] - day_driver_table['expenses']
                plot_distribution_with_stats(day_driver_table, 'fixed_profit',
                                             "Driver Profit Distribution (Fixed)", "Fixed Profit (PHP)",
                                             color="#bc6c25", bins=20)

        if has_duration_data and not day_drivers.empty and 'actual_duration' in day_drivers.columns:
            col_dur1, col_dur2 = st.columns(2)
            day_drivers_plot = day_drivers.copy()
            day_drivers_plot['duration_hours_plot'] = day_drivers_plot['actual_duration'] / 3600

            with col_dur1:
                plot_distribution_with_stats(day_drivers_plot, 'duration_hours_plot',
                                             "Driver Duration Distribution", "Duration (hours)",
                                             color="#264653", bins=20)

            with col_dur2:
                if 'daily_income' in day_drivers_plot.columns:
                    day_drivers_plot['income_per_hour'] = day_drivers_plot.apply(
                        lambda x: x['daily_income'] / (x['actual_duration'] / 3600) if x['actual_duration'] > 0 else 0,
                        axis=1
                    )
                    iph_data = day_drivers_plot[day_drivers_plot['income_per_hour'] > 0]
                    if not iph_data.empty:
                        plot_distribution_with_stats(iph_data, 'income_per_hour',
                                                     "Income per Hour Distribution", "Income per Hour (PHP)",
                                                     color="#e9c46a", bins=20)

    ## ============================================================
    ## TAB: Trips
    ## ============================================================
    with tab_trips:
        st.subheader(f"Day {selected_day} — Trip-Level Analytics")

        trip_display_cols = ['trike_id', 'hub_id', 'origin_edge', 'dest_edge', 'distance', 'price', 'tick',
                             'driver_asp', 'passenger_asp', 'base_price', 'init_driver_asp', 'init_passenger_asp']
        trip_display_cols = [c for c in trip_display_cols if c in day_transactions.columns]

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

        col_t3, col_t4 = st.columns(2)

        with col_t3:
            plot_distribution_with_stats(
                day_transactions, 'distance',
                "Trip Distance Distribution", "Distance (meters)",
                color="skyblue"
            )

        with col_t4:
            plot_distribution_with_stats(
                day_transactions, 'tick',
                "Trips Over Time (by Tick)", "Tick",
                color="violet"
            )

    ## ============================================================
    ## TAB: Bargaining
    ## ============================================================
    with tab_bargaining:
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
        else:
            st.info("No bargaining data available for this scenario.")

    ## ============================================================
    ## TAB: Surplus
    ## ============================================================
    with tab_surplus:
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

        day_with_surplus['marginal_cost'] = (day_with_surplus['distance'] * gas_price) / (1000 * gas_consumption)
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

        if has_base_price:
            day_with_surplus['fixed_producer_surplus'] = day_with_surplus['base_price'] - day_with_surplus['marginal_cost']

            fps_total = day_with_surplus['fixed_producer_surplus'].sum()
            fps_avg = day_with_surplus['fixed_producer_surplus'].mean()
            fps_median = day_with_surplus['fixed_producer_surplus'].median()

            st.markdown("**Fixed Producer Surplus (Base Price)**")
            col_fps1, col_fps2, col_fps3 = st.columns(3)
            col_fps1.metric("Total Fixed Producer Surplus", f"PHP {fps_total:,.2f}")
            col_fps2.metric("Avg Fixed Producer Surplus", f"PHP {fps_avg:,.2f}")
            col_fps3.metric("Median Fixed Producer Surplus", f"PHP {fps_median:,.2f}")

            plot_distribution_with_stats(day_with_surplus, 'fixed_producer_surplus',
                                         "Fixed Producer Surplus Distribution", "Fixed Producer Surplus (PHP)", color="#bc6c25")

    ## ============================================================
    ## TAB: Profitability
    ## ============================================================
    with tab_profitability:
        st.subheader(f"Day {selected_day} — Driver Profitability")
        st.markdown(
            "This section categorizes drivers based on how much they profit from their trips after "
            "accounting for gas and daily expenses:\n\n"
            "- **Profitable**: The driver earns enough to cover gas and daily expenses.\n"
            "- **Break-even**: The driver earns enough to cover gas, but not daily expenses.\n"
            "- **Not Profitable**: The driver earns less than the cost of gas."
        )

        day_prof = daily_profitability_df[daily_profitability_df['run_id'] == selected_day]
        if not day_prof.empty:
            prof_row = day_prof.iloc[0]
            total_d = int(prof_row['total_drivers'])
            colors_viab = {
                "Covers All Expenses": "#2a9d8f",
                "Covers Gas Only": "#e9c46a",
                "Not Viable": "#e76f51"
            }

            col_viab_neg, col_viab_fix = st.columns(2)

            with col_viab_neg:
                fig_viab_n, ax_viab_n = plt.subplots(figsize=(6, 1.8))
                left = 0
                for group, count_key, pct_key in [
                    ("Covers All Expenses", 'covers_all', 'pct_covers_all'),
                    ("Covers Gas Only", 'covers_gas', 'pct_covers_gas'),
                    ("Not Viable", 'not_viable', 'pct_not_viable'),
                ]:
                    pct = prof_row[pct_key] / 100
                    count = int(prof_row[count_key])
                    ax_viab_n.barh(0, pct, left=left, color=colors_viab[group], label=group)
                    if pct > 0:
                        ax_viab_n.text(left + pct / 2, 0, f"{count}/{total_d}",
                                     va='center', ha='center', fontsize=9,
                                     color="white" if group != "Covers Gas Only" else "black")
                    left += pct
                ax_viab_n.set_xlim(0, 1)
                ax_viab_n.set_yticks([])
                ax_viab_n.set_title("Viability (Negotiated)", fontsize=10)
                ax_viab_n.legend(fontsize=7)
                fig_viab_n.tight_layout()
                st.pyplot(fig_viab_n)

            with col_viab_fix:
                if 'fixed_covers_all' in prof_row.index:
                    fig_viab_f, ax_viab_f = plt.subplots(figsize=(6, 1.8))
                    left = 0
                    for group, count_key, pct_key in [
                        ("Covers All Expenses", 'fixed_covers_all', 'fixed_pct_covers_all'),
                        ("Covers Gas Only", 'fixed_covers_gas', 'fixed_pct_covers_gas'),
                        ("Not Viable", 'fixed_not_viable', 'fixed_pct_not_viable'),
                    ]:
                        pct = prof_row[pct_key] / 100
                        count = int(prof_row[count_key])
                        ax_viab_f.barh(0, pct, left=left, color=colors_viab[group], label=group)
                        if pct > 0:
                            ax_viab_f.text(left + pct / 2, 0, f"{count}/{total_d}",
                                         va='center', ha='center', fontsize=9,
                                         color="white" if group != "Covers Gas Only" else "black")
                        left += pct
                    ax_viab_f.set_xlim(0, 1)
                    ax_viab_f.set_yticks([])
                    ax_viab_f.set_title("Viability (Fixed)", fontsize=10)
                    ax_viab_f.legend(fontsize=7)
                    fig_viab_f.tight_layout()
                    st.pyplot(fig_viab_f)

        st.subheader(f"Day {selected_day} — Profitable Drivers Breakdown")
        st.markdown(
            "Metrics computed only from drivers who made a profit this day, "
            "under four definitions of profitability."
        )

        day_driver_profit_data = driver_daily[driver_daily['run_id'] == selected_day]

        day_profit_defs = [
            ('negotiated_profit', 'Negotiated Income − All Expenses'),
            ('negotiated_profit_gas_only', 'Negotiated Income − Gas Only'),
            ('fixed_profit', 'Fixed Income − All Expenses'),
            ('fixed_profit_gas_only', 'Fixed Income − Gas Only'),
        ]

        day_prof_rows = []
        for pcol, plabel in day_profit_defs:
            if pcol not in day_driver_profit_data.columns:
                continue
            profitable_drivers = day_driver_profit_data[day_driver_profit_data[pcol] > 0]
            n_profitable = len(profitable_drivers)
            n_total = len(day_driver_profit_data)
            if n_profitable > 0:
                avg_p = profitable_drivers[pcol].mean()
                median_p = profitable_drivers[pcol].median()
                try:
                    mode_p = profitable_drivers[pcol].round(2).mode()
                    mode_str = f"PHP {mode_p.iloc[0]:,.2f}" if len(mode_p) > 0 else "N/A"
                except Exception:
                    mode_str = "N/A"
            else:
                avg_p = median_p = 0
                mode_str = "N/A"

            day_prof_rows.append({
                'Profit Definition': plabel,
                'Profitable Drivers': f"{n_profitable} / {n_total}",
                'Avg Profit': f"PHP {avg_p:,.2f}",
                'Median Profit': f"PHP {median_p:,.2f}",
                'Mode Profit': mode_str,
            })

        if day_prof_rows:
            st.table(pd.DataFrame(day_prof_rows).set_index('Profit Definition'))

        st.subheader(f"Day {selected_day} — Unprofitable Drivers Breakdown")
        st.markdown(
            "Metrics computed only from drivers who did **not** make a profit (profit <= 0) this day."
        )

        day_unprof_rows = []
        for pcol, plabel in day_profit_defs:
            if pcol not in day_driver_profit_data.columns:
                continue
            unprofitable_drivers = day_driver_profit_data[day_driver_profit_data[pcol] <= 0]
            n_unprofitable = len(unprofitable_drivers)
            n_total = len(day_driver_profit_data)
            if n_unprofitable > 0:
                avg_l = unprofitable_drivers[pcol].mean()
                median_l = unprofitable_drivers[pcol].median()
                try:
                    mode_l = unprofitable_drivers[pcol].round(2).mode()
                    mode_str = f"PHP {mode_l.iloc[0]:,.2f}" if len(mode_l) > 0 else "N/A"
                except Exception:
                    mode_str = "N/A"
            else:
                avg_l = median_l = 0
                mode_str = "N/A"

            day_unprof_rows.append({
                'Profit Definition': plabel,
                'Unprofitable Drivers': f"{n_unprofitable} / {n_total}",
                'Avg Loss': f"PHP {avg_l:,.2f}",
                'Median Loss': f"PHP {median_l:,.2f}",
                'Mode Loss': mode_str,
            })

        if day_unprof_rows:
            st.table(pd.DataFrame(day_unprof_rows).set_index('Profit Definition'))

    ## ============================================================
    ## TAB: Inequality
    ## ============================================================
    with tab_inequality:
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

        day_gross_income = day_transactions.groupby('trike_id')['price'].sum().reset_index(name='gross_income')
        day_ineq_gas = day_drivers[['trike_id', 'daily_distance']].copy() if not day_drivers.empty else pd.DataFrame(columns=['trike_id', 'daily_distance'])
        day_ineq_gas['gas_expenses'] = day_ineq_gas['daily_distance'] / 1000 / gas_consumption * gas_price
        day_gas_exp = day_ineq_gas[['trike_id', 'gas_expenses']]
        day_fixed_exp = day_expenses[day_expenses['expense_type'] == 'daily_expense'].groupby('trike_id')['amount'].sum().reset_index(name='fixed_daily_expenses')
        day_all_exp = pd.merge(day_gas_exp, day_fixed_exp, on='trike_id', how='outer')
        day_all_exp.fillna(0, inplace=True)
        day_all_exp['all_expenses'] = day_all_exp['gas_expenses'] + day_all_exp['fixed_daily_expenses']
        day_gas_exp = day_all_exp[['trike_id', 'gas_expenses']]
        day_all_exp = day_all_exp[['trike_id', 'all_expenses']]

        day_inequality = day_gross_income.copy()
        day_inequality = pd.merge(day_inequality, day_gas_exp, on='trike_id', how='left')
        day_inequality = pd.merge(day_inequality, day_all_exp, on='trike_id', how='left')
        day_inequality.fillna(0, inplace=True)
        day_inequality['after_gas_profit'] = day_inequality['gross_income'] - day_inequality['gas_expenses']
        day_inequality['net_profit'] = day_inequality['gross_income'] - day_inequality['all_expenses']

        if has_base_price:
            day_fixed_income = day_transactions.groupby('trike_id')['base_price'].sum().reset_index(name='fixed_gross_income')
            day_inequality = pd.merge(day_inequality, day_fixed_income, on='trike_id', how='left')
            day_inequality['fixed_gross_income'] = day_inequality['fixed_gross_income'].fillna(0)
            day_inequality['fixed_after_gas_profit'] = day_inequality['fixed_gross_income'] - day_inequality['gas_expenses']
            day_inequality['fixed_net_profit'] = day_inequality['fixed_gross_income'] - day_inequality['all_expenses']

        gini_gross = gini(day_inequality['gross_income'])
        gini_after_gas = gini(day_inequality['after_gas_profit'])
        gini_net = gini(day_inequality['net_profit'])

        if has_base_price:
            gini_fixed_gross = gini(day_inequality['fixed_gross_income'])
            gini_fixed_after_gas = gini(day_inequality['fixed_after_gas_profit'])
            gini_fixed_net = gini(day_inequality['fixed_net_profit'])

        st.markdown("**Negotiated Income**")
        col_g1, col_g2, col_g3 = st.columns(3)
        col_g1.metric("Gini (Gross Income)", f"{gini_gross:.3f}")
        col_g2.metric("Gini (After Gas)", f"{gini_after_gas:.3f}")
        col_g3.metric("Gini (Net Profit)", f"{gini_net:.3f}")

        if has_base_price:
            st.markdown("**Fixed Income (Base Price)**")
            col_fg1, col_fg2, col_fg3 = st.columns(3)
            col_fg1.metric("Gini (Gross Income)", f"{gini_fixed_gross:.3f}")
            col_fg2.metric("Gini (After Gas)", f"{gini_fixed_after_gas:.3f}")
            col_fg3.metric("Gini (Net Profit)", f"{gini_fixed_net:.3f}")

        col_lorenz1, col_lorenz2 = st.columns(2)

        with col_lorenz1:
            fig_lorenz, ax_lorenz = plt.subplots(figsize=(6, 6))

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
            ax_lorenz.set_title(f"Lorenz Curves (Negotiated) — Day {selected_day}")
            ax_lorenz.legend()
            ax_lorenz.grid(True)
            fig_lorenz.tight_layout()
            st.pyplot(fig_lorenz, use_container_width=True)

        with col_lorenz2:
            if has_base_price:
                fig_lorenz_f, ax_lorenz_f = plt.subplots(figsize=(6, 6))

                datasets_lorenz_f = [
                    (day_inequality['fixed_gross_income'], "Gross Income", gini_fixed_gross),
                    (day_inequality['fixed_after_gas_profit'], "After Gas", gini_fixed_after_gas),
                    (day_inequality['fixed_net_profit'], "Net Profit", gini_fixed_net),
                ]

                for (data, label, g_val), color in zip(datasets_lorenz_f, colors_lorenz):
                    if data.sum() > 0:
                        x, y = lorenz_curve(data)
                        ax_lorenz_f.plot(x, y, label=f"{label} (Gini: {g_val:.3f})", color=color)

                ax_lorenz_f.plot([0, 1], [0, 1], linestyle="--", color='black', label="Perfect Equality")
                ax_lorenz_f.set_xlabel("Cumulative Share of Drivers")
                ax_lorenz_f.set_ylabel("Cumulative Share of Income / Profit")
                ax_lorenz_f.set_title(f"Lorenz Curves (Fixed) — Day {selected_day}")
                ax_lorenz_f.legend()
                ax_lorenz_f.grid(True)
                fig_lorenz_f.tight_layout()
                st.pyplot(fig_lorenz_f, use_container_width=True)


## ============================================================
## CROSS-SCENARIO COMPARISON VIEW
## ============================================================

else:
    st.title("Cross-Scenario Comparison")

    selected_scenarios = st.sidebar.multiselect(
        "Select Scenarios to Compare",
        options=existing_logs,
        default=existing_logs,
        key="scenario_selector"
    )

    if not selected_scenarios:
        st.warning("Please select at least one scenario to compare.")
        st.stop()

    # Load and compute summaries for all selected scenarios
    scenario_summaries = []
    scenario_profitability = []
    scenario_daily_fixed_income = {}  # scenario -> Series of per-run total_fixed_income

    with st.spinner("Loading scenario data..."):
        for scenario in selected_scenarios:
            result = load_scenario_data(scenario)
            if result[0] is None:
                continue
            df_all_s, df_exp_s, df_drv_s, df_trip_s, sim_count_s = result
            daily_sum_s, daily_prof_s = compute_daily_summary(df_all_s, df_exp_s, df_drv_s, df_trip_s, gas_price, gas_consumption)

            # Store per-run total_fixed_income for ANOVA
            if 'total_fixed_income' in daily_sum_s.columns:
                scenario_daily_fixed_income[scenario] = daily_sum_s['total_fixed_income'].dropna()

            # Average across all days in this scenario
            avg_row = daily_sum_s.mean(numeric_only=True).to_dict()
            avg_row['scenario'] = scenario
            avg_row['sim_count'] = sim_count_s

            # Passenger satisfaction rate (WTP >= price)
            if 'passenger_asp' in df_all_s.columns:
                asp_valid = df_all_s.dropna(subset=['passenger_asp', 'price'])
                if not asp_valid.empty:
                    avg_row['satisfaction_rate'] = (asp_valid['passenger_asp'] >= asp_valid['price']).mean() * 100

            scenario_summaries.append(avg_row)

            # Average profitability across days
            prof_avg = daily_prof_s.mean(numeric_only=True).to_dict()
            prof_avg['scenario'] = scenario
            scenario_profitability.append(prof_avg)

    if not scenario_summaries:
        st.warning("No valid scenario data found.")
        st.stop()

    df_scenarios = pd.DataFrame(scenario_summaries)
    df_scenarios = df_scenarios.sort_values('scenario').reset_index(drop=True)

    df_prof_scenarios = pd.DataFrame(scenario_profitability)
    df_prof_scenarios = df_prof_scenarios.sort_values('scenario').reset_index(drop=True)

    st.caption(f"Comparing **{len(df_scenarios)}** scenarios")
    st.divider()

    # --- Summary Table ---
    st.subheader("Summary Table")

    # Merge breakeven rate and gini profit metrics from profitability data into main summary
    prof_merge_cols = ['scenario']
    prof_rename = {}
    if 'pct_covers_all' in df_prof_scenarios.columns:
        prof_merge_cols.append('pct_covers_all')
        prof_rename['pct_covers_all'] = 'avg_breakeven_rate'
    if 'fixed_pct_covers_all' in df_prof_scenarios.columns:
        prof_merge_cols.append('fixed_pct_covers_all')
        prof_rename['fixed_pct_covers_all'] = 'avg_fixed_breakeven_rate'
    if 'gini_net_profit' in df_prof_scenarios.columns:
        prof_merge_cols.append('gini_net_profit')
    if 'gini_fixed_net_profit' in df_prof_scenarios.columns:
        prof_merge_cols.append('gini_fixed_net_profit')
    if len(prof_merge_cols) > 1:
        df_scenarios = df_scenarios.merge(
            df_prof_scenarios[prof_merge_cols].rename(columns=prof_rename),
            on='scenario', how='left'
        )

    # Compute total surplus columns (consumer + producer)
    if 'total_consumer_surplus' in df_scenarios.columns and 'total_producer_surplus' in df_scenarios.columns:
        df_scenarios['total_surplus_negotiated'] = df_scenarios['total_consumer_surplus'] + df_scenarios['total_producer_surplus']
    if 'total_consumer_surplus' in df_scenarios.columns and 'total_fixed_producer_surplus' in df_scenarios.columns:
        df_scenarios['total_surplus_fixed'] = df_scenarios['total_consumer_surplus'] + df_scenarios['total_fixed_producer_surplus']

    table_cols = ['scenario', 'sim_count', 'total_trips', 'active_drivers',
                  'avg_trips_per_driver', 'avg_income_per_driver', 'avg_fixed_income_per_driver',
                  'avg_profit_per_driver', 'avg_fixed_profit_per_driver',
                  'total_profit', 'total_fixed_profit',
                  'gini_gross_income', 'gini_fixed_income', 'gini_net_profit', 'gini_fixed_net_profit', 'gini_bargaining_gap',
                  'gini_producer_surplus', 'gini_fixed_producer_surplus', 'gini_consumer_surplus',
                  'avg_consumer_surplus', 'avg_producer_surplus',
                  'total_consumer_surplus', 'total_producer_surplus', 'total_fixed_producer_surplus',
                  'total_surplus_negotiated', 'total_surplus_fixed',
                  'satisfaction_rate', 'avg_breakeven_rate', 'avg_fixed_breakeven_rate']
    if 'acceptance_rate' in df_scenarios.columns:
        table_cols.append('acceptance_rate')
    table_cols = [c for c in table_cols if c in df_scenarios.columns]
    st.dataframe(df_scenarios[table_cols], use_container_width=True)

    # st.divider()
    #
    # # --- Bar Charts ---
    # x_label = "Scenario"
    # scenarios = df_scenarios['scenario']
    #
    # # Chart 1: Avg Income & Profit per Driver (both types side by side)
    # st.subheader("Avg Income & Profit per Driver")
    # col_xc1_neg, col_xc1_fix = st.columns(2)
    # x = np.arange(len(scenarios))
    # width = 0.35
    #
    # with col_xc1_neg:
    #     fig1n, ax1n = plt.subplots(figsize=(6, 5))
    #     ax1n.bar(x - width/2, df_scenarios['avg_income_per_driver'], width, label='Avg Income', color='#2a9d8f')
    #     ax1n.bar(x + width/2, df_scenarios['avg_profit_per_driver'], width, label='Avg Profit', color='#264653')
    #     ax1n.set_xlabel(x_label)
    #     ax1n.set_ylabel("PHP")
    #     ax1n.set_title("Negotiated")
    #     ax1n.set_xticks(x)
    #     ax1n.set_xticklabels(scenarios, rotation=45, ha='right')
    #     ax1n.legend()
    #     fig1n.tight_layout()
    #     st.pyplot(fig1n, use_container_width=True)
    #
    # with col_xc1_fix:
    #     fig1f, ax1f = plt.subplots(figsize=(6, 5))
    #     ax1f.bar(x - width/2, df_scenarios['avg_fixed_income_per_driver'], width, label='Avg Income', color='#2a9d8f')
    #     ax1f.bar(x + width/2, df_scenarios['avg_fixed_profit_per_driver'], width, label='Avg Profit', color='#264653')
    #     ax1f.set_xlabel(x_label)
    #     ax1f.set_ylabel("PHP")
    #     ax1f.set_title("Fixed")
    #     ax1f.set_xticks(x)
    #     ax1f.set_xticklabels(scenarios, rotation=45, ha='right')
    #     ax1f.legend()
    #     fig1f.tight_layout()
    #     st.pyplot(fig1f, use_container_width=True)
    #
    # # Chart 1b: Average Total Profit (Negotiated vs Fixed)
    # if 'total_profit' in df_scenarios.columns and 'total_fixed_profit' in df_scenarios.columns:
    #     st.subheader("Avg Total Profit (Negotiated vs Fixed)")
    #     fig1b, ax1b = plt.subplots(figsize=(12, 5))
    #     x = np.arange(len(scenarios))
    #     width = 0.35
    #     ax1b.bar(x - width/2, df_scenarios['total_profit'], width, label='Negotiated Profit', color='#e76f51')
    #     ax1b.bar(x + width/2, df_scenarios['total_fixed_profit'], width, label='Fixed Profit', color='#2a9d8f')
    #     ax1b.set_xlabel(x_label)
    #     ax1b.set_ylabel("PHP")
    #     ax1b.set_xticks(x)
    #     ax1b.set_xticklabels(scenarios, rotation=45, ha='right')
    #     ax1b.legend()
    #     fig1b.tight_layout()
    #     st.pyplot(fig1b, use_container_width=True)
    #
    # # Chart 2: Avg Trips per Driver
    # st.subheader("Avg Trips per Driver")
    # fig2, ax2 = plt.subplots(figsize=(12, 4))
    # ax2.bar(scenarios, df_scenarios['avg_trips_per_driver'], color='#2a9d8f', alpha=0.8)
    # ax2.set_xlabel(x_label)
    # ax2.set_ylabel("Trips")
    # ax2.set_title("Average Trips per Driver")
    # ax2.tick_params(axis='x', rotation=45)
    # fig2.tight_layout()
    # st.pyplot(fig2, use_container_width=True)
    #
    # # Chart 3: Gini Coefficients (Income)
    # st.subheader("Income Inequality (Gini Coefficient)")
    # fig3, ax3 = plt.subplots(figsize=(12, 4))
    # x = np.arange(len(scenarios))
    # width = 0.35
    # ax3.bar(x - width/2, df_scenarios['gini_gross_income'], width, label='Negotiated Income', color='#e76f51')
    # ax3.bar(x + width/2, df_scenarios['gini_fixed_income'], width, label='Fixed Income', color='#2a9d8f')
    # ax3.set_xlabel(x_label)
    # ax3.set_ylabel("Gini Coefficient")
    # ax3.set_xticks(x)
    # ax3.set_xticklabels(scenarios, rotation=45, ha='right')
    # ax3.legend()
    # ax3.set_ylim(0, max(0.5, df_scenarios[['gini_gross_income', 'gini_fixed_income']].max().max() * 1.2))
    # fig3.tight_layout()
    # st.pyplot(fig3, use_container_width=True)
    #
    # # Chart 3b: Gini Coefficients (Net Profit)
    # if 'gini_net_profit' in df_scenarios.columns and 'gini_fixed_net_profit' in df_scenarios.columns:
    #     st.subheader("Profit Inequality (Gini Coefficient)")
    #     fig3b, ax3b = plt.subplots(figsize=(12, 4))
    #     x = np.arange(len(scenarios))
    #     width = 0.35
    #     ax3b.bar(x - width/2, df_scenarios['gini_net_profit'], width, label='Negotiated Net Profit', color='#264653')
    #     ax3b.bar(x + width/2, df_scenarios['gini_fixed_net_profit'], width, label='Fixed Net Profit', color='#bc6c25')
    #     ax3b.set_xlabel(x_label)
    #     ax3b.set_ylabel("Gini Coefficient")
    #     ax3b.set_xticks(x)
    #     ax3b.set_xticklabels(scenarios, rotation=45, ha='right')
    #     ax3b.legend()
    #     gini_profit_max = df_scenarios[['gini_net_profit', 'gini_fixed_net_profit']].max().max()
    #     ax3b.set_ylim(0, max(0.5, gini_profit_max * 1.2))
    #     fig3b.tight_layout()
    #     st.pyplot(fig3b, use_container_width=True)
    #
    # # Chart 4: Consumer & Producer Surplus
    # if 'avg_consumer_surplus' in df_scenarios.columns and 'avg_producer_surplus' in df_scenarios.columns:
    #     st.subheader("Average Surplus")
    #     fig4, ax4 = plt.subplots(figsize=(12, 4))
    #     x = np.arange(len(scenarios))
    #     width = 0.25
    #     ax4.bar(x - width, df_scenarios['avg_consumer_surplus'], width, label='Avg Consumer Surplus', color='#2a9d8f')
    #     ax4.bar(x, df_scenarios['avg_producer_surplus'], width, label='Avg Producer Surplus', color='#e76f51')
    #     if 'avg_fixed_producer_surplus' in df_scenarios.columns:
    #         ax4.bar(x + width, df_scenarios['avg_fixed_producer_surplus'], width, label='Avg Fixed Producer Surplus', color='#bc6c25')
    #     ax4.set_xlabel(x_label)
    #     ax4.set_ylabel("PHP")
    #     ax4.set_xticks(x)
    #     ax4.set_xticklabels(scenarios, rotation=45, ha='right')
    #     ax4.legend()
    #     fig4.tight_layout()
    #     st.pyplot(fig4, use_container_width=True)
    #
    # # Chart 4a: Total Surplus
    # if 'total_producer_surplus' in df_scenarios.columns:
    #     st.subheader("Total Surplus")
    #     fig4a, ax4a = plt.subplots(figsize=(12, 4))
    #     x = np.arange(len(scenarios))
    #     surplus_bars = []
    #     if 'total_consumer_surplus' in df_scenarios.columns:
    #         surplus_bars.append(('total_consumer_surplus', 'Total Consumer Surplus', '#2a9d8f'))
    #     surplus_bars.append(('total_producer_surplus', 'Total Producer Surplus', '#e76f51'))
    #     if 'total_fixed_producer_surplus' in df_scenarios.columns:
    #         surplus_bars.append(('total_fixed_producer_surplus', 'Total Fixed Producer Surplus', '#bc6c25'))
    #     n_bars = len(surplus_bars)
    #     width = 0.8 / n_bars
    #     for i, (col, label, color) in enumerate(surplus_bars):
    #         ax4a.bar(x + i * width - (n_bars - 1) * width / 2, df_scenarios[col], width, label=label, color=color)
    #     ax4a.set_xlabel(x_label)
    #     ax4a.set_ylabel("PHP")
    #     ax4a.set_xticks(x)
    #     ax4a.set_xticklabels(scenarios, rotation=45, ha='right')
    #     ax4a.legend()
    #     fig4a.tight_layout()
    #     st.pyplot(fig4a, use_container_width=True)
    #
    # # Chart 4c: Total Surplus (Combined Consumer + Producer)
    # if 'total_producer_surplus' in df_scenarios.columns and 'total_consumer_surplus' in df_scenarios.columns:
    #     st.subheader("Total Surplus (Consumer + Producer)")
    #     fig4c, ax4c = plt.subplots(figsize=(12, 4))
    #     x = np.arange(len(scenarios))
    #     total_neg_surplus = df_scenarios['total_consumer_surplus'] + df_scenarios['total_producer_surplus']
    #     has_fixed_total = 'total_fixed_producer_surplus' in df_scenarios.columns
    #     n_bars = 2 if has_fixed_total else 1
    #     width = 0.8 / n_bars
    #     offsets = np.linspace(-(n_bars - 1) * width / 2, (n_bars - 1) * width / 2, n_bars)
    #     ax4c.bar(x + offsets[0], total_neg_surplus, width, label='Total Surplus (Negotiated)', color='#e76f51')
    #     if has_fixed_total:
    #         total_fix_surplus = df_scenarios['total_consumer_surplus'] + df_scenarios['total_fixed_producer_surplus']
    #         ax4c.bar(x + offsets[1], total_fix_surplus, width, label='Total Surplus (Fixed)', color='#bc6c25')
    #     ax4c.set_xlabel(x_label)
    #     ax4c.set_ylabel("PHP")
    #     ax4c.set_xticks(x)
    #     ax4c.set_xticklabels(scenarios, rotation=45, ha='right')
    #     ax4c.legend()
    #     fig4c.tight_layout()
    #     st.pyplot(fig4c, use_container_width=True)
    #
    # # Chart 4b: Gini Coefficients (Surplus)
    # if 'gini_producer_surplus' in df_scenarios.columns:
    #     st.subheader("Surplus Inequality (Gini Coefficient)")
    #     fig4b, ax4b = plt.subplots(figsize=(12, 4))
    #     x = np.arange(len(scenarios))
    #     surplus_gini_cols = ['gini_producer_surplus']
    #     has_fixed_ps_gini = 'gini_fixed_producer_surplus' in df_scenarios.columns
    #     has_cs_gini = 'gini_consumer_surplus' in df_scenarios.columns
    #     n_bars = 1 + int(has_fixed_ps_gini) + int(has_cs_gini)
    #     width = 0.8 / n_bars
    #     offset = 0
    #     ax4b.bar(x + offset * width - (n_bars - 1) * width / 2, df_scenarios['gini_producer_surplus'], width, label='Producer Surplus', color='#e76f51')
    #     offset += 1
    #     if has_fixed_ps_gini:
    #         ax4b.bar(x + offset * width - (n_bars - 1) * width / 2, df_scenarios['gini_fixed_producer_surplus'], width, label='Fixed Producer Surplus', color='#bc6c25')
    #         surplus_gini_cols.append('gini_fixed_producer_surplus')
    #         offset += 1
    #     if has_cs_gini:
    #         ax4b.bar(x + offset * width - (n_bars - 1) * width / 2, df_scenarios['gini_consumer_surplus'], width, label='Consumer Surplus', color='#2a9d8f')
    #         surplus_gini_cols.append('gini_consumer_surplus')
    #     ax4b.set_xlabel(x_label)
    #     ax4b.set_ylabel("Gini Coefficient")
    #     ax4b.set_xticks(x)
    #     ax4b.set_xticklabels(scenarios, rotation=45, ha='right')
    #     ax4b.legend()
    #     surplus_gini_max = df_scenarios[surplus_gini_cols].max().max()
    #     ax4b.set_ylim(0, max(0.5, surplus_gini_max * 1.2))
    #     fig4b.tight_layout()
    #     st.pyplot(fig4b, use_container_width=True)
    #
    # # Chart 5: Acceptance Rate
    # if 'acceptance_rate' in df_scenarios.columns:
    #     st.subheader("Average Acceptance Rate")
    #     fig5, ax5 = plt.subplots(figsize=(12, 4))
    #     ax5.bar(scenarios, df_scenarios['acceptance_rate'], color='#264653', alpha=0.8)
    #     ax5.set_xlabel(x_label)
    #     ax5.set_ylabel("Acceptance Rate (%)")
    #     ax5.set_title("Average Trip Acceptance Rate")
    #     ax5.set_ylim(0, 105)
    #     ax5.tick_params(axis='x', rotation=45)
    #     fig5.tight_layout()
    #     st.pyplot(fig5, use_container_width=True)
    #
    # # Chart 5b: Sufficientarianism Metrics
    # has_satisfaction = 'satisfaction_rate' in df_scenarios.columns and df_scenarios['satisfaction_rate'].notna().any()
    # has_breakeven = 'pct_covers_all' in df_prof_scenarios.columns
    # has_fixed_breakeven = 'fixed_pct_covers_all' in df_prof_scenarios.columns
    #
    # if has_satisfaction or has_breakeven or has_fixed_breakeven:
    #     st.subheader("Sufficientarianism Metrics")
    #     fig_suf, ax_suf = plt.subplots(figsize=(12, 5))
    #     x = np.arange(len(scenarios))
    #     n_bars = sum([has_satisfaction, has_breakeven, has_fixed_breakeven])
    #     width = 0.8 / max(n_bars, 1)
    #     offsets = np.linspace(-(n_bars - 1) * width / 2, (n_bars - 1) * width / 2, n_bars)
    #     bar_idx = 0
    #
    #     if has_satisfaction:
    #         ax_suf.bar(x + offsets[bar_idx], df_scenarios['satisfaction_rate'], width,
    #                    label='Passenger Satisfaction Rate', color='#2a9d8f')
    #         bar_idx += 1
    #     if has_breakeven:
    #         ax_suf.bar(x + offsets[bar_idx], df_prof_scenarios['pct_covers_all'], width,
    #                    label='Driver Break-even Rate (Negotiated)', color='#264653')
    #         bar_idx += 1
    #     if has_fixed_breakeven:
    #         ax_suf.bar(x + offsets[bar_idx], df_prof_scenarios['fixed_pct_covers_all'], width,
    #                    label='Driver Break-even Rate (Fixed)', color='#e76f51')
    #         bar_idx += 1
    #
    #     ax_suf.set_xlabel(x_label)
    #     ax_suf.set_ylabel("%")
    #     ax_suf.set_title("Sufficientarianism: Satisfaction & Break-even Rates")
    #     ax_suf.set_xticks(x)
    #     ax_suf.set_xticklabels(scenarios, rotation=45, ha='right')
    #     ax_suf.legend()
    #     ax_suf.set_ylim(0, 105)
    #     fig_suf.tight_layout()
    #     st.pyplot(fig_suf, use_container_width=True)
    #
    # # Chart 6: Driver Profitability Breakdown (stacked bar, both types)
    # st.subheader("Driver Profitability Breakdown")
    #
    # col_xprof_neg, col_xprof_fix = st.columns(2)
    # x = np.arange(len(df_prof_scenarios))
    #
    # with col_xprof_neg:
    #     if all(c in df_prof_scenarios.columns for c in ['pct_covers_all', 'pct_covers_gas', 'pct_not_viable']):
    #         fig6n, ax6n = plt.subplots(figsize=(6, 5))
    #         ax6n.bar(x, df_prof_scenarios['pct_covers_all'], label='Covers All Expenses', color='#2a9d8f')
    #         ax6n.bar(x, df_prof_scenarios['pct_covers_gas'], bottom=df_prof_scenarios['pct_covers_all'], label='Covers Gas Only', color='#e9c46a')
    #         ax6n.bar(x, df_prof_scenarios['pct_not_viable'],
    #                 bottom=df_prof_scenarios['pct_covers_all'] + df_prof_scenarios['pct_covers_gas'],
    #                 label='Not Viable', color='#e76f51')
    #         ax6n.set_xlabel(x_label)
    #         ax6n.set_ylabel("% of Drivers")
    #         ax6n.set_title("Profitability by Scenario (Negotiated)")
    #         ax6n.set_xticks(x)
    #         ax6n.set_xticklabels(df_prof_scenarios['scenario'], rotation=45, ha='right')
    #         ax6n.legend()
    #         ax6n.set_ylim(0, 105)
    #         fig6n.tight_layout()
    #         st.pyplot(fig6n, use_container_width=True)
    #
    # with col_xprof_fix:
    #     if all(c in df_prof_scenarios.columns for c in ['fixed_pct_covers_all', 'fixed_pct_covers_gas', 'fixed_pct_not_viable']):
    #         fig6f, ax6f = plt.subplots(figsize=(6, 5))
    #         ax6f.bar(x, df_prof_scenarios['fixed_pct_covers_all'], label='Covers All Expenses', color='#2a9d8f')
    #         ax6f.bar(x, df_prof_scenarios['fixed_pct_covers_gas'], bottom=df_prof_scenarios['fixed_pct_covers_all'], label='Covers Gas Only', color='#e9c46a')
    #         ax6f.bar(x, df_prof_scenarios['fixed_pct_not_viable'],
    #                 bottom=df_prof_scenarios['fixed_pct_covers_all'] + df_prof_scenarios['fixed_pct_covers_gas'],
    #                 label='Not Viable', color='#e76f51')
    #         ax6f.set_xlabel(x_label)
    #         ax6f.set_ylabel("% of Drivers")
    #         ax6f.set_title("Profitability by Scenario (Fixed)")
    #         ax6f.set_xticks(x)
    #         ax6f.set_xticklabels(df_prof_scenarios['scenario'], rotation=45, ha='right')
    #         ax6f.legend()
    #         ax6f.set_ylim(0, 105)
    #         fig6f.tight_layout()
    #         st.pyplot(fig6f, use_container_width=True)
    #
    # # Profitability summary table
    # st.subheader("Profitability Summary Table")
    # prof_table_cols = ['scenario', 'total_drivers',
    #                    'pct_covers_all', 'pct_covers_gas', 'pct_not_viable']
    # if 'fixed_pct_covers_all' in df_prof_scenarios.columns:
    #     prof_table_cols.extend(['fixed_pct_covers_all', 'fixed_pct_covers_gas', 'fixed_pct_not_viable'])
    # prof_table_cols = [c for c in prof_table_cols if c in df_prof_scenarios.columns]
    # st.dataframe(df_prof_scenarios[prof_table_cols], use_container_width=True)
    #
    # # --- One-Way ANOVA: Mean Total Fixed Income ---
    # st.divider()
    # st.subheader("One-Way ANOVA: Mean Total Fixed Income")
    # st.caption("One-way ANOVA on per-run total fixed income across selected scenarios.")
    #
    # anova_scenarios = [s for s in selected_scenarios if s in scenario_daily_fixed_income and len(scenario_daily_fixed_income[s]) >= 2]
    #
    # if len(anova_scenarios) < 2:
    #     st.warning("Need at least 2 scenarios with 2+ runs each to perform ANOVA.")
    # else:
    #     groups = [scenario_daily_fixed_income[s] for s in anova_scenarios]
    #     f_stat, p_value = stats.f_oneway(*groups)
    #
    #     anova_summary = []
    #     for s in anova_scenarios:
    #         data = scenario_daily_fixed_income[s]
    #         anova_summary.append({
    #             'Scenario': s,
    #             'Mean': round(data.mean(), 4),
    #             'Std': round(data.std(), 4),
    #             'n': len(data),
    #         })
    #     df_anova_summary = pd.DataFrame(anova_summary)
    #     st.dataframe(df_anova_summary, use_container_width=True)
    #
    #     st.markdown(
    #         f"**F-statistic:** {f_stat:.4f} &nbsp;&nbsp; "
    #         f"**p-value:** {p_value:.6f} &nbsp;&nbsp; "
    #         f"**Significant (p<0.05):** {'Yes' if p_value < 0.05 else 'No'}"
    #     )
    #
    #     # --- Post-hoc: Games-Howell pairwise comparisons ---
    #     if p_value < 0.05 and len(anova_scenarios) > 2:
    #         st.markdown("---")
    #         st.markdown("**Post-hoc: Games-Howell Pairwise Comparisons**")
    #         st.caption("Since the ANOVA is significant, Games-Howell tests identify which specific scenario pairs differ. "
    #                    "This test does not assume equal variances or equal sample sizes.")
    #
    #         posthoc_results = []
    #         k = len(anova_scenarios)
    #         for i in range(k):
    #             for j in range(i + 1, k):
    #                 s1, s2 = anova_scenarios[i], anova_scenarios[j]
    #                 d1 = scenario_daily_fixed_income[s1]
    #                 d2 = scenario_daily_fixed_income[s2]
    #                 n1, n2 = len(d1), len(d2)
    #                 m1, m2 = d1.mean(), d2.mean()
    #                 v1, v2 = d1.var(ddof=1), d2.var(ddof=1)
    #
    #                 # Welch's t-statistic
    #                 se = np.sqrt(v1 / n1 + v2 / n2)
    #                 t_stat_gh = (m1 - m2) / se if se > 0 else 0.0
    #
    #                 # Welch-Satterthwaite degrees of freedom
    #                 num = (v1 / n1 + v2 / n2) ** 2
    #                 denom = (v1 / n1) ** 2 / (n1 - 1) + (v2 / n2) ** 2 / (n2 - 1)
    #                 df_gh = num / denom if denom > 0 else 1.0
    #
    #                 # Two-tailed p-value from t-distribution
    #                 p_gh = 2 * stats.t.sf(abs(t_stat_gh), df_gh)
    #
    #                 # Bonferroni correction for multiple comparisons
    #                 n_comparisons = k * (k - 1) / 2
    #                 p_adj = min(p_gh * n_comparisons, 1.0)
    #
    #                 posthoc_results.append({
    #                     'Scenario A': s1,
    #                     'Scenario B': s2,
    #                     'Mean A': round(m1, 4),
    #                     'Mean B': round(m2, 4),
    #                     'Mean Diff': round(m1 - m2, 4),
    #                     't-statistic': round(t_stat_gh, 4),
    #                     'df': round(df_gh, 2),
    #                     'p-value': round(p_gh, 6),
    #                     'p-adjusted': round(p_adj, 6),
    #                     'Significant (p<0.05)': 'Yes' if p_adj < 0.05 else 'No'
    #                 })
    #
    #         df_posthoc = pd.DataFrame(posthoc_results)
    #         st.dataframe(df_posthoc, use_container_width=True)
