# A FairFare Program

---

## Overview

This repository contains the command-line traffic simulation program and analysis dashboard used for the study **A Fair Fare? An Agent-Based Model of Tricycle Fare Sustainability in Manila**.

The application uses the SUMO software by interfacing with Python libraries for operation and analysis. The goal is to create a springboard for analysts, traffic engineers, and policymakers to infer traffic policy changes, particularly on tricycle fare matrices.

FairFare is able to:

- Simulate tricycle behaviors in a day, including:
  - Waiting in TODA queues
  - Passenger haggling
  - Realistic driving (using SUMO)
  - Calculating daily expenses
- Realistically simulate traffic in the City of Manila and show how this affects tricycle drivers
- Export simulation data to `.csv` format
- Integrate results into a data analysis dashboard, including:
  - Daily stats
  - Important macro and microeconomic indicators

---

## Environment Setup

### Software Prerequisites

- Source Code Repository
- Python 3.13 or above

### External Python Packages

Install using `pip`:

- traci
- eclipse-sumo
- numpy
- pandas
- scipy
- sumolib

---

## Installation

1. Download and install the repository and software prerequisites using their respective links.
2. If using Windows, add Python and SUMO directories to the `PATH`.
3. Install required external libraries:

```bash
pip install traci eclipse-sumo numpy pandas scipy sumolib
```

## Usage

To run a simulation scenario, execute the following command in the project directory:

```bash
py main.py --base_price <base_price> --base_distance <base_distance> --added_price <added_price> --added_distance <added_distance>
```

### Flags

| Flag               | Description                                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------------- |
| `--base_price`     | Integer representing the base price for any distance equal to or below the base distance.               |
| `--base_distance`  | Integer representing the base distance.                                                                 |
| `--added_price`    | Integer representing the added price for every distance (or fraction thereof) beyond the base distance. |
| `--added_distance` | Integer representing the distance interval for each added price beyond the base distance.               |
<!-- | `--gas_price`      | String enum representing the gas price used in the model: `"DEFAULT"`, `"LOW"`, or `"HIGH"`.            | -->

By default, the system runs 30 simulation runs. This can be modified in: `main.py`

## Post-Usage Analysis

After execution, run results are saved in the `analysis/` folder.

Folder format: `<base_price>_<base_distance>_<added_price>_<added_distance>`
 
Go to `/analysis` then run the analysis dashboard using:

```bash
streamlit run analysis.py
```

## Making Changes

For more information, the repository code uses Sphinx for documentation. Compile and read using:

```bash
cd docs
./make html
```

Then open `build/html/index.html`.

## Project File Structure Overview

```
TricycleABM/
│
├── analysis/               # Scenario logs save folder and streamlit analysis dashboard
├── application/            # Interaction SDK assets
│   ├── SimulationEngine.py # Meta XR integration assets
├── config/                 # Interaction SDK assets
│   ├── SimulationConfig.py # Configuration (gas prices, behavior distributions)
├── domain/                 # Program domain for simulation
├── infrastructure/         # Program simulation classes
├── maps/                   # SUMO Simulation Files
│   ├── net.net.xml         # SUMO map file (use netedit for editing)
│   ├── parking.add.xml     # SUMO parking file
│   ├── routes.xml          # SUMO routes file (change using sheet and script in parking/)
├── parking/                # External script for generating parking flow
├── sphinx/                 # Docs
├── utils/                  # SUMO utils
└── main.py
```

## Team

- Reyes, Ma. Julianna Re-an D.
- Ruiz, James Christian T.
- Soriano, John Angelo S.
- Yap, Jan Benjamin C.

## Adviser

- Dr. Briane Paul V. Samson
