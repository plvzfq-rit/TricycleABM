from pathlib import Path
from scipy.stats import lognorm

import random
import numpy as np

class SimulationConfig:
    assetDirectoryName = "maps"
    networkFileName = "net.net.xml"
    parkingFileName = "parking.add.xml"
    decalFileName = "map.xml"
    routesFileName = "routes.xml"
    gasPricePerLiter = 58.9
    
    def getAssetDirectory(self) -> str:
        script_dir = Path(__file__).resolve().parent.parent
        assets_dir = script_dir / self.assetDirectoryName
        return assets_dir
    
    def getNetworkFilePath(self) -> str:
        return str(self.getAssetDirectory() / self.networkFileName)
    
    def getParkingFilePath(self) -> str:
        return str(self.getAssetDirectory() / self.parkingFileName)
    
    def getDecalFilePath(self) -> str:
        return str(self.getAssetDirectory() / self.decalFileName)
    
    def getRoutesFilePath(self) -> str:
        return str(self.getAssetDirectory() / self.routesFileName)
    
    def getGasPricePerLiter(self) -> float:
        return float(self.gasPricePerLiter)
    
    def getWTPDistribution(self) -> callable:
        shape = 0.7134231299166108
        scale = 38.38513260285555
        return lambda size=1: lognorm.rvs(shape, loc=0, scale=scale, size=size)
    
    def getTodaPositions(self) -> dict[str, float]:
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
        return [0.08284023669, 0.1301775148, 0.1538461538, 0.1301775148, 0.08284023669, 0.07100591716, 0.04733727811, 0.0650887574, 0.03550295858, 0.02366863905, 0.02366863905, 0.04142011834, 0.02366863905, 0.01183431953, 0.005917159763, 0.005917159763, 0.005917159763, 0.005917159763]

    def getStartTimeDistribution(self) -> callable:
        shape = 0.21442788235989804
        scale = 6.471010297664735
        MINUTES_OVER_HOURS = 60
        SECONDS_OVER_MINUTES = 60
        MULTIPLICATIVE_CONSTANT = MINUTES_OVER_HOURS * SECONDS_OVER_MINUTES
        START_TIME = 6 #AM
        NORMALIZING_CONSTANT = 6 * MULTIPLICATIVE_CONSTANT
        return lambda size=1: max(0, \
            MULTIPLICATIVE_CONSTANT * 
            lognorm.rvs(shape, loc=0, scale=scale, size=size) - 
            NORMALIZING_CONSTANT)
    
    def getEndTimeDistribution(self) -> callable:
        shape = 0.4675881648065253
        scale = 4.4056405084474735
        MINUTES_OVER_HOURS = 60
        SECONDS_OVER_MINUTES = 60
        MULTIPLICATIVE_CONSTANT = MINUTES_OVER_HOURS * SECONDS_OVER_MINUTES
        MAX_END_TIME = 64800 # 12AM in seconds
        SET_END_TIME = 23 * 60 * 60 - 1 # 11:59:59PM in seconds
        return lambda size=1: min(SET_END_TIME, \
            MAX_END_TIME - MULTIPLICATIVE_CONSTANT * 
            lognorm.rvs(shape, loc=0, scale=scale, size=size))
    
    def getMaxGasDistribution(self) -> callable:
        import numpy as np
        import scipy.stats as stats
        unique_max_gas = [ 8.        ,  8.6       ,  9.5       ,  9.64      ,  9.70294118,10.        , 10.2       , 10.5       , 10.75      , 12.        ]
        prob_max_gas = [0.05405405, 0.21621622, 0.05405405, 0.27027027, 0.08108108, 0.08108108, 0.02702703, 0.02702703, 0.10810811, 0.08108108]
        return lambda size=1: (np.random.choice(unique_max_gas, size=size, p=prob_max_gas) + np.random.normal(0, 0.1, size=1)).item()
    
    def getGasConsumptionDistribution(self) -> callable:
        import numpy as np
        import scipy.stats as stats
        unique_gas_consumption = [33.        , 40.        , 40.25      , 46.21764706, 48.        , 61.4       , 62.5       ]
        prob_gas_consumption = [0.02702703, 0.48648649, 0.10810811, 0.08108108, 0.05405405, 0.02702703, 0.21621622]
        return lambda size=1: (np.random.choice(unique_gas_consumption, size=size, p=prob_gas_consumption) + np.random.normal(0, 0.1, size=1)).item()
    
    def getGasPaymentDistribution(self) -> callable:
        import numpy as np
        import scipy.stats as stats
        unique_gas_payment = [ 50., 100., 110., 120., 125., 150., 200., 300.]
        prob_gas_payment = [0.02702703, 0.21621622, 0.02702703, 0.05405405, 0.02702703, 0.32432432, 0.2972973 , 0.02702703]
        return lambda size=1: (np.random.choice(unique_gas_payment, size=size, p=prob_gas_payment)).item()
    
    def getGetsFullTankDistribution(self) -> callable:
        import numpy as np
        w_af = [27/37, 1 - 27/37]
        return lambda size=1: np.random.choice([False, True], size=size, p=w_af).item()
    
    def getDailyExpenseDistribution(self) -> callable:
        shape = 0.5551170551235295
        scale = 375.96181139256873
        return lambda size=1: lognorm.rvs(shape, loc=0, scale=scale, size=size)

    def getFarthestDistanceDistribution(self) -> callable:
        shape = 0.4562970511172417
        scale = 4.119316604349962
        MULTIPLICATIVE_CONSTANT = 1000
        return lambda size=1: lognorm.rvs(shape, loc=0, scale=scale, size=size) * MULTIPLICATIVE_CONSTANT
    
    def getProfitDistribution(self) -> callable:
        prob_zero = 24/37
        return lambda size=1: 0 if random.random() < 24/37 else np.random.choice([30,10,50,-20,-50,20], size=size, p=[2/13,2/13,3/13,2/13,1/13,3/13])[0]

    def getTricyclePatienceDistribution(self) -> callable:
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
        return lambda size=1: np.random.choice([50, 70, 100, 60], size=size, p=[37/54, 9/54, 7/54, 1/54])[0]

    def getPassengerAspiredPriceDistribution(self) -> callable:
        
        return lambda size=1: lognorm.rvs(0.7234913879629307, loc=0, scale=36.844797800005615, size=size)[0]