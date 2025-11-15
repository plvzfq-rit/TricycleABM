import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

## DATA LOADING

LOG_DIRECTORY = r"logs"

df_all = pd.DataFrame()

# Go through every folder
sim_count = 0
for folder in os.listdir(LOG_DIRECTORY):
    folder_path = os.path.join(LOG_DIRECTORY, folder)
    if not os.path.isdir(folder_path):
        continue
    print(f"Folder: {folder}")
    # go through every file in the folder
    driver_df = pd.read_csv(os.path.join(folder_path, "drivers.csv"))
    print(driver_df.head())
    transaction_df = pd.read_csv(os.path.join(folder_path, "transactions.csv"))
    print(transaction_df.head())

    # merge the two dataframes on taxi_id
    merged_df = pd.merge(transaction_df, driver_df, left_on="trike_id", right_on="trike_id", how="left")

    # merge run_id with taxi_id to create a unique identifier
    merged_df["trike_id"] = merged_df["run_id"].astype(str) + "_" + merged_df["trike_id"].astype(str)
    merged_df.drop(columns=["run_id"], inplace=True)
    print(merged_df.head())

    ## add to overall dataframe
    df_all = pd.concat([df_all, merged_df], ignore_index=True)

## Copilot tab enter magic
st.title("Tricycle Simulation Analysis")
st.write(f"Total distance traveled: {df_all['distance'].sum()} meters")
st.write(f"Average distance per trip: {df_all['distance'].mean()} meters")
st.write(f"Average price per trip: {df_all['price'].mean()} currency units")
# Show first few rows of the dataframe
st.subheader("Sample Data")
st.dataframe(df_all.head(20))
# Show histogram of trip distances
st.subheader("Trip Distance Distribution")
fig, ax = plt.subplots()
ax.hist(df_all['distance'], bins=30, color='skyblue', edgecolor='black')
ax.set_xlabel("Distance (meters)")
ax.set_ylabel("Number of Trips")
st.pyplot(fig)
# Show histogram of trip prices
st.subheader("Trip Price Distribution")
fig, ax = plt.subplots()
ax.hist(df_all['price'], bins=30, color='lightgreen', edgecolor='black')
ax.set_xlabel("Price (currency units)")
ax.set_ylabel("Number of Trips")
st.pyplot(fig)
# Show scatter plot of distance vs price
st.subheader("Distance vs Price")
fig, ax = plt.subplots()
ax.scatter(df_all['distance'], df_all['price'], alpha=0.5)
ax.set_xlabel("Distance (meters)")
ax.set_ylabel("Price (currency units)")
st.pyplot(fig)
# Show average price per distance bucket
st.subheader("Average Price per Distance Bucket")
df_all['distance_bucket'] = pd.cut(df_all['distance'], bins=range(0, int(df_all['distance'].max()) + 500, 500))
avg_price_per_bucket = df_all.groupby('distance_bucket')['price'].mean().reset_index()
fig, ax = plt.subplots()
ax.bar(avg_price_per_bucket['distance_bucket'].astype(str), avg_price_per_bucket['price'], color='salmon', edgecolor='black')
ax.set_xlabel("Distance Bucket (meters)")
ax.set_ylabel("Average Price (currency units)")
plt.xticks(rotation=45)
st.pyplot(fig)
# histogram of tick
st.subheader("Trips per time tick")
fig, ax = plt.subplots()
ax.hist(df_all['tick'], bins=30, color='violet', edgecolor='black')
ax.set_xlabel("Tick")
ax.set_ylabel("Number of Trips")
st.pyplot(fig)