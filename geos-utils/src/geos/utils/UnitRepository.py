# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
from enum import Enum
from typing import Union

from typing_extensions import Self

from geos.utils.enumUnits import Unit, getPropertyUnitEnum, getSIUnits


class UnitRepository:

    def __init__( self: Self, userPropertiesUnitChoice: Union[ dict[ str, int ], None ] = None ) -> None:
        """Unit repository.

        * Input example : { "pressure": 4, "bhp": 4,"stress": 3, "length": 2, ...}
        * Output example : { "pressure": Pressure.BAR.value, "bhp": Pressure.BAR.value,
            "stress": Pressure.MPA.value, "length": Lenght.FEET.value,
            ...
            }

        These Pressure.BAR.value corresponds to Unit objects that have a
        conversion multiplier and a conversion adder, and also a unit label.

        Args:
            userPropertiesUnitChoice (dict[str, int], Optional): dictionary of
                unit user choices.

                Defaults {}.
        """
        self.m_userPropsUnitChoice: dict[ str, int ] = {}
        if userPropertiesUnitChoice is not None:
            self.m_userPropsUnitChoice = userPropertiesUnitChoice

        self.m_propertiesUnit: dict[ str, Unit ] = getSIUnits()
        if self.m_userPropsUnitChoice != {}:
            self.initPropertiesUnit()

    def initPropertiesUnit( self: Self ) -> None:
        """Initialize the attribute m_propertiesUnit."""
        propertiesUnit: dict[ str, Unit ] = getSIUnits()
        for propertyName, userChoice in self.m_userPropsUnitChoice.items():
            unitEnum: Enum = getPropertyUnitEnum( propertyName )
            unitObj: Unit = list( unitEnum )[ userChoice ].value  # type: ignore[call-overload]
            propertiesUnit[ propertyName ] = unitObj
        self.m_propertiesUnit = propertiesUnit

    def getPropertiesUnit( self: Self ) -> dict[ str, Unit ]:
        """Access the m_propertiesUnit attribute.

        Returns:
            dict[str, Unit]: dictionary of unit as values for each property as
            keys.
        """
        return self.m_propertiesUnit
