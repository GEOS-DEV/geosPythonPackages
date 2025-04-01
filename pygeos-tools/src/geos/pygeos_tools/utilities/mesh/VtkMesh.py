# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# Copyright (c) 2019-     INRIA project-team Makutu
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------

from os import path
import numpy.typing as npt
from typing import Iterable, Tuple
from typing_extensions import Self
from geos.pygeos_tools.utilities.model.pyevtk_tools import cGlobalIds
from geos.utils.errors_handling.classes import required_attributes
from geos.utils.vtk.helpers import getCopyNumpyArrayByName, getNumpyGlobalIdsArray, getNumpyArrayByName
from geos.utils.vtk.io import read_mesh, write_mesh
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkDataArray, vtkDoubleArray, vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellLocator, vtkFieldData, vtkImageData, vtkPointData, vtkPointSet
from vtkmodules.vtkFiltersCore import vtkExtractCells, vtkResampleWithDataSet
from vtkmodules.vtkFiltersExtraction import vtkExtractGrid


__doc__ = """
VTKMesh class uses a VTK filepath to read, extract data and write a new VTK file.
Along with wrapping of VTK methods to extract geometry data and arrays, this class also allows you to extract
geometrically a subset of the original mesh.

The input and output VTK file types handled currently are .vtu .vts .pvts .pvtu.
"""


