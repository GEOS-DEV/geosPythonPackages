# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
import contextlib
import io
import os
import sys
import unittest

from typing_extensions import Self

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.join(os.path.dirname(dir_path), "src")
if parent_dir_path not in sys.path:
    sys.path.append(parent_dir_path)

from geos_posp.readers.GeosLogReaderAquifers import GeosLogReaderAquifers
from geos_posp.readers.GeosLogReaderConvergence import GeosLogReaderConvergence
from geos_posp.readers.GeosLogReaderFlow import GeosLogReaderFlow
from geos_posp.readers.GeosLogReaderWells import GeosLogReaderWells
from geos_posp.utils.UnitRepository import Unit, UnitRepository

unitsObjSI: UnitRepository = UnitRepository()
conversionFactors: dict[str, Unit] = unitsObjSI.getPropertiesUnit()
pathFlowSim: str = os.path.join(dir_path, "Data/empty.txt")


class TestsInvalidLogs(unittest.TestCase):
    def test_emptyLog(self: Self) -> None:
        """Test empty log."""
        # capturedOutWells = io.StringIO()
        with self.assertRaises(AssertionError):
            objWells = GeosLogReaderWells(  # noqa: F841
                pathFlowSim, conversionFactors, [], 1
            )

        capturedOutAquif = io.StringIO()
        with contextlib.redirect_stdout(capturedOutAquif):
            objAquif = GeosLogReaderAquifers(  # noqa: F841
                pathFlowSim, conversionFactors
            )
        expectedOutAquif: str = (
            "Invalid Geos log file. Please check that your log "
            + "did not crash and contains aquifers."
        )
        self.assertEqual(capturedOutAquif.getvalue().strip(), expectedOutAquif)

        with self.assertRaises(AssertionError):
            objFlow = GeosLogReaderFlow(  # noqa: F841
                pathFlowSim, conversionFactors
            )  # noqa: F841

        capturedOutConv = io.StringIO()
        with contextlib.redirect_stdout(capturedOutConv):
            objConv = GeosLogReaderConvergence(  # noqa: F841
                pathFlowSim, conversionFactors
            )
        expectedOutConv: str = (
            "Invalid Geos log file. Please check that your log " + "did not crash."
        )
        self.assertEqual(capturedOutConv.getvalue().strip(), expectedOutConv)


if __name__ == "__main__":
    unittest.main()
