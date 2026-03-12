"""Represents passengers needing tricycle rides in the simulation.

This module defines the Passenger class of the simulation. Each 
passenger has a destination, a maximum willingness to pay, aspired price,
and maximum wait duration (patience).
"""

from domain.Location import Location


class Passenger:
    """Represents a passenger request to a tricycle within the simulation.
    
    :ivar name: Unique ID assigned to a passenger.
    :ivar willingness_to_pay: Maximum amount they would pay for their trip.
    :ivar patience: Duration they are willing to wait for available transportation.
    :ivar aspiredPrice: Price they expect or prefer for the trip.
    :ivar destination: Location they wish to go to.
    """

    def __init__(self, name: str, willingness_to_pay: float, patience: float, 
                 aspiredPrice: float, destination: Location) -> None:
        """Initialize a passenger with travel preferences and destination.
        
        :param name: Unique ID assigned to a passenger.
        :type name: str
        :param willingness_to_pay: Maximum amount they would pay for the trip.
        :type willingness_to_pay: float
        :param patience: Duration in seconds they are willing to wait.
        :type patience: float
        :param aspiredPrice: Expected price for the trip.
        :type aspiredPrice: float
        :param destination: Location object representing the passenger's destination.
        :type destination: Location
        """
        self.name = name
        self.willingness_to_pay = willingness_to_pay
        self.patience = patience
        self.aspiredPrice = aspiredPrice
        self.destination = destination

    def getDestination(self) -> Location:
        """Get the destination location of the passenger.
        
        :return: Location object representing the passenger's destination.
        :rtype: Location
        """
        return self.destination
    
    def getPatience(self) -> float:
        """Get the patience level of the passenger.
        
        :return: Float representing the passenger's patience level (in ticks).
        :rtype: float
        """
        return self.patience
    
    def getAspiredPrice(self) -> float:
        """Get the aspired price of the passenger.
        
        :return: Float representing the passenger's aspired price.
        :rtype: float
        """
        return self.aspiredPrice