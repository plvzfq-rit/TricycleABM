# import streamlit as st
import pandas as pd
import os

LOG_DIRECTORY = r"logs"

df_all = pd.DataFrame()

# Go through every folder
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

# st.title("My First Streamlit App")
# st.write("Hello, Streamlit!")