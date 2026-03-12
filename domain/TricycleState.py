"""Enum of all tricycle states in the simulation.

This module defines the states that a tricycle can have during sim, 
from spawning, dispatch, and to end of day.
"""

from enum import Enum


class TricycleState(Enum):
    """Defines the enumeration of tricycle states.
    
    :ivar FREE: Tricycle is available and waiting for a passenger.
    :ivar HAS_PASSENGER: Tricycle is currently carrying a passenger.
    :ivar DROPPING_OFF: Tricycle is at the destination, dropping off passenger.
    :ivar RETURNING_TO_TODA: Tricycle is returning to the TODA hub after dropping off.
    :ivar DEAD: Tricycle is no longer active in the simulation.
    :ivar TO_SPAWN: Tricycle is waiting to be spawned into the simulation.
    """
    FREE = 0
    HAS_PASSENGER = 1
    DROPPING_OFF = 2
    RETURNING_TO_TODA = 5
    DEAD = 6
    TO_SPAWN = 7