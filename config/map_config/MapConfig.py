class MapConfig:
    hubDistribution = dict()
    numberOfTricycles = 0

    # Hub Distribution is a dictionary(hub_name: str -> number_of_tricycles_at_hub: int)
    def __init__(self, hub_distribution: dict=dict()) -> None:
        self.hubDistribution = hub_distribution
        self.numberOfTricycles = 0
        for number_of_tricycles_in_hub in hub_distribution.values():
            self.numberOfTricycles += number_of_tricycles_in_hub

    def getHubDistribution(self) -> dict:
        return self.hubDistribution
    
    def getNumberOfTricycles(self) -> int:
        return self.numberOfTricycles
    
    def addHub(self, hub_id: str, number_of_tricycles: int) -> None:
        if not hub_id.strip():
            raise Exception("Invalid hub id. Was empty.")
        if number_of_tricycles <= 0:
            raise Exception(f"Invalid number of tricycles. Was: {number_of_tricycles}")
        self.hubDistribution[hub_id] = number_of_tricycles
        self.numberOfTricycles += number_of_tricycles