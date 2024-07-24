import adsk.core, adsk.fusion
from math import floor

class ImperialFraction:

    DENOMINATORS = [2, 4, 8, 16]

    def __init__(self, numerator: int, denominator: int):
        self.numerator = numerator
        self.denominator = denominator

    def __format__(self, format_spec):
        prefix_int = floor(self.numerator / self.denominator)
        if prefix_int < 1:
            return f'{self.numerator}/{self.denominator}\"'

        numerator = self.numerator - (self.denominator * prefix_int)
        if numerator == 0:
            return f'{prefix_int}\"'

        return f'{prefix_int} {numerator}/{self.denominator}\"'

    @classmethod
    def from_measurement(cls, measurement: float, units_manager: adsk.fusion.FusionUnitsManager):
        return cls._from_str(units_manager.formatValue(
            measurement, 'in', -1, adsk.core.BooleanOptions.DefaultBooleanOption, -1, False
        ))

    @classmethod
    def _from_str(cls, value: str):
        return cls._from_float(float(value))

    @classmethod
    def _from_float(cls, value: float):
        numerator, denominator = min(
            ((round(value * denominator), denominator) for denominator in cls.DENOMINATORS),
            key=lambda f: abs(value - f[0] / f[1])
        )
        return cls(numerator, denominator)
