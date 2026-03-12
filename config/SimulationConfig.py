"""Module containing simulation configuration and probability distributions.

This module provides the SimulationConfig class which centralizes all simulation
parameters, asset paths, and statistical distributions used to generate random
variables for tricycle drivers, passengers, and operational parameters.
"""

import math
from pathlib import Path
from scipy.stats import lognorm

import random
import numpy as np


class SimulationConfig:
    """Centralized configuration for the ABMS (Agent-Based Mobility Simulation).
    
    Manages all configurable parameters including asset paths, pricing matrices,
    gas prices, and probability distributions for generating realistic tricycle
    and passenger behaviors.
    
    :ivar assetDirectoryName: Name of directory containing asset files.
    :ivar networkFileName: SUMO network file name.
    :ivar parkingFileName: Parking areas file name.
    :ivar decalFileName: Map decal file name.
    :ivar routesFileName: Routes file name.
    :ivar gasPrices: Dictionary of gas price scenarios.
    :ivar GAS_CONSUMPTION_FROM_PAPER: Gas consumption rate from literature.
    :ivar demandMultiplier: Multiplier for demand probabilities.
    """
    assetDirectoryName = "maps"
    networkFileName = "net.net.xml"
    parkingFileName = "parking.add.xml"
    decalFileName = "map.xml"
    routesFileName = "routes.xml"
    gasPrices = {
        "DEFAULT": 58.9,
        "LOW": 54.8,
        "HIGH": 61.0
    }
    gasPricePerLiter = gasPrices["DEFAULT"]
    GAS_CONSUMPTION_FROM_PAPER = 24.41
    demandMultiplier = 2.0

    def __init__(self, gas_price_select: str, base_price: float, base_distance: float, 
                 added_price: float, added_distance: float) -> None:
        """Initialize simulation configuration with pricing parameters.
        
        :param gas_price_select: Gas price scenario ("DEFAULT", "LOW", or "HIGH").
        :type gas_price_select: str
        :param base_price: Base fare price in pesos.
        :type base_price: float
        :param base_distance: Base distance in meters.
        :type base_distance: float
        :param added_price: Additional price per increment.
        :type added_price: float
        :param added_distance: Distance increment in meters.
        :type added_distance: float
        """
        self.basePrice = base_price
        self.baseDistance = base_distance
        self.addedPrice = added_price
        self.addedDistance = added_distance
        self.matrix = lambda x: base_price if x <= base_distance else base_price + added_price * math.ceil((x-1000)/1000)
        self.gasPricePerLiter = self.gasPrices[gas_price_select]

    def getAssetDirectory(self) -> str:
        """Get the path to the assets directory.
        
        :return: Path object pointing to the assets directory.
        :rtype: str
        """
        script_dir = Path(__file__).resolve().parent.parent
        assets_dir = script_dir / self.assetDirectoryName
        return assets_dir
    
    def getNetworkFilePath(self) -> str:
        """Get the full path to the SUMO network file.
        
        :return: String path to the network XML file.
        :rtype: str
        """
        return str(self.getAssetDirectory() / self.networkFileName)
    
    def getParkingFilePath(self) -> str:
        """Get the full path to the parking areas file.
        
        :return: String path to the parking XML file.
        :rtype: str
        """
        return str(self.getAssetDirectory() / self.parkingFileName)
    
    def getDecalFilePath(self) -> str:
        """Get the full path to the map decal file.
        
        :return: String path to the map XML file.
        :rtype: str
        """
        return str(self.getAssetDirectory() / self.decalFileName)
    
    def getRoutesFilePath(self) -> str:
        """Get the full path to the routes file.
        
        :return: String path to the routes XML file.
        :rtype: str
        """
        return str(self.getAssetDirectory() / self.routesFileName)
    
    def getGasPricePerLiter(self) -> float:
        """Get the current gas price per liter.
        
        :return: Gas price in pesos per liter as a float.
        :rtype: float
        """
        return float(self.gasPricePerLiter)
    
    def getGasConsumption(self) -> float:
        """Get the gas consumption rate.
        
        :return: Gas consumption rate from literature as a float.
        :rtype: float
        """
        return float(self.GAS_CONSUMPTION_FROM_PAPER)
    
    def getWTPDistribution(self) -> callable:
        """Get a callable for generating passenger willingness-to-pay values.
        
        :return: Function that generates WTP values following a lognormal distribution.
        :rtype: callable
        """
        shape = 0.7134231299166108
        scale = 38.38513260285555
        return lambda size=1: round(lognorm.rvs(shape, loc=0, scale=scale, size=size).item(), 2)
    
    def getTodaPositions(self) -> dict[str, float]:
        """Get the positions of all TODA hubs in the network.
        
        :return: Dictionary mapping hub IDs to their positions.
        :rtype: dict[str, float]
        """
        return {
            "hub0": 6.12,
            "hub1": 16.48,
            "hub2": 7.72,
            "hub3": 20.44,
            "hub4": 508.38,
            "hub5": 73.76,
            "hub6": 40.82,
            "hub7": 75.65,
            "hub8": 57.71
        }

    def getPeakHourProbabilities(self) -> list[float]:
        """Get hourly demand probabilities (scalable) for the entire day.
        
        :return: List of probabilities (24 probabilities, one per hour).
        :rtype: list[float]
        """
        base = [0.08284023669, 0.1301775148, 0.1538461538, 0.1301775148, 0.08284023669, 0.07100591716, 0.04733727811, 0.0650887574, 0.03550295858, 0.02366863905, 0.02366863905, 0.04142011834, 0.02366863905, 0.01183431953, 0.005917159763, 0.005917159763, 0.005917159763, 0.005917159763]
        return [p * self.demandMultiplier for p in base]

    def getStartTimeDistribution(self) -> callable:
        """Get a callable for generating tricycle start times.
        
        :return: Function that generates start times in seconds following a lognormal.
        :rtype: callable
        """
        shape = 0.21442788235989804
        scale = 6.471010297664735
        MINUTES_OVER_HOURS = 60
        SECONDS_OVER_MINUTES = 60
        MULTIPLICATIVE_CONSTANT = MINUTES_OVER_HOURS * SECONDS_OVER_MINUTES
        NORMALIZING_CONSTANT = 6 * MULTIPLICATIVE_CONSTANT
        return lambda size=1: math.floor(max(0, \
            MULTIPLICATIVE_CONSTANT *
            lognorm.rvs(shape, loc=0, scale=scale, size=size).item() -
            NORMALIZING_CONSTANT))
    
    def getEndTimeDistribution(self) -> callable:
        """Get a callable for generating tricycle end times.
        
        :return: Function that generates end times in seconds following a lognormal.
        :rtype: callable
        """
        shape = 0.4675881648065253
        scale = 4.4056405084474735
        MINUTES_OVER_HOURS = 60
        SECONDS_OVER_MINUTES = 60
        MULTIPLICATIVE_CONSTANT = MINUTES_OVER_HOURS * SECONDS_OVER_MINUTES
        MAX_END_TIME = 64800 # 12AM in seconds
        SET_END_TIME = 23 * 60 * 60 - 1 # 11:59:59PM in seconds
        return lambda size=1: math.floor(min(SET_END_TIME, \
            MAX_END_TIME - MULTIPLICATIVE_CONSTANT *
            lognorm.rvs(shape, loc=0, scale=scale, size=size).item()))
    
    def getMaxGasDistribution(self) -> callable:
        import numpy as np
        """Get a callable for generating maximum gas tank capacity.
        
        :return: Function that generates tank capacity in liters.
        :rtype: callable
        """
        unique_max_gas = [ 8.        ,  8.6       ,  9.5       ,  9.64      ,  9.70294118,10.        , 10.2       , 10.5       , 10.75      , 12.        ]
        prob_max_gas = [0.05405405, 0.21621622, 0.05405405, 0.27027027, 0.08108108, 0.08108108, 0.02702703, 0.02702703, 0.10810811, 0.08108108]
        return lambda size=1: (np.random.choice(unique_max_gas, size=size, p=prob_max_gas) + np.random.normal(0, 0.1, size=1)).item()
    
    def getGasPaymentDistribution(self) -> callable:
        import numpy as np
        """Get a callable for generating gas payment amounts.
        
        :return: Function that generates gas payment values in pesos.
        :rtype: callable
        """
        unique_gas_payment = [ 50., 100., 110., 120., 125., 150., 200., 300.]
        prob_gas_payment = [0.02702703, 0.21621622, 0.02702703, 0.05405405, 0.02702703, 0.32432432, 0.2972973 , 0.02702703]
        return lambda size=1: (np.random.choice(unique_gas_payment, size=size, p=prob_gas_payment)).item()
    
    def getGetsFullTankDistribution(self) -> callable:
        import numpy as np
        """Get a callable for deciding if tricycle gets full tank.
        
        :return: Function that returns True/False whether driver fuels completely.
        :rtype: callable
        """
        w_af = [27/37, 1 - 27/37]
        return lambda size=1: np.random.choice([False, True], size=size, p=w_af).item()
    
    def getDailyExpenseDistribution(self) -> callable:
        """Get a callable for generating daily operational expenses.
        
        :return: Function that generates daily expense values in pesos.
        :rtype: callable
        """
        shape = 0.5551170551235295
        scale = 375.96181139256873
        return lambda size=1: round(lognorm.rvs(shape, loc=0, scale=scale, size=size).item(), 2)

    def getFarthestDistanceDistribution(self) -> callable:
        """Get a callable for generating maximum trip distance preference.
        
        :return: Function that generates distance in meters.
        :rtype: callable
        """
        shape = 0.4562970511172417
        scale = 4.119316604349962
        MULTIPLICATIVE_CONSTANT = 1000
        return lambda size=1: lognorm.rvs(shape, loc=0, scale=scale, size=size).item() * MULTIPLICATIVE_CONSTANT
    
    def getTricyclePatienceDistribution(self) -> callable:
        """Get a callable for generating tricycle driver patience levels.
        
        :return: Function that generates patience values between 0 and 1.
        :rtype: callable
        """
        def patience_distribution(size=1):
            draw = random.random()
            if draw < 17/28:
                return random.uniform(0, 1/3)
            elif draw < 26/28:  # 17/28 + 9/28
                return random.uniform(1/3, 2/3)
            else:
                return random.uniform(2/3, 1)
        return patience_distribution
    
    def getPassengerPatienceDistribution(self) -> callable:
        """Get a callable for generating passenger patience levels.
        
        :return: Function that generates patience values between 0 and 1.
        :rtype: callable
        """
        def patience_distribution(size=1):
            draw = random.random()
            if draw < 16/28:
                return random.uniform(0, 1/4)
            elif draw < 22/28:  # 16/28 + 6/28
                return random.uniform(1/4, 1/2)
            elif draw < 27/28:  # 16/28 + 6/28 + 5/28
                return random.uniform(1/2, 3/4)
            else:
                return random.uniform(3/4, 1)
        return patience_distribution

    def getTricycleAspiredPriceDistribution(self) -> callable:
        """Get a callable for generating tricycle driver aspired prices.
        
        :return: Function that generates aspired price values in pesos.
        :rtype: callable
        """
        return lambda size=1: round(np.random.choice([50, 70, 100, 60], size=size, p=[24/37, 6/37, 6/37, 1/37])[0], 2)

    def getPassengerAspiredPriceDistribution(self) -> callable:
        """Get a callable for generating passenger aspired prices.
        
        :return:
            Function that generates aspired price values in pesos.
        """
        return lambda size=1: round(lognorm.rvs(0.7234913879629307, loc=0, scale=36.844797800005615, size=size)[0], 2)
    
    def getMinimumPriceDistribution(self) -> callable:
        """Get a callable for generating driver minimum price thresholds.
        
        :return: Function that generates minimum price values in pesos.
        :rtype: callable
        """
        return lambda size=1: round(np.random.choice([50,40,70,100,80], size=size, p=[27/36,3/36, 4/36, 1/36, 1/36])[0], 2)
