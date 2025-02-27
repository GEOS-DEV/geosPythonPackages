# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
import unittest

from typing_extensions import Self

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.join(os.path.dirname(dir_path), "src")
if parent_dir_path not in sys.path:
    sys.path.append(parent_dir_path)

from geos_posp.visu.pythonViewUtils import functionsFigure2DGenerator as utils


class TestsFunctionsFigure2DGenerator(unittest.TestCase):
    def test_associatePropertyToAxeType(self: Self) -> None:
        """Test of associatePropertyToAxeType function."""
        example: list[str] = [
            "WellControls1__BHP__Pa__Source1",
            "WellControls1__TotalMassRate__kg/s__Source1",
            "WellControls1__TotalSurfaceVolumetricRate__m3/s__Source1",
            "WellControls1__SurfaceVolumetricRateCO2__m3/s__Source1",
            "WellControls1__SurfaceVolumetricRateWater__m3/s__Source1",
            "WellControls2__BHP__Pa__Source1",
            "WellControls2__TotalMassRate__kg/s__Source1",
            "WellControls2__TotalSurfaceVolumetricRate__m3/s__Source1",
            "WellControls2__SurfaceVolumetricRateCO2__m3/s__Source1",
            "WellControls2__SurfaceVolumetricRateWater__m3/s__Source1",
            "WellControls3__BHP__Pa__Source1",
            "WellControls3__TotalMassRate__tons/day__Source1",
            "WellControls3__TotalSurfaceVolumetricRate__bbl/day__Source1",
            "WellControls3__SurfaceVolumetricRateCO2__bbl/day__Source1",
            "WellControls3__SurfaceVolumetricRateWater__bbl/day__Source1",
            "Mean__BHP__Pa__Source1",
            "Mean__TotalMassRate__tons/day__Source1",
            "Mean_TotalVolumetricRate__bbl/day__Source1",
            "Mean__SurfaceVolumetricRateCO2__bbl/day__Source1",
            "Mean__SurfaceVolumetricRateWater__bbl/day__Source1",
        ]
        expected: dict[str, list[str]] = {
            "BHP (Pa)": [
                "WellControls1__BHP__Pa__Source1",
                "WellControls2__BHP__Pa__Source1",
                "WellControls3__BHP__Pa__Source1",
                "Mean__BHP__Pa__Source1",
            ],
            "MassRate (kg/s)": [
                "WellControls1__TotalMassRate__kg/s__Source1",
                "WellControls2__TotalMassRate__kg/s__Source1",
            ],
            "VolumetricRate (m3/s)": [
                "WellControls1__TotalSurfaceVolumetricRate__m3/s__Source1",
                "WellControls1__SurfaceVolumetricRateCO2__m3/s__Source1",
                "WellControls1__SurfaceVolumetricRateWater__m3/s__Source1",
                "WellControls2__TotalSurfaceVolumetricRate__m3/s__Source1",
                "WellControls2__SurfaceVolumetricRateCO2__m3/s__Source1",
                "WellControls2__SurfaceVolumetricRateWater__m3/s__Source1",
            ],
            "MassRate (tons/day)": [
                "WellControls3__TotalMassRate__tons/day__Source1",
                "Mean__TotalMassRate__tons/day__Source1",
            ],
            "VolumetricRate (bbl/day)": [
                "WellControls3__TotalSurfaceVolumetricRate__bbl/day__Source1",
                "WellControls3__SurfaceVolumetricRateCO2__bbl/day__Source1",
                "WellControls3__SurfaceVolumetricRateWater__bbl/day__Source1",
                "Mean_TotalVolumetricRate__bbl/day__Source1",
                "Mean__SurfaceVolumetricRateCO2__bbl/day__Source1",
                "Mean__SurfaceVolumetricRateWater__bbl/day__Source1",
            ],
        }
        obtained: dict[str, list[str]] = utils.associatePropertyToAxeType(example)
        self.assertEqual(expected, obtained)

    def test_propertiesPerIdentifier(self: Self) -> None:
        """Test of propertiesPerIdentifier function."""
        propertyNames: list[str] = [
            "WellControls1__BHP__Pa__Source1",
            "WellControls1__TotalMassRate__kg/s__Source1",
            "WellControls2__BHP__Pa__Source1",
            "WellControls2__TotalMassRate__kg/s__Source1",
        ]
        expected: dict[str, list[str]] = {
            "WellControls1": [
                "WellControls1__BHP__Pa__Source1",
                "WellControls1__TotalMassRate__kg/s__Source1",
            ],
            "WellControls2": [
                "WellControls2__BHP__Pa__Source1",
                "WellControls2__TotalMassRate__kg/s__Source1",
            ],
        }
        obtained = utils.propertiesPerIdentifier(propertyNames)
        self.assertEqual(expected, obtained)

    def test_associationIdentifers(self: Self) -> None:
        """Test of associationIdentifiers function."""
        propertyNames: list[str] = [
            "WellControls1__BHP__Pa__Source1",
            "WellControls1__TotalMassRate__kg/s__Source1",
            "WellControls1__TotalSurfaceVolumetricRate__m3/s__Source1",
            "WellControls1__SurfaceVolumetricRateCO2__m3/s__Source1",
            "WellControls1__SurfaceVolumetricRateWater__m3/s__Source1",
            "WellControls2__BHP__Pa__Source1",
            "WellControls2__TotalMassRate__kg/s__Source1",
            "WellControls2__TotalSurfaceVolumetricRate__m3/s__Source1",
            "WellControls2__SurfaceVolumetricRateCO2__m3/s__Source1",
            "WellControls2__SurfaceVolumetricRateWater__m3/s__Source1",
            "WellControls3__BHP__Pa__Source1",
            "WellControls3__TotalMassRate__tons/day__Source1",
            "WellControls3__TotalSurfaceVolumetricRate__bbl/day__Source1",
            "WellControls3__SurfaceVolumetricRateCO2__bbl/day__Source1",
            "WellControls3__SurfaceVolumetricRateWater__bbl/day__Source1",
            "Mean__BHP__Pa__Source1",
            "Mean__TotalMassRate__tons/day__Source1",
            "Mean__TotalSurfaceVolumetricRate__bbl/day__Source1",
            "Mean__SurfaceVolumetricRateCO2__bbl/day__Source1",
            "Mean__SurfaceVolumetricRateWater__bbl/day__Source1",
        ]
        expected: dict[str, dict[str, list[str]]] = {
            "WellControls1": {
                "BHP (Pa)": [
                    "WellControls1__BHP__Pa__Source1",
                ],
                "MassRate (kg/s)": [
                    "WellControls1__TotalMassRate__kg/s__Source1",
                ],
                "VolumetricRate (m3/s)": [
                    "WellControls1__TotalSurfaceVolumetricRate__m3/s__Source1",
                    "WellControls1__SurfaceVolumetricRateCO2__m3/s__Source1",
                    "WellControls1__SurfaceVolumetricRateWater__m3/s__Source1",
                ],
            },
            "WellControls2": {
                "BHP (Pa)": [
                    "WellControls2__BHP__Pa__Source1",
                ],
                "MassRate (kg/s)": [
                    "WellControls2__TotalMassRate__kg/s__Source1",
                ],
                "VolumetricRate (m3/s)": [
                    "WellControls2__TotalSurfaceVolumetricRate__m3/s__Source1",
                    "WellControls2__SurfaceVolumetricRateCO2__m3/s__Source1",
                    "WellControls2__SurfaceVolumetricRateWater__m3/s__Source1",
                ],
            },
            "WellControls3": {
                "BHP (Pa)": [
                    "WellControls3__BHP__Pa__Source1",
                ],
                "MassRate (tons/day)": [
                    "WellControls3__TotalMassRate__tons/day__Source1",
                ],
                "VolumetricRate (bbl/day)": [
                    "WellControls3__TotalSurfaceVolumetricRate__bbl/day__Source1",
                    "WellControls3__SurfaceVolumetricRateCO2__bbl/day__Source1",
                    "WellControls3__SurfaceVolumetricRateWater__bbl/day__Source1",
                ],
            },
            "Mean": {
                "BHP (Pa)": [
                    "Mean__BHP__Pa__Source1",
                ],
                "MassRate (tons/day)": [
                    "Mean__TotalMassRate__tons/day__Source1",
                ],
                "VolumetricRate (bbl/day)": [
                    "Mean__TotalSurfaceVolumetricRate__bbl/day__Source1",
                    "Mean__SurfaceVolumetricRateCO2__bbl/day__Source1",
                    "Mean__SurfaceVolumetricRateWater__bbl/day__Source1",
                ],
            },
        }
        obtained = utils.associationIdentifiers(propertyNames)
        self.assertEqual(expected, obtained)


if __name__ == "__main__":
    unittest.main()
