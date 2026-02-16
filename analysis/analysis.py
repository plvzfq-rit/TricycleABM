import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import sqlite3
import os

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Tricycle Market Analysis", layout="wide")
sns.set_theme(style="whitegrid")

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def plot_distribution(data, x_col, title, xlabel, ylabel="Count", color="skyblue", bins=30):
    """Histogram + KDE with descriptive stats box."""
    if data.empty or x_col not in data.columns:
        st.write(f"No data for {title}")
        return
    series = data[x_col].dropna()
    if series.empty:
        st.write(f"No data for {title}")
        return
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(series, bins=bins, color=color, kde=True, ax=ax, edgecolor="black")
    stats = (
        f"Mean: {series.mean():,.2f}\n"
        f"Median: {series.median():,.2f}\n"
        f"Std: {series.std():,.2f}\n"
        f"N: {len(series):,}"
    )
    ax.text(0.95, 0.95, stats, transform=ax.transAxes, fontsize=9,
            va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.pyplot(fig, use_container_width=False)
    plt.close(fig)


def gini_coefficient(values):
    """Compute Gini coefficient for a 1-D array of non-negative values."""
    v = np.sort(np.asarray(values, dtype=float))
    v = v[~np.isnan(v)]
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    index = np.arange(1, n + 1)
    return (2 * np.sum(index * v) - (n + 1) * np.sum(v)) / (n * np.sum(v))


def lorenz_curve(values, label="", ax=None):
    """Plot Lorenz curve on given axes."""
    v = np.sort(np.asarray(values, dtype=float))
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return
    cum = np.concatenate(([0], np.cumsum(v) / v.sum()))
    x = np.linspace(0, 1, len(cum))
    if ax is None:
        _, ax = plt.subplots()
    ax.plot(x, cum, label=label)
    ax.plot([0, 1], [0, 1], 'k--', alpha=0.4, label='Perfect equality')
    ax.set_xlabel("Cumulative share of agents")
    ax.set_ylabel("Cumulative share of value")


def income_shares(values, top_pct=0.10, bottom_pct=0.40):
    """Return top X% share and bottom Y% share of total."""
    v = np.sort(np.asarray(values, dtype=float))
    v = v[~np.isnan(v)]
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0, 0.0
    top_n = max(1, int(np.ceil(n * top_pct)))
    bottom_n = max(1, int(np.ceil(n * bottom_pct)))
    total = v.sum()
    top_share = v[-top_n:].sum() / total
    bottom_share = v[:bottom_n].sum() / total
    return top_share, bottom_share


# ---------------------------------------------------------------------------
# Database connection
# ---------------------------------------------------------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "db", "simulation_logs.db")
DB_PATH = os.path.normpath(DB_PATH)

if not os.path.isfile(DB_PATH):
    st.error(f"Database not found at `{DB_PATH}`. Run the simulation first.")
    st.stop()


@st.cache_data(ttl=60)
def load_data():
    conn = sqlite3.connect(DB_PATH)

    runs = pd.read_sql("SELECT * FROM runs", conn)
    drivers = pd.read_sql("SELECT * FROM drivers", conn)
    passengers = pd.read_sql("SELECT * FROM passengers", conn)
    transactions = pd.read_sql("SELECT * FROM passenger_transactions", conn)
    neg_steps = pd.read_sql("SELECT * FROM negotiation_steps", conn)
    expenses = pd.read_sql("SELECT * FROM expenses", conn)

    conn.close()
    return runs, drivers, passengers, transactions, neg_steps, expenses


runs_df, drivers_df, passengers_df, txn_df, neg_df, expenses_df = load_data()

if txn_df.empty:
    st.warning("No transaction data found. Run the simulation first.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar - run selection
# ---------------------------------------------------------------------------
st.sidebar.header("Configuration")
all_run_ids = sorted(runs_df["id"].unique())
selected_runs = st.sidebar.multiselect(
    "Select simulation runs",
    options=all_run_ids,
    default=all_run_ids,
    help="Leave empty to include all runs"
)
if not selected_runs:
    selected_runs = all_run_ids

# Filter data to selected runs
drivers = drivers_df[drivers_df["run_id"].isin(selected_runs)].copy()
passengers = passengers_df[passengers_df["run_id"].isin(selected_runs)].copy()
txn = txn_df[txn_df["run_id"].isin(selected_runs)].copy()
neg = neg_df[neg_df["transaction_id"].isin(txn["id"])].copy()
expenses = expenses_df[expenses_df["run_id"].isin(selected_runs)].copy()

n_runs = len(selected_runs)

# ---------------------------------------------------------------------------
# Pre-compute useful columns
# ---------------------------------------------------------------------------
# Merge driver info onto transactions
txn = txn.merge(
    drivers[["id", "trike_code", "hub", "gas_consumption_rate",
             "aspired_price", "minimum_price"]],
    left_on="driver_id", right_on="id", how="left", suffixes=("", "_drv")
)
# Merge passenger info onto transactions
txn = txn.merge(
    passengers[["id", "willingness_to_pay", "aspired_price"]],
    left_on="passenger_id", right_on="id", how="left", suffixes=("", "_pax")
)

# Compute passenger WTP & aspired price in absolute terms (per-km * distance/1000)
txn["pax_wtp"] = txn["willingness_to_pay"] * txn["distance"] / 1000.0
txn["pax_asp_abs"] = txn["aspired_price_pax"] * txn["distance"] / 1000.0

# Get initial negotiation step for driver asp at start of negotiation
init_neg = neg[neg["iteration"] == 0].drop_duplicates(subset=["transaction_id"])
txn = txn.merge(
    init_neg[["transaction_id", "driver_asp", "passenger_asp"]],
    left_on="id", right_on="transaction_id", how="left", suffixes=("", "_neg")
)

# Marginal cost proxy: gas_consumption_rate * distance * gas_price_per_liter
# gas_consumption_rate is liters/meter essentially; gas price ~ 58.9 PHP/L
GAS_PRICE = 58.9
txn["marginal_cost"] = txn["gas_consumption_rate"] * txn["distance"] * GAS_PRICE

# Separate accepted / failed negotiation / rejected (too far)
accepted = txn[txn["result"] == "agree"].copy()
failed_neg = txn[txn["result"] == "failed"].copy()
rejected = txn[txn["result"] == "reject"].copy()
not_accepted = txn[txn["result"] != "agree"].copy()

# Consumer surplus (accepted only)
accepted["consumer_surplus"] = accepted["pax_wtp"] - accepted["final_price"]
# Producer surplus (accepted only)
accepted["producer_surplus"] = accepted["final_price"] - accepted["marginal_cost"]

# ---------------------------------------------------------------------------
# TITLE
# ---------------------------------------------------------------------------
st.title("Measurement Framework: Tricycle Negotiation Market")
st.markdown(
    "A multi-dimensional measurement framework for evaluating access, welfare, "
    "inequality, bargaining distribution, and spatial heterogeneity in a Monte Carlo "
    "simulation of negotiated tricycle fares. The framework is **descriptive and "
    "comparative**, not causal."
)
st.caption(f"Analyzing **{n_runs}** simulation run(s)  |  "
           f"{len(txn):,} total transactions  |  "
           f"{len(accepted):,} accepted  |  "
           f"{len(failed_neg):,} failed negotiations  |  "
           f"{len(rejected):,} rejected (too far)")
st.divider()

# =========================================================================
# SECTION 1 - Passenger Outcome Metrics
# =========================================================================
st.header("1. Passenger Outcome Metrics")
st.markdown(
    "These metrics measure **access** (whether passengers are served) and "
    "**realized welfare** (the economic benefit passengers receive from completed "
    "transactions)."
)

# 1.1 Access Ratios
st.subheader("1.1 Access Ratios")
st.markdown(
    "Access ratios decompose every passenger interaction into one of three outcomes:\n"
    "- **Served (Accepted):** Negotiation succeeded and the passenger was transported.\n"
    "- **Failed Negotiation:** A negotiation took place but driver and passenger "
    "could not agree on a fare.\n"
    "- **Rejected (Too Far):** The passenger's destination exceeded the driver's "
    "maximum service distance (`farthest_distance`), so no negotiation was attempted."
)
total_txn = len(txn)
n_accepted = len(accepted)
n_failed = len(failed_neg)
n_rejected = len(rejected)
c1, c2, c3, c4 = st.columns(4)
c1.metric("% Served", f"{n_accepted / total_txn * 100:.1f}%" if total_txn else "N/A")
c2.metric("% Failed Negotiation", f"{n_failed / total_txn * 100:.1f}%" if total_txn else "N/A")
c3.metric("% Rejected (Too Far)", f"{n_rejected / total_txn * 100:.1f}%" if total_txn else "N/A")
c4.metric("Total Interactions", f"{total_txn:,}")

# Pie chart of outcomes
fig_pie, ax_pie = plt.subplots(figsize=(4, 4))
outcome_counts = [n_accepted, n_failed, n_rejected]
outcome_labels = [
    f"Served\n({n_accepted:,})",
    f"Failed Negotiation\n({n_failed:,})",
    f"Rejected (Too Far)\n({n_rejected:,})"
]
outcome_colors = ["#2a9d8f", "#e76f51", "#e9c46a"]
# Only plot non-zero slices
nonzero = [(c, l, co) for c, l, co in zip(outcome_counts, outcome_labels, outcome_colors) if c > 0]
if nonzero:
    ax_pie.pie(
        [x[0] for x in nonzero],
        labels=[x[1] for x in nonzero],
        colors=[x[2] for x in nonzero],
        autopct='%1.1f%%', startangle=90
    )
    ax_pie.set_title("Transaction Outcome Breakdown")
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.pyplot(fig_pie, use_container_width=False)
    plt.close(fig_pie)

# 1.2 Consumer Surplus
st.subheader("1.2 Consumer Surplus")
st.markdown(
    "For each accepted transaction: **Consumer Surplus = Passenger WTP - Final Price**.\n\n"
    "This measures the welfare gain a passenger receives relative to the maximum they "
    "were willing to pay. A higher consumer surplus indicates passengers are paying "
    "well below their reservation price."
)
if not accepted.empty:
    cs_total = accepted["consumer_surplus"].sum()
    cs_mean = accepted["consumer_surplus"].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Consumer Surplus", f"PHP {cs_total:,.2f}")
    c2.metric("Avg Consumer Surplus / Passenger", f"PHP {cs_mean:,.2f}")
    c3.metric("Median Consumer Surplus", f"PHP {accepted['consumer_surplus'].median():,.2f}")

    # Hub-level consumer surplus
    hub_cs = accepted.groupby("hub")["consumer_surplus"].agg(["sum", "mean", "count"]).reset_index()
    hub_cs.columns = ["Hub", "Total CS", "Avg CS", "Transactions"]
    st.dataframe(hub_cs.sort_values("Total CS", ascending=False), use_container_width=True)

    plot_distribution(accepted, "consumer_surplus",
                      "Consumer Surplus Distribution", "Consumer Surplus (PHP)", color="#2a9d8f")
else:
    st.info("No accepted transactions to compute consumer surplus.")

st.divider()

# =========================================================================
# SECTION 2 - Driver Outcome Metrics
# =========================================================================
st.header("2. Driver Outcome Metrics")
st.markdown(
    "These metrics measure **economic sustainability** and **rent capture** for "
    "drivers. They answer the question: can drivers sustain their livelihoods under "
    "the negotiated fare regime?"
)

# 2.1 Income and Profit
st.subheader("2.1 Income and Profit")
st.markdown(
    "- **Income** = Sum of all accepted fares for a driver.\n"
    "- **Profit** = Income - Total Expenses.\n"
    "- Expenses include **fuel costs** (end-of-day and midday refueling) and "
    "**daily operating costs** (food, vehicle maintenance, etc.)."
)

driver_income = accepted.groupby("driver_id")["final_price"].sum().reset_index()
driver_income.columns = ["driver_id", "income"]

driver_expenses = expenses.groupby("driver_id")["amount"].sum().reset_index()
driver_expenses.columns = ["driver_id", "total_expenses"]

# Breakdown by expense type
fuel_expenses = expenses[expenses["expense_type"].isin(["end_gas", "midday_gas"])].groupby("driver_id")["amount"].sum().reset_index()
fuel_expenses.columns = ["driver_id", "fuel_cost"]

daily_exp = expenses[expenses["expense_type"] == "daily_expense"].groupby("driver_id")["amount"].sum().reset_index()
daily_exp.columns = ["driver_id", "daily_expense_total"]

driver_profit = drivers[["id", "trike_code", "hub", "run_id"]].copy()
driver_profit = driver_profit.merge(driver_income, left_on="id", right_on="driver_id", how="left")
driver_profit = driver_profit.merge(driver_expenses, left_on="id", right_on="driver_id", how="left", suffixes=("", "_exp"))
driver_profit = driver_profit.merge(fuel_expenses, left_on="id", right_on="driver_id", how="left", suffixes=("", "_fuel"))
driver_profit = driver_profit.merge(daily_exp, left_on="id", right_on="driver_id", how="left", suffixes=("", "_daily"))
driver_profit["income"] = driver_profit["income"].fillna(0)
driver_profit["total_expenses"] = driver_profit["total_expenses"].fillna(0)
driver_profit["fuel_cost"] = driver_profit["fuel_cost"].fillna(0)
driver_profit["daily_expense_total"] = driver_profit["daily_expense_total"].fillna(0)
driver_profit["profit"] = driver_profit["income"] - driver_profit["total_expenses"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Driver Income", f"PHP {driver_profit['income'].sum():,.2f}")
c2.metric("Total Expenses", f"PHP {driver_profit['total_expenses'].sum():,.2f}")
c3.metric("Total Profit", f"PHP {driver_profit['profit'].sum():,.2f}")
c4.metric("Avg Profit / Driver", f"PHP {driver_profit['profit'].mean():,.2f}")

display_cols = ["trike_code", "hub", "run_id", "income", "fuel_cost",
                "daily_expense_total", "total_expenses", "profit"]
st.dataframe(
    driver_profit[display_cols].sort_values("profit", ascending=False),
    use_container_width=True
)

plot_distribution(driver_profit, "profit", "Driver Profit Distribution",
                  "Profit (PHP)", color="#264653")

# 2.2 Sustainability Ratios
st.subheader("2.2 Sustainability Ratios")
st.markdown(
    "Two thresholds evaluate whether drivers can sustain operations:\n\n"
    "| Threshold | Condition | Interpretation |\n"
    "|---|---|---|\n"
    "| **Covers Fuel** | Income >= Fuel cost | Can the driver keep the vehicle running? |\n"
    "| **Profitable** | Profit > 0 (Income > All expenses) | Does the driver take home any net earnings? |\n\n"
    "*Fuel cost = end-of-day + midday refueling. "
    "Total expenses = Fuel cost + Daily operating cost (food, maintenance, etc.).*"
)
n_drivers = len(driver_profit)
covers_fuel = (driver_profit["income"] >= driver_profit["fuel_cost"]).sum()
profitable = (driver_profit["profit"] > 0).sum()

c1, c2 = st.columns(2)
c1.metric("Covers Fuel", f"{covers_fuel}/{n_drivers} ({covers_fuel/n_drivers*100:.1f}%)" if n_drivers else "N/A",
          help="Income >= Fuel cost (end_gas + midday_gas)")
c2.metric("Profitable", f"{profitable}/{n_drivers} ({profitable/n_drivers*100:.1f}%)" if n_drivers else "N/A",
          help="Income > Fuel cost + Daily operating expense")

# Breakdown: show how many drivers fall into each category
n_below_fuel = n_drivers - covers_fuel
n_covers_fuel_only = covers_fuel - profitable
n_profitable = profitable
st.markdown(
    f"**Breakdown:** "
    f"{n_below_fuel} cannot cover fuel | "
    f"{n_covers_fuel_only} cover fuel but not daily expenses | "
    f"{n_profitable} profitable"
)

# Stacked bar visualization
fig_sust, ax_sust = plt.subplots(figsize=(6, 1.5))
categories = [n_below_fuel, n_covers_fuel_only, n_profitable]
cat_labels = ["Below fuel cost", "Covers fuel only", "Profitable"]
cat_colors = ["#e76f51", "#f4a261", "#2a9d8f"]
left = 0
for count, label, color in zip(categories, cat_labels, cat_colors):
    if count > 0:
        ax_sust.barh(0, count, left=left, color=color, edgecolor="white", label=f"{label} ({count})")
        left += count
ax_sust.set_xlim(0, n_drivers)
ax_sust.set_yticks([])
ax_sust.set_xlabel("Number of drivers")
ax_sust.legend(loc="upper center", bbox_to_anchor=(0.5, -0.3), ncol=3, fontsize=8)
plt.tight_layout()
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.pyplot(fig_sust, use_container_width=False)
plt.close(fig_sust)

# 2.3 Producer Surplus
st.subheader("2.3 Producer Surplus")
st.markdown(
    "For each accepted transaction: **Producer Surplus = Final Price - Marginal Cost**.\n\n"
    "Marginal cost is estimated as `gas_consumption_rate x distance x gas_price_per_liter`. "
    "This measures the economic rent per trip, distinct from accounting profit (which "
    "also includes fixed daily expenses)."
)
if not accepted.empty:
    ps_total = accepted["producer_surplus"].sum()
    ps_mean = accepted["producer_surplus"].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Producer Surplus", f"PHP {ps_total:,.2f}")
    c2.metric("Avg Producer Surplus / Trip", f"PHP {ps_mean:,.2f}")
    c3.metric("Median Producer Surplus", f"PHP {accepted['producer_surplus'].median():,.2f}")

    plot_distribution(accepted, "producer_surplus",
                      "Producer Surplus Distribution", "Producer Surplus (PHP)", color="#e76f51")

st.divider()

# =========================================================================
# SECTION 3 - System-Level Welfare Metrics
# =========================================================================
st.header("3. System-Level Welfare Metrics")
st.markdown(
    "These metrics assess the overall **allocative efficiency** of the market: "
    "how well the negotiation system converts potential gains from trade into "
    "realized transactions."
)

# 3.1 Total Surplus
st.subheader("3.1 Total Surplus")
st.markdown(
    "**Total Surplus = Consumer Surplus + Producer Surplus** (equivalently, "
    "Passenger WTP - Marginal Cost, summed across accepted transactions). "
    "This is the standard measure of allocative efficiency."
)
if not accepted.empty:
    accepted["total_surplus"] = accepted["consumer_surplus"] + accepted["producer_surplus"]
    ts = accepted["total_surplus"].sum()
    c1, c2 = st.columns(2)
    c1.metric("Total Surplus (Accepted)", f"PHP {ts:,.2f}")
    c2.metric("Avg Total Surplus / Trip", f"PHP {accepted['total_surplus'].mean():,.2f}")

# 3.2 Deadweight Loss
st.subheader("3.2 Deadweight Loss")
st.markdown(
    "When a transaction is **feasible** (Passenger WTP >= Marginal Cost) but "
    "no agreement is reached, the unrealized surplus is counted as **deadweight loss**. "
    "This measures inefficiency due to negotiation breakdown or spatial friction.\n\n"
    "*Note: Rejected transactions (too far) are excluded because they represent "
    "structural infeasibility, not negotiation failure.*"
)
# Only use failed negotiations (not rejections) for DWL
if not failed_neg.empty:
    feasible_failed = failed_neg[failed_neg["pax_wtp"] >= failed_neg["marginal_cost"]].copy()
    feasible_failed["unrealized_surplus"] = feasible_failed["pax_wtp"] - feasible_failed["marginal_cost"]
    dwl = feasible_failed["unrealized_surplus"].sum()
    c1, c2, c3 = st.columns(3)
    c1.metric("Deadweight Loss", f"PHP {dwl:,.2f}")
    c2.metric("Feasible-but-Failed Negotiations", f"{len(feasible_failed):,}")
    c3.metric("Avg Unrealized Surplus", f"PHP {feasible_failed['unrealized_surplus'].mean():,.2f}" if len(feasible_failed) else "N/A")
else:
    st.info("No failed negotiations.")
    dwl = 0

# 3.3 Surplus Realization Rate
st.subheader("3.3 Surplus Realization Rate")
st.markdown(
    "**Realization Rate = Realized Surplus / Feasible Surplus**, where feasible "
    "surplus includes both realized surplus and deadweight loss. A rate of 100% "
    "means every feasible transaction was completed."
)
if not accepted.empty:
    realized = accepted["total_surplus"].sum()
    feasible = realized + dwl
    realization_rate = realized / feasible if feasible > 0 else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Realized Surplus", f"PHP {realized:,.2f}")
    c2.metric("Feasible Surplus", f"PHP {feasible:,.2f}")
    c3.metric("Surplus Realization Rate", f"{realization_rate:.2%}")

st.divider()

# =========================================================================
# SECTION 4 - Distributional Metrics
# =========================================================================
st.header("4. Distributional Metrics")
st.markdown(
    "Aggregate efficiency tells only part of the story. These metrics examine "
    "**how outcomes are distributed** across agents, distinguishing outcome "
    "inequality from bargaining inequality."
)

# 4.1 Income Inequality (measured on profit)
st.subheader("4.1 Income (Profit) Inequality")
st.markdown(
    "Income inequality is measured using driver **profit** (income minus all expenses):\n"
    "- **Gini coefficient:** 0 = perfect equality, 1 = one driver captures all profit.\n"
    "- **Top 10% share:** Fraction of total profit captured by the highest-earning 10%.\n"
    "- **Bottom 40% share:** Fraction captured by the lowest-earning 40%.\n"
    "- **Lorenz curve:** Visual representation; the further from the diagonal, the "
    "greater the inequality."
)
profits = driver_profit["profit"].values
gini = gini_coefficient(profits)
top10, bot40 = income_shares(profits, 0.10, 0.40)

c1, c2, c3 = st.columns(3)
c1.metric("Gini Coefficient", f"{gini:.4f}")
c2.metric("Top 10% Profit Share", f"{top10:.2%}")
c3.metric("Bottom 40% Profit Share", f"{bot40:.2%}")

# Lorenz Curve
fig_lorenz, ax_lorenz = plt.subplots(figsize=(5, 5))
lorenz_curve(profits, label=f"Driver Profit (Gini={gini:.3f})", ax=ax_lorenz)
ax_lorenz.set_title("Lorenz Curve - Driver Profit")
ax_lorenz.legend()
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    st.pyplot(fig_lorenz, use_container_width=False)
plt.close(fig_lorenz)

# 4.2 Surplus Distribution
st.subheader("4.2 Surplus Distribution")
st.markdown(
    "Separate Gini coefficients for consumer and producer surplus reveal whether "
    "inequality stems from **outcome dispersion** (some agents simply have more "
    "transactions) or **bargaining power** (some agents extract more per transaction)."
)
if not accepted.empty:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Consumer Surplus across Passengers**")
        pax_cs = accepted.groupby("passenger_id")["consumer_surplus"].sum()
        gini_cs = gini_coefficient(pax_cs.values)
        st.metric("Gini (Consumer Surplus)", f"{gini_cs:.4f}")
        plot_distribution(pax_cs.reset_index(), "consumer_surplus",
                          "Consumer Surplus per Passenger", "PHP", color="#2a9d8f")

    with col_b:
        st.markdown("**Producer Surplus across Drivers**")
        drv_ps = accepted.groupby("driver_id")["producer_surplus"].sum()
        gini_ps = gini_coefficient(drv_ps.values)
        st.metric("Gini (Producer Surplus)", f"{gini_ps:.4f}")
        plot_distribution(drv_ps.reset_index(), "producer_surplus",
                          "Producer Surplus per Driver", "PHP", color="#e76f51")

st.divider()

# =========================================================================
# SECTION 5 - Bargaining Dynamics
# =========================================================================
st.header("5. Bargaining Dynamics")
st.markdown(
    "These metrics examine the **procedural distribution** within each negotiation: "
    "given a zone of possible agreement, who captures the surplus?"
)

# 5.1 Bargaining Surplus
st.subheader("5.1 Bargaining Surplus")
st.markdown(
    "When Passenger WTP >= Driver ASP, a **zone of possible agreement** exists. "
    "The bargaining surplus is the size of that zone:\n\n"
    "**Bargaining Surplus = Passenger WTP - Driver ASP**\n\n"
    "This is the total value available to be split between driver and passenger "
    "through negotiation."
)
barg = accepted.dropna(subset=["driver_asp", "pax_wtp"]).copy()
barg = barg[barg["pax_wtp"] >= barg["driver_asp"]].copy()
if not barg.empty:
    barg["bargaining_surplus"] = barg["pax_wtp"] - barg["driver_asp"]
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Bargaining Surplus", f"PHP {barg['bargaining_surplus'].mean():,.2f}")
    c2.metric("Total Bargaining Surplus", f"PHP {barg['bargaining_surplus'].sum():,.2f}")
    c3.metric("N (feasible bargains)", f"{len(barg):,}")

    # 5.2 Surplus Capture Ratio
    st.subheader("5.2 Surplus Capture Ratio")
    st.markdown(
        "**Driver Capture Ratio = (Final Price - Driver ASP) / (Passenger WTP - Driver ASP)**\n\n"
        "| Value | Interpretation |\n"
        "|---|---|\n"
        "| Near 1.0 | Driver dominant - fare is close to passenger's maximum |\n"
        "| Near 0.5 | Balanced - surplus is split roughly evenly |\n"
        "| Near 0.0 | Passenger dominant - fare is close to driver's minimum |"
    )
    barg["driver_capture"] = (barg["final_price"] - barg["driver_asp"]) / barg["bargaining_surplus"]
    barg["driver_capture"] = barg["driver_capture"].clip(0, 1)

    cap_mean = barg["driver_capture"].mean()
    c1, c2, c3 = st.columns(3)
    c1.metric("Avg Driver Capture Ratio", f"{cap_mean:.3f}")
    c2.metric("Median Driver Capture", f"{barg['driver_capture'].median():.3f}")
    c3.metric("Std Dev", f"{barg['driver_capture'].std():.3f}")

    plot_distribution(barg, "driver_capture",
                      "Driver Surplus Capture Ratio Distribution",
                      "Capture Ratio (0=Pax dominant, 1=Driver dominant)", color="#f4a261")

    # Scatter: Driver ASP vs Passenger WTP, colored by capture
    fig_sc, ax_sc = plt.subplots(figsize=(6, 5))
    sc = ax_sc.scatter(barg["pax_wtp"], barg["driver_asp"],
                       c=barg["driver_capture"], cmap="RdYlGn_r",
                       alpha=0.6, edgecolors="black", linewidths=0.3, s=20)
    plt.colorbar(sc, ax=ax_sc, label="Driver Capture Ratio")
    lims = [min(barg["pax_wtp"].min(), barg["driver_asp"].min()),
            max(barg["pax_wtp"].max(), barg["driver_asp"].max())]
    ax_sc.plot(lims, lims, "k--", alpha=0.4, label="Equal line")
    ax_sc.set_xlabel("Passenger WTP (PHP)")
    ax_sc.set_ylabel("Driver ASP (PHP)")
    ax_sc.set_title("Bargaining Space: WTP vs Driver ASP")
    ax_sc.legend()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.pyplot(fig_sc, use_container_width=False)
    plt.close(fig_sc)
else:
    st.info("No transactions with Passenger WTP >= Driver ASP found for bargaining analysis.")

st.divider()

# =========================================================================
# SECTION 6 - Spatial (Hub-Level) Analysis
# =========================================================================
st.header("6. Spatial (Hub-Level) Analysis")
st.markdown(
    "The same metrics are decomposed **by hub** to identify spatial heterogeneity "
    "in outcomes. No causal claims are made; these are descriptive decompositions "
    "that reveal whether certain hubs systematically produce better or worse "
    "outcomes for drivers and passengers."
)

hubs = drivers["hub"].dropna().unique()
hub_rows = []

for hub in sorted(hubs):
    hub_driver_ids = drivers[drivers["hub"] == hub]["id"].values
    hub_dp = driver_profit[driver_profit["id"].isin(hub_driver_ids)]
    hub_acc = accepted[accepted["driver_id"].isin(hub_driver_ids)]
    hub_txn = txn[txn["driver_id"].isin(hub_driver_ids)]

    n_hub_drivers = len(hub_dp)
    avg_profit = hub_dp["profit"].mean() if n_hub_drivers else 0
    hub_gini = gini_coefficient(hub_dp["profit"].values) if n_hub_drivers > 1 else 0
    survival = (hub_dp["profit"] > 0).sum() / n_hub_drivers if n_hub_drivers else 0

    n_hub_txn = len(hub_txn)
    n_hub_acc = len(hub_acc)
    served_rate = n_hub_acc / n_hub_txn if n_hub_txn else 0

    avg_cs = hub_acc["consumer_surplus"].mean() if not hub_acc.empty else 0
    avg_ps = hub_acc["producer_surplus"].mean() if not hub_acc.empty else 0

    # Capture ratio for this hub
    hub_barg = hub_acc.dropna(subset=["driver_asp", "pax_wtp"])
    hub_barg = hub_barg[hub_barg["pax_wtp"] >= hub_barg["driver_asp"]]
    if not hub_barg.empty:
        hub_barg_surplus = hub_barg["pax_wtp"] - hub_barg["driver_asp"]
        hub_capture = ((hub_barg["final_price"] - hub_barg["driver_asp"]) / hub_barg_surplus).clip(0, 1).mean()
    else:
        hub_capture = np.nan

    hub_rows.append({
        "Hub": hub,
        "Drivers": n_hub_drivers,
        "Avg Profit": round(avg_profit, 2),
        "Gini": round(hub_gini, 4),
        "Survival Rate": f"{survival:.1%}",
        "Pax Served Rate": f"{served_rate:.1%}",
        "Avg CS": round(avg_cs, 2),
        "Avg PS": round(avg_ps, 2),
        "Capture Ratio": round(hub_capture, 3) if not np.isnan(hub_capture) else "N/A"
    })

hub_table = pd.DataFrame(hub_rows)
st.dataframe(hub_table, use_container_width=True)

# Bar chart of avg profit by hub
if not hub_table.empty:
    fig_hub, ax_hub = plt.subplots(figsize=(8, 4))
    ax_hub.bar(hub_table["Hub"].astype(str), hub_table["Avg Profit"], color="#264653")
    ax_hub.set_xlabel("Hub")
    ax_hub.set_ylabel("Avg Profit (PHP)")
    ax_hub.set_title("Average Driver Profit by Hub")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.tight_layout()
    st.pyplot(fig_hub, use_container_width=True)
    plt.close(fig_hub)

st.divider()

# =========================================================================
# SECTION 7 - Monte Carlo Aggregation
# =========================================================================
st.header("7. Monte Carlo Aggregation (Across Runs)")
st.markdown(
    "Because the model is stochastic, each parameter regime is evaluated using "
    "repeated simulation runs. For each metric, we report the **mean**, **standard "
    "deviation**, **min**, and **max** across runs. This distinguishes structural "
    "properties of the market from stochastic noise."
)

if n_runs < 2:
    st.info("Select multiple runs to see Monte Carlo aggregation statistics.")
else:
    mc_rows = []
    for rid in selected_runs:
        r_txn = txn[txn["run_id"] == rid]
        r_acc = accepted[accepted["run_id"] == rid]
        r_fail_neg = failed_neg[failed_neg["run_id"] == rid]
        r_rej = rejected[rejected["run_id"] == rid]
        r_drv = driver_profit[driver_profit["run_id"] == rid]

        n_txn = len(r_txn)
        served = len(r_acc) / n_txn if n_txn else 0
        failed_pct = len(r_fail_neg) / n_txn if n_txn else 0
        rejected_pct = len(r_rej) / n_txn if n_txn else 0

        cs = r_acc["consumer_surplus"].sum() if not r_acc.empty else 0
        ps = r_acc["producer_surplus"].sum() if not r_acc.empty else 0
        ts_val = cs + ps

        # DWL for this run (failed negotiations only, not rejections)
        ff = r_fail_neg[r_fail_neg["pax_wtp"] >= r_fail_neg["marginal_cost"]]
        run_dwl = (ff["pax_wtp"] - ff["marginal_cost"]).sum() if not ff.empty else 0

        realization = ts_val / (ts_val + run_dwl) if (ts_val + run_dwl) > 0 else 0

        run_gini = gini_coefficient(r_drv["profit"].values)
        avg_profit = r_drv["profit"].mean() if not r_drv.empty else 0

        mc_rows.append({
            "Run": rid,
            "Served %": served,
            "Failed Neg %": failed_pct,
            "Rejected %": rejected_pct,
            "Total CS": cs,
            "Total PS": ps,
            "Total Surplus": ts_val,
            "DWL": run_dwl,
            "Realization Rate": realization,
            "Gini (Profit)": run_gini,
            "Avg Driver Profit": avg_profit,
        })

    mc_df = pd.DataFrame(mc_rows)

    # Summary stats
    st.subheader("7.1 Per-Metric Summary Across Runs")
    metric_cols = ["Served %", "Failed Neg %", "Rejected %",
                   "Total CS", "Total PS", "Total Surplus",
                   "DWL", "Realization Rate", "Gini (Profit)", "Avg Driver Profit"]
    summary_rows = []
    for col in metric_cols:
        vals = mc_df[col]
        summary_rows.append({
            "Metric": col,
            "Mean": f"{vals.mean():.4f}",
            "Std Dev": f"{vals.std():.4f}",
            "Min": f"{vals.min():.4f}",
            "Max": f"{vals.max():.4f}",
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    # Full run-level table
    st.subheader("7.2 Run-Level Detail")
    st.dataframe(mc_df.style.format({
        "Served %": "{:.2%}",
        "Failed Neg %": "{:.2%}",
        "Rejected %": "{:.2%}",
        "Total CS": "PHP {:.2f}",
        "Total PS": "PHP {:.2f}",
        "Total Surplus": "PHP {:.2f}",
        "DWL": "PHP {:.2f}",
        "Realization Rate": "{:.2%}",
        "Gini (Profit)": "{:.4f}",
        "Avg Driver Profit": "PHP {:.2f}",
    }), use_container_width=True)

    # Distribution of key metrics across runs
    st.subheader("7.3 Distribution of Metrics Across Runs")
    plot_distribution(mc_df, "Total Surplus",
                      "Total Surplus Across Runs", "PHP", color="#2a9d8f")
    plot_distribution(mc_df, "Gini (Profit)",
                      "Gini Coefficient Across Runs", "Gini", color="#e76f51")
    plot_distribution(mc_df, "Avg Driver Profit",
                      "Average Driver Profit Across Runs", "PHP", color="#264653")

st.divider()
st.caption("Measurement framework: descriptive and comparative, not causal. "
           "See design document for interpretive boundaries.")
