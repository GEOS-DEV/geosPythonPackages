# SPDX-FileContributor: Jacques Franc 
# SPEDX-FileCopyrightText: Copyright 2023-2025 TotalEnergies 
# SPDX-License-Identifier: Apache 2.0
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkFloatArray, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersGeneral import vtkTransformFilter
import numpy as np
import logging


class ClipToMainFrame( vtkTransform ):

    userTranslation: vtkFloatArray | None = None  # user provided translation
    pts: vtkPoints

    def __init__( self, pts: vtkPoints ) -> None:
        """Clip mesh to main frame
        Args:            userTranslation (vtkFloatArray | None): if provided use this translation instead of the computed one
        
        """
        super().__init__()
        self.pts = pts

    def Update( self ) -> None:
        """Update the transformation"""
        self.__transform( self.pts, self.userTranslation )
        super().Update()

    def SetUserTranslation( self, userTranslation: vtkFloatArray ) -> None:
        """Set the user translation
        Args:
            userTranslation (vtkFloatArray): user translation to set
        """
        self.userTranslation = userTranslation

    def GetUserTranslation( self ) -> vtkFloatArray | None:
        """Get the user translation
        Returns:
            vtkFloatArray | None: user translation if set, None otherwise
        """
        return self.userTranslation

    def __transform( self, pts: vtkPoints, userTranslation: vtkFloatArray | None = None ) -> None:
        """Apply the transformation to the points
        Args:
            pts (vtkPoints): points to transform
            userTranslation (vtkFloatArray | None, optional): if provided use this translation instead of the computed one. Defaults to None.
        """
        translation, theta, axis = self.__recenter_and_rotate( dsa.numpy_support.vtk_to_numpy( pts.GetData() ) )

        if userTranslation is not None:
            translation = dsa.numpy_support.vtk_to_numpy( userTranslation )
            logging.info( "Using user translation" )

        self.PostMultiply()  # we want to apply rotation then translation
        self.RotateWXYZ( -theta, axis[ 0 ], axis[ 1 ], axis[ 2 ] )
        self.Translate( -translation[ 0 ], -translation[ 1 ], -translation[ 2 ] )

        logging.info( f"Using translation {translation}" )
        logging.info( f"Theta {theta}" )
        logging.info( f"Axis {axis}" )

    def __local_frame( self, pts: np.ndarray ) -> tuple[ np.ndarray, np.ndarray, np.ndarray ]:
        """Find a local frame for a set of points
        Args:
            pts (np.ndarray): points to find the local frame of
        Returns:
            tuple[np.ndarray, np.ndarray, np.ndarray]: three orthogonal vectors defining the local frame
        """
        # find 3 orthogonal vectors
        # we assume points are on a box
        # first vector is along x axis
        ori, _, _ = self.__origin_bounding_box( pts )
        u = pts[ 1 ]
        v = u
        for pt in pts[ 2: ]:  # As we assume points are on a box there should be one orthogonal to u
            if ( np.abs( np.dot( u, pt ) ) < 1e-10 ):
                v = pt
                break

        return ( u, v, np.cross( u, v ) )

        # utils
    def __origin_bounding_box( self, pts: np.ndarray ) -> tuple[ np.ndarray, np.ndarray, np.ndarray ]:
        """Find the bounding box of a set of points
        Args:
            pts (np.ndarray): points to find the bounding box of
        Returns:
            tuple[np.ndarray, np.ndarray, np.ndarray]: origin, min, max of the bounding box
        """
        pt0 = pts[ np.argmin( pts, axis=0 ), : ]
        pt1 = pts[ np.argmax( pts, axis=0 ), : ]

        return ( pts[ 0 ], pt0, pt1 )

    def __recenter_and_rotate( self, pts: np.ndarray ) -> tuple[ np.ndarray, float, np.ndarray ]:
        """Recenter and rotate points to align with principal axes
        
        Args:
            pts (np.ndarray): points to recenter and rotate
        """
        # find bounding box
        org, vmin, vmax = self.__origin_bounding_box( pts )
        logging.info( f"Bounding box is {org}, {vmin}, {vmax}" )

        # Transformation
        translation = org
        pts -= translation

        u, v, w = self.__local_frame( pts )
        logging.info( f"Local frame u {u}, v {v}, w {w}" )

        # find rotation R = U sig V
        rotation = np.asarray( [ u / np.linalg.norm( u ), v / np.linalg.norm( v ), w / np.linalg.norm( w ) ],
                               dtype=np.float64 ).transpose()
        logging.info( f"R {rotation}" )

        theta = np.acos( .5 * ( np.trace( rotation ) - 1 ) ) * 180 / np.pi
        logging.info( f"Theta {theta}" )

        axis = np.asarray( [
            rotation[ 2, 1 ] - rotation[ 1, 2 ], rotation[ 0, 2 ] - rotation[ 2, 0 ],
            rotation[ 1, 0 ] - rotation[ 0, 1 ]
        ],
                           dtype=np.float64 )
        axis /= np.linalg.norm( axis )

        pts = ( rotation.transpose() @ pts.transpose() ).transpose()
        pts[ np.abs( pts ) < 1e-15 ] = 0.  # clipping points too close to zero

        # return translation, rotation, pts
        return translation, theta, axis


class ClipToMainFrameFilter( vtkTransformFilter ):

    userTranslation: vtkFloatArray | None = None  # user provided translation

    def SetUserTranslation( self, userTranslation: vtkFloatArray ) -> None:
        """Set the user translation
        Args:
            userTranslation (vtkFloatArray): user translation to set
        """
        self.userTranslation = userTranslation

    def GetUserTranslation( self ) -> vtkFloatArray | None:
        """Get the user translation
        Returns:
            vtkFloatArray | None: user translation if set, None otherwise
        """
        return self.userTranslation

    def SetInputData( self, input: vtkUnstructuredGrid ) -> None:
        """Set the input data and apply the transformation to it
        Args:
            input (vtkUnstructuredGrid): input mesh to transform
        """
        super().SetInputData( input )
        clip = ClipToMainFrame( input.GetPoints() )
        clip.SetUserTranslation( self.userTranslation )
        clip.Update()
        self.SetTransform( clip )
