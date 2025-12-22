# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest

from typing import Any
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

from geos.processing.generic_processing_tools.DiffFields import DiffFields
