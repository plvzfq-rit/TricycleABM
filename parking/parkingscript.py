import pandas as pd

# --------------------------------------------------------
# 1. Load CSV (no header in first column, so index_col=0)
# --------------------------------------------------------
df = pd.read_csv("./parking/Book1.csv", index_col=0)

# --------------------------------------------------------
# 2. Convert hour labels to begin/end seconds
# --------------------------------------------------------
def hour_to_seconds(hour_index):
    begin = hour_index * 60
    end = (hour_index + 1) * 60
    return begin, end

# --------------------------------------------------------
# 3. Generate XML flows
#    Each row = road
#    Each column = hour slot
# --------------------------------------------------------
flow_list = []

for road, row in df.iterrows():
    for i, flow in enumerate(row):
        begin, end = hour_to_seconds(i)   # because your first column is "6–7"
        flow = int(flow)

        # Skip zero-flows
        if flow == 0:
            continue

        
        flow_list.append({
            "begin": begin,
            "xml": f'<flow id="{road}_{begin}" route="{road}" begin="{begin}" end="{end}" vehsPerHour="{int(flow)}"/>'
        })

# ------------------------------
# Sort by departure time
# ------------------------------
flow_list = sorted(flow_list, key=lambda x: x["begin"])

for i in flow_list:
    print(i['xml'])

# ------------------------------
# Write XML
# ------------------------------
# with open("script/sorted_flows.xml", "w") as f:
#     for ftag in flow_list:
#         f.write(ftag["xml"] + "\n")

# print("Generated sorted_flows.xml (flows sorted by departure time).")