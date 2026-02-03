class TodaHubDescriptor:
    """A dictionary containing all of the TODA Hubs inside the map.

    Attributes:
        hubDistribution: a dictionary object with that gives the number of 
            tricycles in a TODA hub given the hub ID
        numberOfTricycles: the total number of tricycles inside the map
    """
    hubDistribution = dict()
    numberOfTricycles = 0

    def __init__(self, hub_distribution: dict=dict()) -> None:
        """Initializes a specialized dictionary object given a normal 
        dictionary.

        Assumes the following structure, key=hub ID as string that starts with
        'hub', value=number of tricycles in the TODA hub.
        
        Args:
            hub_distribution: a dictionary object with that gives the number of 
                tricycles in a TODA hub given the hub ID
        """
        self.hubDistribution = hub_distribution
        self.numberOfTricycles = 0

        # Calculates for the total number of tricycles in the simulation
        for number_of_tricycles_in_hub in hub_distribution.values():
            self.numberOfTricycles += number_of_tricycles_in_hub

    def getHubDistribution(self) -> dict:
        """Getter for the hub distribution dictionary.
        
        Returns:
            A dictionary object with that gives the number of 
            tricycles in a TODA hub given the hub ID.
        """
        return self.hubDistribution
    
    def getNumberOfTricycles(self) -> int:
        """Getter for the total number of tricycles inside the simulation.
        
        Returns:
            The number of tricycles in the entire map.
        """
        return self.numberOfTricycles
    
    def addHub(self, hub_id: str, number_of_tricycles: int) -> None:
        """Adds a TODA hub to the dictionary.

        Args:
            hub_id: the string ID of the hub. Should start with 'hub'.
            number_of_tricycles: the number of tricycles inside the hub.
                Should be positive.
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