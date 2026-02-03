import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import re # For cleaning expense amount

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
        # Rounding to 2 decimals to find a meaningful mode in float data
        mode_series = data[x_col].round(2).mode()
        if len(mode_series) > 0:
            mode_val = mode_series[0] # Take the first mode if multiple
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
    
    # Add text box to the plot (top right corner usually works well)
    # transform=ax.transAxes uses relative coordinates (0 to 1)
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
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.pyplot(fig, use_container_width=False)


## --- NEW: Sidebar Configuration ---
st.sidebar.header("Analysis Configuration")

# 1. Select Log Directory
# Find all directories that match the expected pattern
available_logs = ["Driver_55.9", "Driver_58.9", "Manila_55.9", "Manila_58.9", "Test", "Without_Queue"] 
existing_logs = [d for d in available_logs if os.path.isdir(d)]

if not existing_logs:
    st.error("No log directories (e.g., 'logs', 'log1') found. Please check your folder structure.")
    st.stop()

LOG_DIRECTORY = st.sidebar.selectbox(
    "Select Log Directory to Analyze",
    options=existing_logs,
    index=0 # Default to the first one found
)

# 2. Select number of runs to skip
all_folders = []
if os.path.isdir(LOG_DIRECTORY):
    # Get all items, then filter for directories (which are the sim runs)
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
df_drivers_list = []  # Store driver info for per-day stats

sim_count = 0

# USES THE FILTERED LIST 'folders_to_process'
for folder in all_folders:
    folder_path = os.path.join(LOG_DIRECTORY, folder)
    
    # Use folder name as the run_id for consistency
    run_id = folder 
    
    drivers_file = os.path.join(folder_path, "drivers.csv")
    transactions_file = os.path.join(folder_path, "transactions.csv")
    expenses_file = os.path.join(folder_path, "expenses.csv")

    # Check if all required files exist before trying to read
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
        # Load all files for this run
        driver_df = pd.read_csv(drivers_file)
        transaction_df = pd.read_csv(transactions_file)
        expenses_df = pd.read_csv(expenses_file)

        # Add run_id to driver_df for per-day tracking
        driver_df["run_id"] = run_id
        df_drivers_list.append(driver_df)

        # --- Process Transactions & Drivers (Income) ---
        # Merge transactions and driver info
        merged_df = pd.merge(transaction_df, driver_df, on="trike_id", how="left")

        # Assign the run_id from the folder
        merged_df["run_id"] = run_id
        df_all_list.append(merged_df)

        # --- Process Expenses ---
        expenses_df["run_id"] = run_id
        
        # Clean the 'amount' column using the helper function
        expenses_df["amount"] = expenses_df["amount"].apply(extract_amount)
        # Clean expenses *before* calculating run-level profit
        expenses_df.dropna(subset=['amount'], inplace=True) 
        df_expenses_list.append(expenses_df)

        sim_count += 1
        
    except Exception as e:
        st.error(f"Error processing folder {folder}: {e}")

# Exit if no data was loaded
if sim_count == 0:
    st.warning(f"No simulation data was successfully loaded. Check the 'logs' directory and file contents, or adjust the 'skip' value.")
    st.stop()
    
# Concatenate all data from all runs
df_all = pd.concat(df_all_list, ignore_index=True)
df_all_expenses = pd.concat(df_expenses_list, ignore_index=True)
df_all_drivers = pd.concat(df_drivers_list, ignore_index=True) if df_drivers_list else pd.DataFrame()

# Drop any rows where expense amount could not be parsed
df_all_expenses.dropna(subset=['amount'], inplace=True)

## --- NEW DRIVER-CENTRIC ANALYSIS ---

# 1. Total Income per driver (grouped by trike_id)
income_by_driver = df_all.groupby('trike_id')['price'].sum().reset_index().rename(columns={'price': 'total_income'})

# 2. Total Expenses per driver (grouped by trike_id)
expenses_by_driver = df_all_expenses.groupby('trike_id')['amount'].sum().reset_index().rename(columns={'amount': 'total_expenses'})

# 3. Daily Income Variance per driver (Corrected)
# Calculate daily income for each driver in each run first
daily_income_per_run = df_all.groupby(['trike_id', 'run_id'])['price'].sum().reset_index()

# Now calculate the variance of these daily totals for each driver
variance_by_driver = daily_income_per_run.groupby('trike_id')['price'].var().reset_index().rename(columns={'price': 'income_variance'}).fillna(0)

# 4. Trip Count per driver (grouped by trike_id)
trip_count_by_driver = df_all.groupby('trike_id').size().reset_index(name='total_trip_count')

