import random
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

        start_times = np.array([6, 7, 8, 9, 10])
        start_times_probs = np.array([18/31, 5/31, 5/31, 2/31, 1/31])
        start_time_seed = np.random.choice(start_times, p=start_times_probs)
        start_time = np.random.uniform(low=start_time_seed * 60 - 6 * 60, high=(start_time_seed + 1) * 60 - 6 * 60)

        end_times = np.array(list(range(14, 22)))
        end_times_probs = np.array([1/31, 2/31, 1/31, 4/31, 2/31, 4/31, 7/31, 10/31])
        end_time_seed = np.random.choice(end_times, p=end_times_probs)
        end_time = np.random.uniform(low=end_time_seed * 60 - 6 * 60, high=(end_time_seed + 1) * 60 - 6 * 60)

        max_gas = stats.gamma.rvs(4.310842116036499  , loc=7.546639006032087  , scale=0.5024555276240792)[0]

        # in km/L
        w_gc=[0.2580645161290322,0.12903225806451613,0.03225806451612909,0.03225806451612909,0.03225806451612909,0.03225806451612909,0.48387096774193533]
        mu_gc=[62.36249999999998,40.33333332999998,46.2494252899999,32.99999999999993,47.99999999999989,44.297338169999904,39.99999999999999]
        sigma_gc=[0.36379217968505084,0.001,0.001,0.001,0.001,0.001,0.001]
        index = np.random.choice(list(range(5)), p=w_gc)
        gas_consumption = np.random.normal(mu_gc[index], sigma_gc[index])

        gas_threshold = 0

        w_gp=[0.3225806451612903,0.19354823351376013,0.32258064515495616,0.032258064516129094,0.032258064516129094,0.09677434713773515]
        mu_gp=[199.99999999999997,99.99999999999994,149.99999999999997,299.9999999999993,49.999999999999886,117.99997143569914]
        sigma_gp=[0.001,0.001,0.001,0.001,0.001,5.887879661555394]
        index = np.random.choice(list(range(5)), p=w_gp)
        usual_gas_payment = np.random.normal(mu_gp[index], sigma_gp[index])

        w_af = [0.6774193548, 1 - 0.6774193548]
        index = np.random.choice(list(range(2)), p=w_af)
        gets_full_tank = False
        if index == 1:
            gets_full_tank = True

        w_e=[0.037037037037037035,0.2592592593675214,0.07407410700127677,0.296296296188034,0.11111111110006881,0.22222218930606197]
        mu_e=[399.99999999999915,176.32653066592968,574.9999666910353,299.9999999999999,699.9999999999995,499.9999999999999]
        sigma_e=[0.001,25.85964758770186,25.00004450145673,0.001,0.001,0.001]
        index = np.random.choice(list(range(5)), p=w_e)
        daily_expense = np.random.normal(mu_e[index], sigma_e[index])

        w_d=[0.3225806451612903,0.19354823351376013,0.32258064515495616,0.032258064516129094,0.032258064516129094,0.09677434713773515]
        mu_d=[199.99999999999997,99.99999999999994,149.99999999999997,299.9999999999993,49.999999999999886,117.99997143569914]
        sigma_d=[0.001,0.001,0.001,0.001,0.001,5.887879661555394]
        index = np.random.choice(list(range(5)), p=w_d)
        farthest_distance = np.random.normal(mu_d[index], sigma_d[index])

        return (trike_name, Tricycle(trike_name, assigned_hub, start_time, end_time, max_gas, gas_consumption, gas_threshold, usual_gas_payment, gets_full_tank, farthest_distance, daily_expense))