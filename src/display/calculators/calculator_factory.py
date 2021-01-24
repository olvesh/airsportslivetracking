from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from influx_facade import InfluxFacade
    from display.calculators.calculator import Calculator
from display.calculators.precision_calculator import PrecisionCalculator
from display.models import Contestant, Scorecard


def calculator_factory(contestant: "Contestant", influx: "InfluxFacade", live_processing: bool = True) -> "Calculator":
    if contestant.navigation_task.scorecard.calculator == Scorecard.PRECISION:
        return PrecisionCalculator(contestant, influx, live_processing=live_processing)
