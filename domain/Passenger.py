from domain.Location import Location

class Passenger:
    """Represents a passenger request to a tricycle within the simulation.
    
    Attributes:
        name: unique ID assigned to a passenger.
        willingness_to_pay: maximum amount they would pay for their trip.
        destination: location they wish to go to.
    """

    def __init__(self, name: str, willingness_to_pay: float, patience: float, 
                 aspiredPrice: float, destination: Location) -> None:
        """Initializes passenger with name, destination, and willingness to pay.
        
        Args:
            name: unique ID assigned to a passenger.
            willingness_to_pay: maximum amount they would pay for their trip.
            destination: location they wish to go to.
        """
        self.name = name
        self.willingness_to_pay = willingness_to_pay
        self.patience = patience
        self.aspiredPrice = aspiredPrice
        self.destination = destination

    def getDestination(self) -> Location:
        """Get the destination location of the passenger.
        
        Returns:
            Location object representing the passenger's destination.
        """
        return self.destination
    
    def getPatience(self) -> float:
        """Get the patience level of the passenger.
        
        Returns:
            Float representing the passenger's patience level.
        """
        return self.patience
    
    def getWillingnessToPay(self) -> float:
        """Get the willingness to pay of the passenger.
        
        Returns:
            Float representing the passenger's willingness to pay.
        """
        return self.willingness_to_pay
    
    def getAspiredPrice(self) -> float:
        """Get the aspired price of the passenger.
        
        Returns:
            Float representing the passenger's aspired price.
        """
        return self.aspiredPrice