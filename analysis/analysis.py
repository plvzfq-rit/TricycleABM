import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import re # For cleaning expense amount
import numpy as np
import scipy.stats as stats

# Set page config for a wider layout
st.set_page_config(layout="wide")

## --- Helper Function ---

# Regex to find numbers in the amount column (handles floats, ints)
# It will find '310.96864488' in '[310.96864488]'
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

## --- NEW: Sidebar Configuration ---
st.sidebar.header("Analysis Configuration")

# 1. Select Log Directory
# Find all directories that match the expected pattern
available_logs = ["Driver_55.9", "Driver_58.9", "Manila_55.9", "Manila_58.9"] 
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

total_runs_found = len(all_folders)

# We need at least 1 run for analysis, so max_skip is total - 1
# But if we have 0 or 1 run, max_skip should be 0.
max_skip = max(0, total_runs_found - 1) 

runs_to_skip = st.sidebar.number_input(
    "Number of runs to skip (from end)", 
    min_value=0, 
    max_value=max_skip, 
    value=0, 
    step=1,
    help=f"Skips the last N simulation folders. {total_runs_found} runs found in '{LOG_DIRECTORY}'. You can skip up to {max_skip}."
)

# Get the final list of folders to process for the main analysis
end_index = total_runs_found - runs_to_skip
folders_to_process = all_folders[:end_index]


## --- DATA LOADING (PASS 1: Pre-analysis for ALL runs) ---
# This pass calculates the run profit for ALL folders, ignoring the skip,
# to provide a stable "Required Runs" recommendation.

all_run_profits = []
for folder in all_folders: # Note: Looping over 'all_folders'
    folder_path = os.path.join(LOG_DIRECTORY, folder)
    transactions_file = os.path.join(folder_path, "transactions.csv")
    expenses_file = os.path.join(folder_path, "expenses.csv")

    if not (os.path.exists(transactions_file) and os.path.exists(expenses_file)):
        continue # Skip if essential files are missing

    try:
        transaction_df = pd.read_csv(transactions_file)
        expenses_df = pd.read_csv(expenses_file)
        
        expenses_df["amount"] = expenses_df["amount"].apply(extract_amount)
        expenses_df.dropna(subset=['amount'], inplace=True) 

        run_income_by_trike = transaction_df.groupby('trike_id')['price'].sum()
        run_expense_by_trike = expenses_df.groupby('trike_id')['amount'].sum()
        run_profit_by_trike = run_income_by_trike.sub(run_expense_by_trike, fill_value=0)
        
        run_mean_profit = run_profit_by_trike.mean()
        if not pd.isna(run_mean_profit):
            all_run_profits.append(run_mean_profit)
            
    except Exception as e:
        st.warning(f"Pre-analysis error in folder {folder}: {e}. Skipping for recommendation.")

all_run_profits_series = pd.Series(all_run_profits)


## --- DATA LOADING (PASS 2: Main Analysis for Filtered Runs) ---

df_all_list = []
df_expenses_list = []
filtered_run_profits = [] # Stores profit for *analyzed* runs

sim_count = 0

# USES THE FILTERED LIST 'folders_to_process'
for folder in folders_to_process:
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
        
        # --- Calculate Run-Level Profit (for Stability Analysis) ---
        run_income_by_trike = transaction_df.groupby('trike_id')['price'].sum()
        run_expense_by_trike = expenses_df.groupby('trike_id')['amount'].sum()
        run_profit_by_trike = run_income_by_trike.sub(run_expense_by_trike, fill_value=0)
        
        # Get the mean profit per trike *for this single run*
        run_mean_profit = run_profit_by_trike.mean()
        if not pd.isna(run_mean_profit):
            filtered_run_profits.append(run_mean_profit)
        
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

# Create a series of the mean profits from the *filtered* runs
filtered_run_profits_series = pd.Series(filtered_run_profits)

# Drop any rows where expense amount could not be parsed
df_all_expenses.dropna(subset=['amount'], inplace=True)

## --- NEW DRIVER-CENTRIC ANALYSIS ---
# This section remains the same, based on the filtered data
# ... (rest of driver_stats calculations) ...

# 1. Total Income per driver (grouped by trike_id)
income_by_driver = df_all.groupby('trike_id')['price'].sum().reset_index().rename(columns={'price': 'total_income'})

# 2. Total Expenses per driver (grouped by trike_id)
expenses_by_driver = df_all_expenses.groupby('trike_id')['amount'].sum().reset_index().rename(columns={'amount': 'total_expenses'})

# 3. Income Variance per driver (grouped by trike_id)
# .var() returns NaN for a single trip; we fillna(0) for cleaner tables.
variance_by_driver = df_all.groupby('trike_id')['price'].var().reset_index().rename(columns={'price': 'income_variance'}).fillna(0)

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
st.write(f"Analyzed **{sim_count}** simulation run(s) from `{LOG_DIRECTORY}` (skipped last {runs_to_skip}).")
st.write(f"Found **{total_runs_found}** total runs. 'Required Runs' recommendation is based on all runs.")
st.divider()

