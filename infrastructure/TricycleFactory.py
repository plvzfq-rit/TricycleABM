import random
import math
import numpy as np
import scipy.stats as stats
from domain.Tricycle import Tricycle

class TricycleFactory:
    def __init__(self, simulation_config):
        self.getStartTime = simulation_config.getStartTimeDistribution()
        self.getEndTime = simulation_config.getEndTimeDistribution()
        self.getMaxGas = simulation_config.getMaxGasDistribution()
        self.getGasConsumption = simulation_config.getGasConsumptionDistribution()
        self.getGasPayment = simulation_config.getGasPaymentDistribution()
        self.getGetsFullTank = simulation_config.getGetsFullTankDistribution()
        self.getDailyExpense = simulation_config.getDailyExpenseDistribution()
        self.getFarthestDistance = simulation_config.getFarthestDistanceDistribution()
        self.getPatience = simulation_config.getTricyclePatienceDistribution()
        self.getAspiredPrice = simulation_config.getTricycleAspiredPriceDistribution()
    def createRandomTricycle(self, assigned_id: int, assigned_hub: str) -> tuple[str, Tricycle]:
        trike_name = "trike" + str(assigned_id)
        start_time = self.getStartTime()
        end_time = 0
        while end_time <= start_time:
            end_time = self.getEndTime()
        max_gas = self.getMaxGas()
        gas_consumption = self.getGasConsumption()
        gas_threshold = 0
        usual_gas_payment = self.getGasPayment()
        gets_full_tank = self.getGetsFullTank()
        daily_expense = self.getDailyExpense()
        farthest_distance = self.getFarthestDistance()
        patience = self.getPatience()
        aspired_price = self.getAspiredPrice()
        return (trike_name, Tricycle(trike_name, assigned_hub, start_time, end_time, max_gas, gas_consumption, gas_threshold, usual_gas_payment, gets_full_tank, farthest_distance, daily_expense, patience, aspired_price))
