from domain.Location import Location

class Passenger:
    """Represents a passenger request to a tricycle within the simulation.
    
    Attributes:
        name: unique ID assigned to a passenger.
        willingness_to_pay: maximum amount they would pay for their trip.
        destination: location they wish to go to.
    """

    def __init__(self, name: str, willingness_to_pay: float, 
                 destination: Location) -> None:
        """Initializes passenger with name, destination, and willingness to pay.
        
        Args:
            name: unique ID assigned to a passenger.
            willingness_to_pay: maximum amount they would pay for their trip.
            destination: location they wish to go to.
        """
        self.name = name
        self.willingness_to_pay = willingness_to_pay
        self.destination = destination