# --- Global Metrics ---
st.header("Overall Simulation Metrics (Based on Analyzed Runs)")
col1, col2, col3 = st.columns(3)
# ... (rest of global metrics) ...
col1.metric("Total Trips", f"{len(df_all):,}")
col2.metric("Total Distance", f"{df_all['distance'].sum():,.0f} m")
col3.metric("Total Income", f"{df_all['price'].sum():,.2f}")
col1.metric("Total Expenses", f"{df_all_expenses['amount'].sum():,.2f}")
col2.metric("Total Profit", f"{(df_all['price'].sum() - df_all_expenses['amount'].sum()):,.2f}")
st.divider()

# --- NEW: Simulation Stability Analysis (Based on TricycleABM_Paper.pdf) ---
st.header("Simulation Stability & Run Analysis")

st.write("This analysis estimates the stability of your simulation's **Mean Trike Profit**.")

# --- Part 1: Required Runs Recommendation (based on ALL runs) ---
st.subheader(f"Part 1: Required Runs Recommendation (Based on ALL {len(all_run_profits_series)} Runs)")

if len(all_run_profits_series) < 3:
    st.warning(f"Found only {len(all_run_profits_series)} total run(s). Please run at least 3 simulations to generate a recommendation.", icon="⚠️")
else:
    # --- 1. Calculate Stats from ALL runs ---
    n_total = len(all_run_profits_series)
    mean_total = all_run_profits_series.mean()
    std_total = all_run_profits_series.std()
    cv_total = std_total / abs(mean_total) if mean_total != 0 else 0 
    
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("Total Runs Found (n)", f"{n_total}")
    col_s2.metric("Overall Mean Profit (x̄)", f"{mean_total:,.2f}")
    col_s3.metric("Overall Std. Dev (s)", f"{std_total:,.2f}")
    col_s4.metric("Overall CV", f"{cv_total:,.3f}")

    # --- 2. User Inputs for Desired Precision ---
    st.write("How precise do you want your final result to be?")
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        confidence = st.select_slider(
            "Desired Confidence Level",
            options=[0.90, 0.95, 0.99],
            value=0.95,
            format_func=lambda x: f"{int(x*100)}%"
        )
    with col_i2:
        precision = st.select_slider(
            "Desired Precision (w) (as % of mean)",
            options=[0.01, 0.02, 0.05, 0.10, 0.15],
            value=0.05,
            format_func=lambda x: f"±{x*100:.0f}%"
        )

    # --- 3. Calculations for Required Runs ---
    alpha = 1 - confidence
    w = precision # Desired precision (width)
    
    t_z_cutoff = 100 # From the paper
    z_val = stats.norm.ppf(1 - alpha/2)
    n_z = (z_val * cv_total / w)**2

    if n_z >= t_z_cutoff:
        n_required = np.ceil(n_z)
    else:
        # Iterative solution using t-distribution
        n_new = n_z
        if n_new <= 1: n_new = 2 
        for _ in range(10):
            df = n_new - 1
            if df < 1: df = 1 
            t_val = stats.t.ppf(1 - alpha/2, df)
            n_new = (t_val * cv_total / w)**2
        n_required = np.ceil(n_new)
    
    st.success(f"**Recommendation:** To achieve **±{w*100:.0f}%** precision, you should aim to run approximately **{int(n_required)}** total simulations.")
    
    if n_required > n_total:
        st.warning(f"Based on your current {n_total} runs, you may need **{int(n_required - n_total)}** more simulations to meet your goal.")
    else:
        st.balloons()
        st.success("Congratulations! You have already run enough simulations to meet your desired precision level.")

# --- Part 2: Current Precision (based on FILTERED runs) ---
st.subheader(f"Part 2: Current Analysis Precision (Based on {sim_count} Analyzed Runs)")

if sim_count < 3:
     st.warning(f"You have analyzed {sim_count} simulation(s). Please analyze at least 3 simulations (by reducing 'runs to skip') to calculate your current precision.", icon="⚠️")
else:
    # --- Calculate Stats from FILTERED runs ---
    n_current = len(filtered_run_profits_series)
    mean_current = filtered_run_profits_series.mean()
    std_current = filtered_run_profits_series.std()
    cv_current = std_current / abs(mean_current) if mean_current != 0 else 0 

    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    col_c1.metric("Analyzed Runs (n)", f"{n_current}")
    col_c2.metric("Analyzed Mean Profit (x̄)", f"{mean_current:,.2f}")
    col_c3.metric("Analyzed Std. Dev (s)", f"{std_current:,.2f}")
    col_c4.metric("Analyzed CV", f"{cv_current:,.3f}")

    # --- Calculate CURRENT precision (w_current) ---
    df_current = n_current - 1
    t_val_current = stats.t.ppf(1 - (1 - confidence)/2, df_current)
    w_current = (t_val_current * cv_current) / np.sqrt(n_current)

    st.info(f"**Your Current Precision:** With the **{n_current} runs** you are analyzing, your result is precise to **±{w_current*100:,.1f}%** (at {confidence*100:.0f}% confidence).")

