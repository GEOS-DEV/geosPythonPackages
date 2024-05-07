import numpy as np
import functools

from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase, smproxy, smproperty, smdomain
from paraview.vtk import vtkIdTypeArray, vtkSelectionNode, vtkSelection, vtkCollection, vtkInformation, vtkDataObject
from paraview.vtk.util import numpy_support
from vtkmodules.util import vtkConstants

from checks import element_volumes, non_conformal


# #decorator
def extract_mesh( attr_key ):

    def mesh_decorator( func ):
        """Make a selected set from a list of points/face/cells"""

        @functools.wraps( func )
        def wrapper_extract_mesh( self, **kwargs ):
            res = func( self, **kwargs )
            inData = self.GetInputData( kwargs[ 'inInfo' ], 0, 0 )
            mesh = inData.NewInstance()
            mesh.DeepCopy( inData )
            maskArray = np.full( ( mesh.GetNumberOfCells(), ), 0 )
            for ix, _ in getattr( res, attr_key ):
                maskArray[ ix ] = 1

            print( f'There are {np.sum(maskArray)} cells under {self.opt} m3 vol' )
            insidedness = numpy_support.numpy_to_vtk( maskArray, deep=1, array_type=vtkConstants.VTK_SIGNED_CHAR )
            insidedness.SetName( attr_key )
            mesh.GetAttributes( vtkDataObject.CELL ).AddArray( insidedness )
            outData = self.GetOutputData( kwargs[ 'outInfo' ], 0 )
            kwargs[ 'outInfo' ].GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), mesh )

            return res

        return wrapper_extract_mesh

    return mesh_decorator


class BaseFilter( VTKPythonAlgorithmBase ):
    """
       Base Class refactoring filter construction
    """

    def __init__( self ):
        super().__init__( outputType='vtkUnstructuredGrid' )

    def RequestData( self, request: vtkInformation, inInfo: vtkInformation, outInfo: vtkInformation ):
        inData = self.GetInputData( inInfo, 0, 0 )
        outData = self.GetOutputData( outInfo, 0 )
        assert inData is not None
        if outData is None or ( not outData.IsA( inData.GetClassName() ) ):
            outData = inData.NewInstance()
        self._Process( inInfo=inInfo, outInfo=outInfo )

        print( "1> There are {} cells under {} vol".format( outData.GetNumberOfCells(), self.opt ) )
        return 1


@smproxy.filter( name="Mesh Doctor(GEOS) - Element Volume Filter" )
@smproperty.input( name="Input" )
@smdomain.datatype( dataTypes=[ "vtkUnstructuredGrid" ], composite_data_supported=False )
class ElementVolumeFilter( BaseFilter ):

    def __init__( self ):
        super().__init__()
        self.opt = element_volumes.Options( 0 )

    @extract_mesh( attr_key='element_volumes' )
    def _Process( self, inInfo: vtkInformation, outInfo: vtkInformation ):
        return element_volumes.check( self.GetInputData( inInfo, 0, 0 ), self.opt )

    @smproperty.doublevector( name="Vol Threshold", default_values=[ "0.0" ] )
    def SetValue( self, val: float ):
        self.opt = element_volumes.Options( min_volume=val )
        print( "Settings value:", self.opt )
        self.Modified()


@smproxy.filter( name="Mesh Doctor(GEOS) - NonConformal" )
@smproperty.input( name="Input" )
@smdomain.datatype( dataTypes=[ "vtkUnstructuredGrid" ], composite_data_supported=False )
class NonConformalFilter( BaseFilter ):

    def __init__( self ):
        super().__init__()
        self.opt = non_conformal.Options( 0, 0, 0 )

    @extract_mesh( attr_key='non_conformal_cells' )
    def _Process( self, inInfo: vtkInformation, outInfo: vtkInformation ):
        return non_conformal.check( self.GetInputData( inInfo, 0, 0 ), self.opt )

    @smproperty.doublevector( name="angle/point/face tol", default_values=[ "0.0", "0.0", "0.0" ] )
    def SetValue( self, angle: float, point: float, face: float ):
        self.opt = non_conformal.Options( angle_tolerance=angle, point_tolerance=point, face_tolerance=face )
        print( "Settings value:", self.opt )
        self.Modified()
