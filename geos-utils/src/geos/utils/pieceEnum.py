# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
from enum import Enum


class Piece( str, Enum ):
    """String Enum of a vtkDataObject pieces."""
    POINTS = "points"
    CELLS = "cells"
    BOTH = "cells and points"
    FIELD = "field"
    NONE = "none"
