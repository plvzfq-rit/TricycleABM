import random
import math
import numpy as np
import scipy.stats as stats
from domain.Tricycle import Tricycle

class TricycleFactory:
    lowerGasBound = 50.0
    upperGasBound = 52.0

    def __init__(self, lower_gas_bound: float = 50.0, upper_gas_bound: float = 52.0):
        self.lowerGasBound = lower_gas_bound
        self.upperGasBound = upper_gas_bound

    def createRandomTricycle(self, assigned_id: int, simulation_duration: int, assigned_hub: str) -> tuple[str, Tricycle]:
        trike_name = "trike" + str(assigned_id)

        start_time = max(0,math.floor(60 * stats.lognorm.rvs(0.19840374997921292, loc=0, scale=6.520004321549422, size=1)))
        # start_time = 0

        end_time = min(1080, math.floor(60 * (24 - stats.lognorm.rvs(0.46084412009093767, loc=0, scale=4.207763166353462, size=1))))

        unique_max_gas = [ 8.        ,  8.6       ,  9.5       ,  9.64      ,  9.70294118,10.        , 10.2       , 10.5       , 10.75      , 12.        ]
        prob_max_gas = [0.05405405, 0.21621622, 0.05405405, 0.27027027, 0.08108108, 0.08108108, 0.02702703, 0.02702703, 0.10810811, 0.08108108]
        max_gas = (np.random.choice(unique_max_gas, size=1, p=prob_max_gas) + np.random.normal(0, 0.1, size=1)).item()

        # in km/L
        unique_gas_consumption = [33.        , 40.        , 40.25      , 46.21764706, 48.        , 61.4       , 62.5       ]
        prob_gas_consumption = [0.02702703, 0.48648649, 0.10810811, 0.08108108, 0.05405405, 0.02702703, 0.21621622]
        gas_consumption = (np.random.choice(unique_gas_consumption, size=1, p=prob_gas_consumption) + np.random.normal(0, 0.1, size=1)).item()

        gas_threshold = 0

        unique_gas_payment = [ 50., 100., 110., 120., 125., 150., 200., 300.]
        prob_gas_payment = [0.02702703, 0.21621622, 0.02702703, 0.05405405, 0.02702703, 0.32432432, 0.2972973 , 0.02702703]
        usual_gas_payment = (np.random.choice(unique_gas_payment, size=1, p=prob_gas_payment)).item()

        w_af = [27/37, 1 - 27/37]
        index = np.random.choice(list(range(2)), p=w_af).item()
        gets_full_tank = False
        if index == 1:
            gets_full_tank = True

        daily_expense = stats.lognorm.rvs(0.5551170551235295, loc=0, scale=375.96181139256873, size=1)

        farthest_distance = stats.lognorm.rvs(0.4562970511172417, loc=0, scale=4.119316604349962, size=1) * 1000

        return (trike_name, Tricycle(trike_name, assigned_hub, start_time, end_time, max_gas, gas_consumption, gas_threshold, usual_gas_payment, gets_full_tank, farthest_distance, daily_expense))