st.divider()


# --- Driver Analytics (New Section) ---
st.header("Driver-Level Analytics (Based on Analyzed Runs)")
st.write(f"Summary of driver performance, averaged over **{sim_count}** simulation run(s). 'Trike ID' is the consistent identifier across all runs.")
# ... (rest of app) ...
st.dataframe(driver_stats.sort_values(by='avg_daily_profit', ascending=False))

st.subheader("Driver Average Daily Profit Distribution")
fig, ax = plt.subplots()
ax.hist(driver_stats['avg_daily_profit'], bins=50, color='#2a9d8f', edgecolor='black')
ax.set_xlabel("Average Daily Profit (currency units)")
ax.set_ylabel("Number of Drivers")
ax.set_title("Distribution of Driver Average Daily Profits")
st.pyplot(fig)

st.subheader("Driver Income Variance Distribution")
st.write("Variance measures the consistency of a driver's income per trip. High variance means unpredictable income (e.g., many low-fare trips and a few high-fare ones). Low variance means most trips earn a similar amount.")
fig, ax = plt.subplots()
# Filter out extreme outliers for a better plot, e.g., > 99th percentile
q99 = driver_stats['income_variance'].quantile(0.99)
if q99 > 0:
    plot_data = driver_stats[driver_stats['income_variance'] < q99]['income_variance']
else:
    plot_data = driver_stats['income_variance'] # Show all if q99 is 0
    
ax.hist(plot_data, bins=50, color='#e76f51', edgecolor='black')
ax.set_xlabel("Income Variance")
ax.set_ylabel("Number of Drivers")
ax.set_title("Distribution of Driver Income Variance (capped at 99th percentile for readability)")
st.pyplot(fig)

st.divider()

# --- Trip-Level Analytics (Original Section) ---
st.header("Trip-Level Analytics (Based on Analyzed Runs)")

# Show first few rows of the dataframe
st.subheader("Sample Trip Data (Merged)")
st.dataframe(df_all.head(20))

# Create columns for the plots
col_a, col_b = st.columns(2)

with col_a:
    # Show histogram of trip distances
    st.subheader("Trip Distance Distribution")
    fig, ax = plt.subplots()
    ax.hist(df_all['distance'], bins=30, color='skyblue', edgecolor='black')
    ax.set_xlabel("Distance (meters)")
    ax.set_ylabel("Number of Trips")
    st.pyplot(fig)

    # Show scatter plot of distance vs price
    st.subheader("Distance vs Price")
    fig, ax = plt.subplots()
    ax.scatter(df_all['distance'], df_all['price'], alpha=0.5)
    ax.set_xlabel("Distance (meters)")
    ax.set_ylabel("Price (currency units)")
    st.pyplot(fig)

with col_b:
    # Show histogram of trip prices
    st.subheader("Trip Price Distribution")
    fig, ax = plt.subplots()
    ax.hist(df_all['price'], bins=30, color='lightgreen', edgecolor='black')
    ax.set_xlabel("Price (currency units)")
    ax.set_ylabel("Number of Trips")
    st.pyplot(fig)
    
    # histogram of tick
    st.subheader("Trips Over Time (by Tick)")
    fig, ax = plt.subplots()
    ax.hist(df_all['tick'], bins=50, color='violet', edgecolor='black')
    ax.set_xlabel("Tick")
    ax.set_ylabel("Number of Trips")
    st.pyplot(fig)

# Show average price per distance bucket
st.subheader("Average Price per Distance Bucket")
if not df_all.empty:
    max_dist = df_all['distance'].max()
    if pd.isna(max_dist) or max_dist == 0:
        max_dist = 500 # Default value if no data
        
    try:
        # Ensure at least one bin
        bins = range(0, max(501, int(max_dist) + 500), 500)
        if len(bins) < 2:
             bins = [0, 500]
             
        df_all['distance_bucket'] = pd.cut(df_all['distance'], bins=bins)
        avg_price_per_bucket = df_all.groupby('distance_bucket', observed=True)['price'].mean().reset_index()
        
        fig, ax = plt.subplots()
        ax.bar(avg_price_per_bucket['distance_bucket'].astype(str), avg_price_per_bucket['price'], color='salmon', edgecolor='black')
        ax.set_xlabel("Distance Bucket (meters)")
        ax.set_ylabel("Average Price (currency units)")
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)
    except Exception as e:
        st.write(f"Could not plot distance buckets: {e}")
else:
    st.write("No trip data to plot for distance buckets.")