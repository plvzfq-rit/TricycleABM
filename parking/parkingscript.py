"""Utility script for generating SUMO flow XML from parking demand data.

Reads parking/demand data from demand.csv and generates SUMO-compatible route
flow definitions based on hourly demand patterns. The csv file uses the current
routes located in maps/routes.xml, as such running this script overwrites
the existing traffic flow that is in the SUMO file.
"""

import pandas as pd

# Load CSV
df = pd.read_csv("./parking/demand.csv", index_col=0)


def hour_to_seconds(hour_index: int) -> tuple[int, int]:
    """Convert hour index to simulation time range in seconds.
    
    :param hour_index: Hour index (0-23).
    :type hour_index: int
    :return: Tuple of (begin_seconds, end_seconds).
    :rtype: tuple[int, int]
    """
    begin = hour_index * 60
    end = (hour_index + 1) * 60
    return begin, end


# Generate XML flows, Each row = road, Each column = hour slot
flow_list = []

for road, row in df.iterrows():
    for i, flow in enumerate(row):
        begin, end = hour_to_seconds(i)   # because first column is "6–7"
        flow = int(flow)

        # Skip zero-flows
        if flow == 0:
            continue

        
        flow_list.append({
            "begin": begin,
            "xml": f'<flow id="{road}_{begin}" route="{road}" begin="{begin}" end="{end}" vehsPerHour="{int(flow)}"/>'
        })

# Sort by departure time
flow_list = sorted(flow_list, key=lambda x: x["begin"])

# Write XML
file_path = "../maps/routes.xml"

with open(file_path, "r") as f:
    lines = f.readlines()

with open(file_path, "w") as f:
    f.writelines(lines[:82])

with open(file_path, "a") as f:
    for ftag in flow_list:
        f.write(ftag["xml"] + "\n")

print("Generated sorted_flows.xml (flows sorted by departure time).")