# 5. Combine all driver stats
# Use 'outer' merge to include drivers with income but no expenses, or vice-versa
driver_stats = pd.merge(income_by_driver, expenses_by_driver, on='trike_id', how='outer')
driver_stats = pd.merge(driver_stats, variance_by_driver, on='trike_id', how='outer')
driver_stats = pd.merge(driver_stats, trip_count_by_driver, on='trike_id', how='outer')

# Fill with 0 for any NaNs resulting from the outer merge
driver_stats.fillna(0, inplace=True)

# 6. Calculate Total Profit
driver_stats['total_profit'] = driver_stats['total_income'] - driver_stats['total_expenses']

# --- NEW: Daily Averages & 30-Day Projections ---
# sim_count is now the number of *processed* runs
if sim_count > 0:
    driver_stats['avg_daily_income'] = driver_stats['total_income'] / sim_count
    driver_stats['avg_daily_expenses'] = driver_stats['total_expenses'] / sim_count
    driver_stats['avg_daily_profit'] = driver_stats['total_profit'] / sim_count
    driver_stats['avg_daily_trips'] = driver_stats['total_trip_count'] / sim_count
    
    driver_stats['projected_30day_income'] = driver_stats['avg_daily_income'] * 30
    driver_stats['projected_30day_profit'] = driver_stats['avg_daily_profit'] * 30
else:
     # Avoid division by zero, though we stop earlier if sim_count is 0
     for col in ['avg_daily_income', 'avg_daily_expenses', 'avg_daily_profit', 'avg_daily_trips', 'projected_30day_income', 'projected_30day_profit']:
         driver_stats[col] = 0

# Reorder columns for clarity
driver_stats = driver_stats[[
    'trike_id', 
    'avg_daily_profit',
    'projected_30day_profit',
    'avg_daily_income',
    'projected_30day_income',
    'avg_daily_expenses',
    'avg_daily_trips',
    'total_profit', 
    'total_income', 
    'total_expenses', 
    'income_variance', 
    'total_trip_count'
]]


## --- STREAMLIT APP LAYOUT ---

st.title(f"Tricycle Simulation Analysis: {LOG_DIRECTORY}")
st.divider()

# --- Global Metrics ---
st.header("Overall Simulation Metrics (Based on Analyzed Runs)")
col1, col2, col3 = st.columns(3)
col1.metric("Total Trips", f"{len(df_all):,}")
col2.metric("Total Distance", f"{df_all['distance'].sum():,.0f} m")
col3.metric("Total Income", f"PHP {df_all['price'].sum():,.2f}")
col1.metric("Total Expenses", f"PHP {df_all_expenses['amount'].sum():,.2f}")
col2.metric("Total Profit", f"PHP {(df_all['price'].sum() - df_all_expenses['amount'].sum()):,.2f}")
st.divider()

# --- Driver Analytics (New Section) ---
st.header("Driver-Level Analytics (Based on Analyzed Runs)")
st.write(f"Summary of driver performance, averaged over **{sim_count}** simulation run(s). 'Trike ID' is the consistent identifier across all runs.")
st.dataframe(driver_stats.sort_values(by='avg_daily_profit', ascending=False))

st.subheader("Driver Average Daily Profit Distribution")
plot_distribution_with_stats(
    driver_stats, 
    'avg_daily_profit', 
    "Distribution of Driver Average Daily Profits",
    "Average Daily Profit (PHP)",
    color="#2a9d8f"
)

st.subheader("Driver Daily Income Variance Distribution")
# Filter out extreme outliers for a better plot
q99 = driver_stats['income_variance'].quantile(0.99)
if q99 > 0:
    plot_data = driver_stats[driver_stats['income_variance'] < q99]
else:
    plot_data = driver_stats # Show all if q99 is 0

plot_distribution_with_stats(
    plot_data, 
    'income_variance', 
    "Distribution of Driver Income Variance (Daily Totals, capped at 99th percentile)",
    "Daily Income Variance",
    color="#e76f51"
)

st.divider()

# --- Per-Day Driver Statistics (New Section) ---
st.header("Per-Day Driver Statistics")

