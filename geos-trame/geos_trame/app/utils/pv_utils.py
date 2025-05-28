# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
import pyvista as pv


def read_unstructured_grid( filename ) -> pv.UnstructuredGrid:
    """
    Read an unstructured grid from a .vtu file.
    """
    return pv.read( filename ).cast_to_unstructured_grid()