class VTKMesh:
    """
    VTK format Mesh. Now handling .vtu .vts .pvts .pvtu

    Attributes
    ----------
        meshfile : str
            Mesh filename
        vtktype : str
            Format of the VTK mesh
        bounds : tuple of float
            Real bounds of the mesh (xmin, xmax, ymin, ymax, zmin, zmax)
        numberOfPoints : int
            Total number of points of the mesh
        numberOfCells : int
            Total number of cells of the mesh
        isSet : bool
            Whether or not the mesh properties have been set
        hasLocator : bool
            Whether or not the mesh cell locator has been initialized
    """

    def __init__( self: Self, meshfile: str ):
        """
        Parameters
        ----------
            meshfile : str
                Mesh filename
        """
        self.meshfile: str = meshfile
        self.vtktype: str = path.splitext( self.meshfile )[ -1 ][ 1: ]

        self.bounds: Iterable[ float ] = None
        self.numberOfPoints: int = None
        self.numberOfCells: int = None

        self.isSet: bool = False
        self.hasLocator: bool = False

    """
    Mesh reading, writing and extraction
    """
    @required_attributes( "meshFile" )
    def read( self: Self ) -> vtkPointSet:
        """Read information from the VTK file

        Returns
        --------
            vtk.vtkPointSet
                General representation of VTK mesh data
        """
        return read_mesh( self.meshfile )

    def export( self: Self, data: vtkPointSet = None, rootname: str = None, vtktype: str = None ) -> str:
        """
        Write VTK data in a file

        Parameters
        ----------
            data : vtkPointSet
                vtk.vtkStructuredGrid or vtk.vtkUnstructuredGrid. Default is self.read()
            rootname : str
                Root of the output filename. Default is self.meshfile (without extension)
            vtktype : str
                Format of the output VTK. Default is self.vtktype

        Returns
        --------
            filename : str
                Output filename
        """
        if vtktype is None:
            vtktype = self.vtktype
        if rootname is None:
            rootname, _ = path.splitext( self.meshfile )
        if data is None:
            data = self.read()

        filename: str = ".".join( ( rootname, vtktype ) )
        write_mesh( data, filename )
        return filename

    def extractMesh( self: Self,
                     center: Iterable[ float ],
                     srootname: str,
                     dist: Iterable[ float ] = [ None, None, None ],
                     comm=None,
                     export: bool = True ):
        """
        Extract a rectangular submesh such that for each axis we have the subax: [center-dist, center+dist]

        Parameters
        ---------
            center : 3d float
                Requested center of the subbox
            srootname : str
                Submesh root filename
            dist : 3d float
                Distance to the center in each direction
            comm : MPI.COMM_WORLD
                MPI communicator
            export : bool

        Returns
        -------
            VTKMesh
                Submesh extracted
        """
        assert self.vtktype in ( "vtu", "pvtu", "vts", "pvts" )
        vtktype = self.vtktype[ -3: ]
        sfilename = ".".join( ( srootname, vtktype ) )

        if comm is None or comm.Get_rank() == 0:
            if not self.isSet:
                self.setMeshProperties()
            minpos = list()
            maxpos = list()

            for i in range( 3 ):
                xmin, d = self.getSubAx( center[ i ], dist[ i ], ax=i + 1 )
                minpos.append( xmin )
                maxpos.append( xmin + d )

            data = self.read()
            submesh = VTKSubMesh( sfilename, data, minpos, maxpos, create=export )

        else:
            submesh = VTKMesh( sfilename )

        # if file creation, wait for rank 0 to finish
        if export:
            info = "Done"
            comm.bcast( info, root=0 )

        return submesh

    """
    Accessors
    """
    def getArray( self: Self, name: str, dtype: str = "cell", copy: bool = False, sorted: bool = False ) -> npt.NDArray:
        """
        Return a cell or point data array. If the file is a pvtu, the array is sorted with global ids

        Parameters
        -----------
            name : str
                Name of the vtk cell/point data array
            dtype : str
                Type of vtk data `cell` or `point`
            copy : bool
                Return a copy of the requested array. Default is False
            sorted : bool
                Return the array sorted with respect to GlobalPointIds or GlobalCellIds. Default is False

        Returns
        --------
            array : numpy array
                Requested array
        """
        assert dtype.lower() in ( "cell", "point" )
        fdata = self.getCellData() if dtype.lower() == "cell" else self.getPointData()
        if copy:
            array = getCopyNumpyArrayByName( fdata, name, sorted=sorted )
        else:
            array = getNumpyArrayByName( fdata, name, sorted=sorted )
        return array

    def getBounds( self: Self ) -> Iterable[ float ]:
        """
        Get the bounds of the mesh in the format:
            (xmin, xmax, ymin, ymax, zmin, zmax)

        Returns
        -------
            tuple or None
                Bounds of the mesh
        """
        return self.bounds

    def getCellData( self: Self ) -> vtkFieldData:
        """Read the cell data

        Returns
        --------
            vtkFieldData
                Cell data information
        """
        data = self.read()
        return data.GetCellData()

    def getCellContainingPoint( self: Self, point: Iterable[ float ] ) -> int:
        """
        Return the global index of the cell containing the coordinates

        Parameters
        -----------
            point : array-like of float
                Point coordinates

        Returns
        --------
            cellId : int
                id of the cell containing the given point
        """
        if not self.hasLocator:
            self.setCellLocator()

        cellId: int = self.cellLocator.FindCell( [ point[ 0 ], point[ 1 ], point[ 2 ] ] )
        return cellId

    def getExtractToGlobalMap( self: Self ) -> npt.NDArray:
        """Return the global cell ids

        Returns
        --------
            array : npt.NDArray
                Global cell Ids or None if not set in the mesh
        """
        return self.getGlobalIds()

    def getGlobalIds( self: Self, dtype: str = "cell" ) -> npt.NDArray:
        """Return the global ids of the cells or points. If the mesh is an extract of an original mesh,
        it is the local to global map

        Parameters
        ----------
            dtype : str
                Type of data: `cell` or `point`

        Returns
        --------
            array : npt.NDArray
                Global Ids
        """
        assert dtype.lower() in ( "cell", "point" )
        fdata = self.getCellData() if dtype.lower() == "cell" else self.getPointData()
        return getNumpyGlobalIdsArray( fdata )

    def getNumberOfBlocks( self: Self ) -> int:
        """Return the number of blocks of a mesh."""
        if self.vtktype in [ "pvtu", "pvts" ]:
            with open( self.meshfile ) as ff:
                nb: int = 0
                for line in ff:
                    m = line.split()
                    if m[ 0 ] == '<Piece':
                        nb += 1
            return nb
        else:
            return 1

    @required_attributes( "numberOfCells" )
    def getNumberOfCells( self: Self ) -> int:
        """
        Get the total number of cells of the mesh

        Returns
        -------
            int
                Number of cells
        """
        return self.numberOfCells

    @required_attributes( "numberOfPoints" )
    def getNumberOfPoints( self: Self ) -> int:
        """
        Get the total number of points of the mesh

        Returns
        -------
            int
                Number of points
        """
        return self.numberOfPoints

    def getPointData( self: Self ) -> vtkFieldData:
        """Read the point data

        Returns
        --------
            vtkFieldData
                Point data information
        """
        data = self.read()
        return data.GetPointData()

    @required_attributes( "bounds" )
    def getSubAx( self: Self, center: float, dist: float, ax: int ) -> Tuple[ float, float ]:
        """
        Return the min and max positions in the mesh given the center, distance and ax considered.
        If the 2*distance if greater than the bounds, the min/max is the corresponding mesh bound.

        Parameters
        ----------
            center : float
                Central position considered
            dist : float
                Max distance requested
            ax : int
                Ax to consider (1, 2, 3)

        Returns
        -------
            min, max : float
                Min and Max positions
        """
        assert ( ax is int )
        bounds = [ self.bounds[ ( ax - 1 ) * 2 ], self.bounds[ ax * 2 - 1 ] ]

        if dist is not None:
            dist = abs( dist )
            ox = max( bounds[ 0 ], center - dist )
            x = min( bounds[ 1 ] - ox, 2 * dist )
        else:
            ox = bounds[ 0 ]
            x = bounds[ 1 ]
        return ox, x

    """
    Update methods
    """
    def updateCellLocator( self: Self ):
        """Set the cell locator"""
        if not self.isSet:
            self.updateMeshProperties()

        if not self.hasLocator:
            self.cellLocator = vtkCellLocator()
            self.cellLocator.SetDataSet( self.read() )
            self.cellLocator.BuildLocator()
            self.hasLocator = True

    def updateMeshProperties( self: Self ) -> None:
        """Read and updates the attributes such as the bounds, number of points and cells"""
        data = self.read()
        self.bounds = data.GetBounds()
        self.numberOfPoints = data.GetNumberOfPoints()
        self.numberOfCells = data.GetNumberOfCells()
        self.isSet = True

    """
    Interpolation
    """
    def interpolateValues( self: Self, centers: Iterable[ Iterable[ float ] ],
                           name: str, values: npt.NDArray ) -> npt.NDArray:
        """
        Interpolate the given cell data over the given points

        Parameters
        -----------
            centers : list of list of float
                Center coordinates
            name : str
                Name of the new array
            values : numpy array
                New values

        Returns
        --------
           interpValues : npt.NDArray
                interpolated values over the given points
        """
        if not self.isSet:
            self.updateMeshProperties()

        dest = vtkPointSet()
        destPoints = vtkPoints()

        for point in centers:
            destPoints.InsertNextPoint( [ point[ 0 ], point[ 1 ], point[ 2 ] ] )
        dest.SetPoints( destPoints )

        transferArray = vtkDoubleArray()
        for value in values:
            transferArray.InsertNextTuple1( value )
        transferArray.SetName( name )

        data = self.read()
        data.GetCellData().AddArray( transferArray )
        resample = vtkResampleWithDataSet()
        resample.SetSourceData( data )
        resample.SetInputData( dest )
        resample.Update()

        pointdata: vtkPointData = resample.GetOutput().GetPointData()

        interpValues = None
        if pointdata.HasArray( name ):
            arr: vtkDataArray = pointdata.GetArray( name )
            interpValues = vtk_to_numpy( arr )
        return interpValues


