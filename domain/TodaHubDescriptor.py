"""Module for managing TODA hub configurations in the simulation.

The TodaHubDescriptor class maintains information about TODA hubs
within the map
"""


class TodaHubDescriptor:
    """A dictionary containing all of the TODA Hubs inside the map.

    :ivar hubDistribution: A dictionary that maps TODA hub IDs to tricycle counts.
    :ivar numberOfTricycles: Total number of tricycles across all hubs.
    """
    hubDistribution = dict()
    numberOfTricycles = 0

    def __init__(self, hub_distribution: dict = dict()) -> None:
        """Initializes the TODA dictionary object to be used.
        
        Assumes the hub_distribution dictionary uses hub IDs (starting with 'hub')
        as keys and the number of tricycles in each hub as values.
        
        :param hub_distribution: Dictionary with hub IDs as keys and tricycle counts as values. Defaults to empty dictionary.
        :type hub_distribution: dict
        """
        self.hubDistribution = hub_distribution
        self.numberOfTricycles = 0

        # Calculate the total number of tricycles in the simulation
        for number_of_tricycles_in_hub in hub_distribution.values():
            self.numberOfTricycles += number_of_tricycles_in_hub

    def getHubDistribution(self) -> dict:
        """Get the hub distribution dictionary.
        
        :return: Dictionary mapping hub IDs to tricycle counts.
        :rtype: dict
        """
        return self.hubDistribution
    
    def getNumberOfTricycles(self) -> int:
        """Get the total number of tricycles across all hubs.
        
        :return: Total number of tricycles in the simulation.
        :rtype: int
        """
        return self.numberOfTricycles
    
    def addHub(self, hub_id: str, number_of_tricycles: int) -> None:
        """Add or update a TODA hub to the current descriptor.

        :param hub_id: The string ID of the hub (should start with 'hub').
        :type hub_id: str
        :param number_of_tricycles: The number of tricycles in this hub (must be positive).
        :type number_of_tricycles: int
        :raises Exception: If hub_id is empty or number_of_tricycles is not positive.
        """
        # Check for empty or blank strings
        if not hub_id.strip():
            raise Exception("Invalid hub id. Was empty.")
        
        # Check for valid number of tricycles
        if number_of_tricycles <= 0:
            raise Exception(f"Invalid number of tricycles. Was: {number_of_tricycles}")
        
        # Set hub in dictionary
        self.hubDistribution[hub_id] = number_of_tricycles

        # Add number to total
        self.numberOfTricycles += number_of_tricycles