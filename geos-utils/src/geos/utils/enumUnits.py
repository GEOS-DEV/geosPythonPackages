# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
# Units conversion factors chosen in this file are from
# https://www.petrobasics.com/unit-convert
from enum import Enum
from typing import cast

from typing_extensions import Self


class Unit:
    def __init__(
        self: Self, conversionMultiplier: float, conversionAdder: float, unitLabel: str
    ) -> None:
        """Unit enumeration.

        Args:
            conversionMultiplier (float): conversion multiplier
            conversionAdder (float): conversion adder
            unitLabel (str): symbol of the unit.
        """
        self.conversionMultiplier: float = conversionMultiplier
        self.conversionAdder: float = conversionAdder
        self.unitLabel: str = unitLabel


class Pressure(Enum):
    PA = Unit(1.0, 0.0, "Pa")
    KPA = Unit(1e-3, 0.0, "kPa")
    MPA = Unit(1e-6, 0.0, "MPa")
    GPA = Unit(1e-9, 0.0, "GPa")
    BAR = Unit(1.0e-5, 0.0, "Bar")
    PSI = Unit(0.00015, 0.0, "psi")


class Length(Enum):
    METER = Unit(1.0, 0.0, "m")
    KILOMETER = Unit(1e-3, 0.0, "km")
    FEET = Unit(3.28084, 0.0, "ft")
    MILE = Unit(0.00062, 0.0, "mile")


class Volume(Enum):
    CUBIC_METER = Unit(1.0, 0.0, "m3")
    CUBIC_FEET = Unit(35.31467, 0.0, "ft3")
    BBL = Unit(6.28981, 0.0, "bbl")


class Mass(Enum):
    KG = Unit(1.0, 0.0, "kg")
    TON = Unit(1e-3, 0.0, "ton")
    MEGATON = Unit(1e-6, 0.0, "Mton")
    POUND = Unit(2.20462, 0.0, "lb")


class Density(Enum):
    KG_PER_CUBIC_METER = Unit(1.0, 0.0, "kg/m3")
    G_PER_CUBIC_CENTIMETER = Unit(0.001, 0.0, "g/cm3")
    POUND_PER_BBL = Unit(0.35051, 0.0, "lb/bbl")


class VolumetricRate(Enum):
    CUBIC_METER_PER_SECOND = Unit(1.0, 0.0, "m3/s")
    CUBIC_METER_PER_HOUR = Unit(3600.0, 0.0, "m3/h")
    CUBIC_METER_PER_DAY = Unit(86400.0, 0.0, "m3/day")
    BBL_PER_DAY = Unit(54343.962, 0.0, "bbl/day")


class MassRate(Enum):
    KG_PER_SECOND = Unit(1.0, 0.0, "kg/s")
    KG_PER_HOUR = Unit(3600.0, 0.0, "kg/h")
    KG_PER_DAY = Unit(86400.0, 0.0, "kg/day")
    TON_PER_DAY = Unit(86.4, 0.0, "ton/day")
    MTPA = Unit(0.0315576, 0.0, "MTPA")


class Time(Enum):
    SECOND = Unit(1.0, 0.0, "s")
    HOUR = Unit(0.00028, 0.0, "h")
    DAY = Unit(1.1574e-5, 0.0, "day")
    MONTH = Unit(3.80263e-7, 0.0, "month")
    YEAR = Unit(3.1688e-8, 0.0, "year")


class Permeability(Enum):
    SQUARE_METER = Unit(1.0, 0.0, "m2")
    DARCY = Unit(1e12, 0.0, "D")
    MILLI_DARCY = Unit(1e15, 0.0, "mD")


class Temperature(Enum):
    K = Unit(1.0, 0.0, "K")
    CELSIUS = Unit(1.0, 273.15, "C")
    FAHRENHEIT = Unit(1.8, -459.67, "F")


class NoUnit(Enum):
    SAME = Unit(1.0, 0.0, "")


associationPropertyUnitEnum: dict[str, Enum] = {
    "pressure": cast(Enum, Pressure),
    "bhp": cast(Enum, Pressure),
    "stress": cast(Enum, Pressure),
    "length": cast(Enum, Length),
    "volumetricRate": cast(Enum, VolumetricRate),
    "massRate": cast(Enum, MassRate),
    "volume": cast(Enum, Volume),
    "mass": cast(Enum, Mass),
    "density": cast(Enum, Density),
    "temperature": cast(Enum, Temperature),
    "time": cast(Enum, Time),
    "permeability": cast(Enum, Permeability),
    "nounit": cast(Enum, NoUnit),
}


def getPropertyUnitEnum(propertyName: str) -> Enum:
    """Get the Unit enum from property name.

    Args:
        propertyName (str): name of the property.

    Returns:
        Enum: Unit enum.
    """
    return associationPropertyUnitEnum[propertyName]


def getSIUnits() -> dict[str, Unit]:
    """Get the dictionary of property Names:Units.

    Generates a dict where the keys are meta-properties
    like pressure, mass etc ... and where the values are Unit
    composed of a conversion factor and its unit associated.
    Here, the conversion factor will always be 1.0 and the unit will
    be the SI associate because we work with SI units.

    Returns:
        dict[str, Unit]: dictionary of unit names as keys and Unit enum as value.
    """
    return {
        "pressure": Pressure.PA.value,
        "bhp": Pressure.PA.value,
        "stress": Pressure.PA.value,
        "length": Length.METER.value,
        "volumetricRate": VolumetricRate.CUBIC_METER_PER_SECOND.value,
        "massRate": MassRate.KG_PER_SECOND.value,
        "volume": Volume.CUBIC_METER.value,
        "mass": Mass.KG.value,
        "density": Density.KG_PER_CUBIC_METER.value,
        "temperature": Temperature.K.value,
        "time": Time.SECOND.value,
        "permeability": Permeability.SQUARE_METER.value,
        "nounit": NoUnit.SAME.value,
    }


def convert(number: float, unitObj: Unit) -> float:
    """Converts a float number that has SI unit to a specific unit.

    Args:
        number (float): Number to convert.
        unitObj (Unit): Object containing conversion multiplier and adder.

    Returns:
        float: number converted to the correct unit.
    """
    return number * unitObj.conversionMultiplier + unitObj.conversionAdder


def enumerationDomainUnit(enumObj: Enum) -> str:
    """Get the xml code corresponding to unit enum object for drop down list.

    Args:
        enumObj (Enum): Unit enum object.

    Returns:
        str: xml text.
    """
    xml: str = """<EnumerationDomain name='enum'>"""
    for i, unitObj in enumerate(list(enumObj)):  # type: ignore[call-overload]
        unit: Unit = unitObj.value
        assert isinstance(unit, Unit), "enumObj does not contain Unit objects."
        xml += f"""<Entry text='{unit.unitLabel}' value='{i}'/>"""
    xml += """</EnumerationDomain>"""
    return xml