class VTKSubMesh( VTKMesh ):
    """
    Class defining a submesh of an existing VTK mesh

    Attributes
    -----------
        meshfile : str
            Submesh filename
        vtktype : str
            Format of the VTK submesh
        bounds : tuple of int
            Real bounds of the mesh (xmin, xmax, ymin, ymax, zmin, zmax)
        numberOfPoints : int
            Total number of points of the submesh
        numberOfCells : int
            Total number of cells of the submesh
        isSet : bool
            Whether or not the mesh properties have been set
    """

    def __init__( self: Self, meshfile: str, data: vtkImageData, minpos, maxpos, create=True ):
        """
        Parameters
        -----------
            meshfile : str
                Submesh filename
            data : vtk.vtkDataObject
                General representation of the original mesh
            minpos : 3d array-like of float
                Minimal positions for the cropping for each axis
            maxpos : 3d array-like of float
                Maximal positions for the cropping for each axis
            create : bool
                Whether or not to create the VTKfile
                Default is True
        """
        super().__init__( meshfile )

        sdata = self.__setData( data, minpos, maxpos )
        self.__setGlobalIds( sdata, data )

        if create:
            self.export( data=sdata )

    def __setGlobalIds( self: Self, sdata: vtkImageData, data: vtkImageData ):
        """
        Set the global cell Ids of the submesh

        Parameters
            sdata : vtk.vtkDataObject
                General representation of the submesh
        """
        if self.vtktype == "vtu":
            subcdata = sdata.GetCellData()
            if subcdata.HasArray( "GlobalCellIds" ) == 1:
                subcdata.RemoveArray( "vtkOriginalCellIds" )
            else:
                cgids: vtkDataArray = subcdata.GetArray( "vtkOriginalCellIds" )
                cgids.SetName( "GlobalCellIds" )

        elif self.vtktype == "vts":
            if not sdata.GetCellData().HasArray( "GlobalCellIds" ):
                nx_extract, ny_extract, nz_extract = sdata.GetDimensions()
                dx = data.GetBounds()[ 1 ] / data.GetExtent()[ 1 ]
                dy = data.GetBounds()[ 3 ] / data.GetExtent()[ 3 ]
                dz = data.GetBounds()[ 5 ] / data.GetExtent()[ 5 ]
                nx, ny, nz = data.GetDimensions()
                xmin, ymin, zmin = sdata.GetBounds()[ 0::2 ]
                xmin0, ymin0, zmin0 = self.bounds[ 0::2 ]

                cgids = cGlobalIds( nx_extract, ny_extract, nz_extract, dx, dy, dz, xmin, ymin, zmin, nx, ny, nz, xmin0,
                                    ymin0, zmin0 )

                subcdata = sdata.GetCellData()
                cgidsAsVtkArray = numpy_to_vtk( num_array=cgids.ravel(), deep=True )
                cgidsAsVtkArray.SetName( "GlobalCellIds" )
                subcdata.AddArray( cgidsAsVtkArray )

    def __setData( self: Self, data: vtkImageData, minpos, maxpos ):
        """
        Return the submesh extracted from the whole mesh dataset

        Parameters
        -----------
            data : vtk.vtkDataObject
                General representation of the original mesh
            minpos : 3d array-like of float
                Minimal positions for the cropping for each axis
            maxpos : 3d array-like of float
                Maximal positions for the cropping for each axis
        """
        assert None not in minpos and len( minpos ) == 3
        assert None not in maxpos and len( maxpos ) == 3

        if self.vtktype == "vtu":
            cellLocator = vtkCellLocator()
            cellLocator.SetDataSet( data )
            cellLocator.BuildLocator()

            idList = vtkIdList()
            # Extraction of the cells
            extract = vtkExtractCells()
            extract.SetInputData( data )
            extract.SetCellList( idList )
            extract.Update()
            dataExtract = extract.GetOutput()

        elif self.vtktype == "vts":
            # vtkExtractGrid requires the [i,j,k] coordinates
            # distances and positions have to be converted
            dx = data.GetBounds()[ 1 ] / data.GetExtent()[ 1 ]
            dy = data.GetBounds()[ 3 ] / data.GetExtent()[ 3 ]
            dz = data.GetBounds()[ 5 ] / data.GetExtent()[ 5 ]

            minx = int( minpos[ 0 ] // dx )
            miny = int( minpos[ 1 ] // dy )
            minz = int( minpos[ 2 ] // dz )

            maxx = int( maxpos[ 0 ] // dx )
            maxy = int( maxpos[ 1 ] // dy )
            maxz = int( maxpos[ 2 ] // dz )

            # Extraction of the grid
            extract = vtkExtractGrid()
            extract.SetInputData( data )
            extract.SetVOI( minx, maxx, miny, maxy, minz, maxz )
            extract.Update()
            dataExtract = extract.GetOutput()

        return dataExtract
