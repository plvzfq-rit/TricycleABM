from enum import Enum

class TricycleState(Enum):
    FREE = 0
    HAS_PASSENGER = 1
    DROPPING_OFF = 2
    GOING_TO_REFUEL = 3
    REFUELLING = 4
    RETURNING_TO_TODA = 5