"""Module for creating tricycle instances with random parameters.

Provides the TricycleFactory class which generates Tricycle objects
with randomized operational and financial parameters according to
probability distributions defined in SimulationConfig.
"""

import random
import math
import numpy as np
from domain.Tricycle import Tricycle


class TricycleFactory:
    """Factory for creating Tricycle objects with randomized parameters.
    
    Generates tricycles with randomly generated operational characteristics 
    using probability distributions from SimulationConfig.
    
    :ivar getStartTime: Callable for generating start times.
    :ivar getEndTime: Callable for generating end times.
    :ivar getMaxGas: Callable for generating max gas capacity.
    :ivar getGasPayment: Callable for generating gas payment amounts.
    :ivar getGetsFullTank: Callable for deciding if driver gets full tank.
    :ivar getDailyExpense: Callable for generating daily expenses.
    :ivar getFarthestDistance: Callable for generating max distance preference.
    :ivar getPatience: Callable for generating driver patience.
    :ivar getAspiredPrice: Callable for generating aspired prices.
    :ivar getMinimumPrice: Callable for generating minimum prices.
    :ivar gasConsumption: Gas consumption rate.
    """
    
    def __init__(self, simulation_config) -> None:
        """Initialize TricycleFactory with distributions from simulation config.
        
        :param simulation_config: SimulationConfig object containing distributions.
        :type simulation_config: SimulationConfig
        """
        self.getStartTime = simulation_config.getStartTimeDistribution()
        self.getEndTime = simulation_config.getEndTimeDistribution()
        self.getMaxGas = simulation_config.getMaxGasDistribution()
        self.getGasPayment = simulation_config.getGasPaymentDistribution()
        self.getGetsFullTank = simulation_config.getGetsFullTankDistribution()
        self.getDailyExpense = simulation_config.getDailyExpenseDistribution()
        self.getFarthestDistance = simulation_config.getFarthestDistanceDistribution()
        self.getPatience = simulation_config.getTricyclePatienceDistribution()
        self.getAspiredPrice = simulation_config.getTricycleAspiredPriceDistribution()
        self.getMinimumPrice = simulation_config.getMinimumPriceDistribution()
        self.gasConsumption = simulation_config.getGasConsumption()
    
    def createRandomTricycle(self, assigned_id: int, assigned_hub: str) -> tuple[str, Tricycle]:
        """Create a tricycle with random operational parameters.
        
        Generates a new Tricycle object with randomized characteristics 
        with the configured probability distributions (from SimulationConfig).
        Called from TricycleRepository.createTricycles() (which contain tricycle
        count and hub distribution)
        
        :param assigned_id: Assigned ID of tricycle.
        :type assigned_id: int
        :param assigned_hub: Assigned TODA Hub of Tricycle.
        :type assigned_hub: str
        :return: Tuple of (tricycle_name, Tricycle object).
        :rtype: tuple[str, Tricycle]
        """
        trike_name = "trike" + str(assigned_id)
        start_time = self.getStartTime()
        end_time = 0
        while end_time <= start_time:
            end_time = self.getEndTime()
        max_gas = self.getMaxGas()
        gas_consumption = self.gasConsumption
        usual_gas_payment = self.getGasPayment()
        gets_full_tank = self.getGetsFullTank()
        daily_expense = self.getDailyExpense()
        farthest_distance = self.getFarthestDistance()
        patience = self.getPatience()
        aspired_price = self.getAspiredPrice()
        minimum_price = self.getMinimumPrice()
        return (trike_name, Tricycle(trike_name, assigned_hub, start_time, end_time, max_gas, 
                                     gas_consumption, usual_gas_payment, gets_full_tank, 
                                     farthest_distance, daily_expense, patience, aspired_price, 
                                     minimum_price))
