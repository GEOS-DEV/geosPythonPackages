# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
import pyvista as pv
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkDataArray


def read_unstructured_grid( filename: str ) -> pv.UnstructuredGrid:
    """Read an unstructured grid from a .vtu file."""
    return pv.read( filename ).cast_to_unstructured_grid()


def split_vector_arrays( ug: pv.UnstructuredGrid ) -> None:
    """Create N 1-component arrays from each vector array with N components."""
    for data in [ ug.GetPointData(), ug.GetCellData() ]:
        for i in range( data.GetNumberOfArrays() ):
            array: vtkDataArray = data.GetArray( i )
            if array.GetNumberOfComponents() != 1:
                np_array = vtk_to_numpy( array )
                array_name = array.GetName()
                data.RemoveArray( array_name )
                for comp in range( array.GetNumberOfComponents() ):
                    component = np_array[ :, comp ]
                    new_array_name = f"{array_name}_{comp}"
                    new_array = numpy_to_vtk( component, deep=True )
                    new_array.SetName( new_array_name )
                    data.AddArray( new_array )