# Helper function to convert ticks to HH:MM:SS format
def ticks_to_time(ticks):
    """Convert simulation ticks to time format (starting at 06:00)"""
    if pd.isna(ticks) or ticks is None:
        return "N/A"
    ticks = int(ticks)
    hours = (ticks // 3600) + 6  # Simulation starts at 6 AM
    minutes = (ticks % 3600) // 60
    seconds = ticks % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def ticks_to_hours(ticks):
    """Convert ticks to hours (for duration display)"""
    if pd.isna(ticks) or ticks is None:
        return 0
    return ticks / 3600

# Check if new columns exist in the driver data
has_duration_data = not df_all_drivers.empty and 'actual_duration' in df_all_drivers.columns

if has_duration_data:
    st.write("This section shows per-day (per-run) statistics for each driver, including actual time spent in the simulation.")

    # Create a summary with formatted times
    per_day_stats = df_all_drivers.copy()

    # Format time columns if they exist
    if 'actual_start_tick' in per_day_stats.columns:
        per_day_stats['start_time'] = per_day_stats['actual_start_tick'].apply(ticks_to_time)
    if 'actual_end_tick' in per_day_stats.columns:
        per_day_stats['end_time'] = per_day_stats['actual_end_tick'].apply(ticks_to_time)
    if 'actual_duration' in per_day_stats.columns:
        per_day_stats['duration_hours'] = per_day_stats['actual_duration'].apply(ticks_to_hours)

    # Select columns to display
    display_cols = ['trike_id', 'run_id', 'hub_id']
    if 'start_time' in per_day_stats.columns:
        display_cols.append('start_time')
    if 'end_time' in per_day_stats.columns:
        display_cols.append('end_time')
    if 'duration_hours' in per_day_stats.columns:
        display_cols.append('duration_hours')
    if 'daily_trips' in per_day_stats.columns:
        display_cols.append('daily_trips')
    if 'daily_income' in per_day_stats.columns:
        display_cols.append('daily_income')
    if 'daily_distance' in per_day_stats.columns:
        display_cols.append('daily_distance')

    # Filter available columns
    display_cols = [c for c in display_cols if c in per_day_stats.columns]

    st.subheader("Per-Day Driver Details")

    # --- Filters ---
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    with filter_col1:
        all_drivers = sorted(per_day_stats['trike_id'].unique())
        selected_drivers = st.multiselect("Filter by Driver", options=all_drivers, default=[], placeholder="All drivers")

    with filter_col2:
        all_runs = sorted(per_day_stats['run_id'].unique())
        selected_runs = st.multiselect("Filter by Day/Run", options=all_runs, default=[], placeholder="All days")

    with filter_col3:
        all_hubs = sorted(per_day_stats['hub_id'].unique())
        selected_hubs = st.multiselect("Filter by Hub", options=all_hubs, default=[], placeholder="All hubs")

    # Apply filters
    filtered_stats = per_day_stats.copy()
    if selected_drivers:
        filtered_stats = filtered_stats[filtered_stats['trike_id'].isin(selected_drivers)]
    if selected_runs:
        filtered_stats = filtered_stats[filtered_stats['run_id'].isin(selected_runs)]
    if selected_hubs:
        filtered_stats = filtered_stats[filtered_stats['hub_id'].isin(selected_hubs)]

    st.caption(f"Showing {len(filtered_stats)} of {len(per_day_stats)} records")
    st.dataframe(filtered_stats[display_cols].sort_values(by=['run_id', 'trike_id']))

    # Summary statistics for duration (uses filtered data)
    if 'actual_duration' in filtered_stats.columns and len(filtered_stats) > 0:
        st.subheader("Driver Duration Statistics (Filtered)")
        col_d1, col_d2, col_d3, col_d4 = st.columns(4)

        avg_duration_hours = filtered_stats['actual_duration'].mean() / 3600
        min_duration_hours = filtered_stats['actual_duration'].min() / 3600
        max_duration_hours = filtered_stats['actual_duration'].max() / 3600
        std_duration_hours = filtered_stats['actual_duration'].std() / 3600

        col_d1.metric("Avg Duration", f"{avg_duration_hours:.2f} hrs")
        col_d2.metric("Min Duration", f"{min_duration_hours:.2f} hrs")
        col_d3.metric("Max Duration", f"{max_duration_hours:.2f} hrs")
        col_d4.metric("Std Dev", f"{std_duration_hours:.2f} hrs")

        # Distribution of driver durations
        st.subheader("Driver Duration Distribution")
        filtered_stats['duration_hours_plot'] = filtered_stats['actual_duration'] / 3600
        plot_distribution_with_stats(
            filtered_stats,
            'duration_hours_plot',
            "Distribution of Driver Time in Simulation",
            "Duration (hours)",
            color="#264653"
        )

    # Per-day income and trips if available (uses filtered data)
    if 'daily_income' in filtered_stats.columns and 'daily_trips' in filtered_stats.columns and len(filtered_stats) > 0:
        st.subheader("Per-Day Performance Summary (Filtered)")
        col_p1, col_p2, col_p3 = st.columns(3)

        avg_daily_trips = filtered_stats['daily_trips'].mean()
        avg_daily_income = filtered_stats['daily_income'].mean()
        avg_daily_distance = filtered_stats['daily_distance'].mean() if 'daily_distance' in filtered_stats.columns else 0

        col_p1.metric("Avg Trips per Driver/Day", f"{avg_daily_trips:.1f}")
        col_p2.metric("Avg Income per Driver/Day", f"PHP {avg_daily_income:,.2f}")
        col_p3.metric("Avg Distance per Driver/Day", f"{avg_daily_distance:,.0f} m")

        # Income per hour analysis
        if 'actual_duration' in filtered_stats.columns:
            filtered_stats['income_per_hour'] = filtered_stats.apply(
                lambda x: x['daily_income'] / (x['actual_duration'] / 3600) if x['actual_duration'] > 0 else 0,
                axis=1
            )
            st.subheader("Income per Hour Distribution")
            plot_distribution_with_stats(
                filtered_stats[filtered_stats['income_per_hour'] > 0],
                'income_per_hour',
                "Distribution of Driver Income per Hour",
                "Income per Hour (PHP)",
                color="#e9c46a"
            )

            avg_income_per_hour = filtered_stats['income_per_hour'].mean()
            st.metric("Average Income per Hour", f"PHP {avg_income_per_hour:,.2f}")

else:
    st.info("Per-day driver statistics (duration, daily trips, daily income) are not available in the current data. "
            "Run the simulation again to generate this data.")

st.divider()

# --- Trip-Level Analytics (Original Section) ---
st.header("Trip-Level Analytics (Based on Analyzed Runs)")

# --- Clean up columns ---
# Select and reorder relevant columns for display
trip_display_cols = ['run_id', 'trike_id', 'hub_id', 'origin_edge', 'dest_edge', 'distance', 'price', 'tick']
# Handle potential duplicate columns from merge (run_id_x, run_id_y)
if 'run_id_x' in df_all.columns:
    df_all['run_id'] = df_all['run_id_x']
if 'run_id_y' in df_all.columns and 'run_id' not in df_all.columns:
    df_all['run_id'] = df_all['run_id_y']
# Filter to only existing columns
trip_display_cols = [c for c in trip_display_cols if c in df_all.columns]

# --- Filters ---
trip_filter_col1, trip_filter_col2, trip_filter_col3, trip_filter_col4 = st.columns(4)

with trip_filter_col1:
    trip_all_drivers = sorted(df_all['trike_id'].unique())
    trip_selected_drivers = st.multiselect("Filter by Driver", options=trip_all_drivers, default=[], placeholder="All drivers", key="trip_driver_filter")

with trip_filter_col2:
    trip_all_runs = sorted(df_all['run_id'].unique()) if 'run_id' in df_all.columns else []
    trip_selected_runs = st.multiselect("Filter by Day/Run", options=trip_all_runs, default=[], placeholder="All days", key="trip_run_filter")

with trip_filter_col3:
    if 'hub_id' in df_all.columns:
        trip_all_hubs = sorted(df_all['hub_id'].dropna().unique())
        trip_selected_hubs = st.multiselect("Filter by Hub", options=trip_all_hubs, default=[], placeholder="All hubs", key="trip_hub_filter")
    else:
        trip_selected_hubs = []

with trip_filter_col4:
    row_limit = st.selectbox("Rows to display", options=[20, 50, 100, 250, 500, "All"], index=0, key="trip_row_limit")

# Apply filters
filtered_trips = df_all.copy()
if trip_selected_drivers:
    filtered_trips = filtered_trips[filtered_trips['trike_id'].isin(trip_selected_drivers)]
if trip_selected_runs and 'run_id' in filtered_trips.columns:
    filtered_trips = filtered_trips[filtered_trips['run_id'].isin(trip_selected_runs)]
if trip_selected_hubs and 'hub_id' in filtered_trips.columns:
    filtered_trips = filtered_trips[filtered_trips['hub_id'].isin(trip_selected_hubs)]

# Apply row limit
if row_limit == "All":
    display_trips = filtered_trips[trip_display_cols].sort_values(by=['run_id', 'tick'] if 'run_id' in trip_display_cols else ['tick'])
else:
    display_trips = filtered_trips[trip_display_cols].sort_values(by=['run_id', 'tick'] if 'run_id' in trip_display_cols else ['tick']).head(row_limit)

st.caption(f"Showing {len(display_trips)} of {len(filtered_trips)} filtered trips ({len(df_all)} total)")
st.dataframe(display_trips)

# Create columns for the plots
col_a = st.columns(1)[0]

with col_a:
    # Show histogram of trip distances
    st.subheader("Trip Distance Distribution")
    plot_distribution_with_stats(
        df_all, 
        'distance', 
        "Trip Distance Distribution",
        "Distance (meters)",
        color="skyblue"
    
    )

     # Show histogram of trip prices
    st.subheader("Trip Price Distribution")
    plot_distribution_with_stats(
        df_all, 
        'price', 
        "Trip Price Distribution",
        "Price (PHP)",
        color="lightgreen"
    )
    
    # histogram of tick
    st.subheader("Trips Over Time (by Tick)")
    plot_distribution_with_stats(
        df_all, 
        'tick', 
        "Trips Over Time",
        "Tick",
        color="violet"
    )
   

