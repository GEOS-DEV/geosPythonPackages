# SPDX-FileContributor: Jacques Franc
# SPEDX-FileCopyrightText: Copyright 2023-2025 TotalEnergies
# SPDX-License-Identifier: Apache 2.0
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkPoints, vtkFloatArray
from vtkmodules.vtkFiltersGeneral import vtkOBBTree
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkMultiBlockDataSet, vtkDataObjectTreeIterator, vtkPolyData
from vtkmodules.vtkCommonTransforms import vtkLandmarkTransform
from vtkmodules.vtkFiltersGeneral import vtkTransformFilter

from geos.mesh.utils.genericHelpers import getMultiBlockBounds

import numpy as np
import logging

__doc__ = """Module to clip a mesh to the main frame using rigid body transformation.
Methods include:
    - ClipToMainFrame class to compute the transformation
    - ClipToMainFrameFilter class to apply the transformation to a mesh
"""


class ClipToMainFrame( vtkLandmarkTransform ):

    userTranslation: vtkFloatArray | None = None  # user provided translation
    sourcePts: vtkPoints
    targetPts: vtkPoints
    mesh: vtkUnstructuredGrid

    def __init__( self, mesh: vtkUnstructuredGrid ) -> None:
        """Clip mesh to main frame.

        Args:
            mesh (vtkUnstructuredGrid): mesh to clip.
        """
        super().__init__()
        self.mesh = mesh

    def Update( self ) -> None:
        """Update the transformation."""
        self.sourcePts, self.targetPts = self.__getFramePoints( self.__getOBBTree( self.mesh ) )
        self.SetSourceLandmarks( self.sourcePts )
        self.SetTargetLandmarks( self.targetPts )
        self.SetModeToRigidBody()
        super().Update()

    def SetUserTranslation( self, userTranslation: vtkFloatArray ) -> None:
        """Set the user translation.

        Args:
            userTranslation (vtkFloatArray): user translation to set.
        """
        self.userTranslation = userTranslation

    def GetUserTranslation( self ) -> vtkFloatArray | None:
        """Get the user translation.

        Returns:
            vtkFloatArray | None: user translation if set, None otherwise.
        """
        return self.userTranslation

    def __str__( self ) -> str:
        """String representation of the transformation."""
        return super().__str__() + f"\nUser translation: {self.userTranslation}" \
                  + f"\nSource points: {self.sourcePts}" \
                  + f"\nTarget points: {self.targetPts}" \
                  + f"\nAngle-Axis: {self.__getAngleAxis()}" \
                  + f"\nTranslation: {self._getTranslation()}"

    def __getAngleAxis( self ) -> tuple[ float, np.ndarray ]:
        """Get the angle and axis of the rotation.

        Returns:
            tuple[float, np.ndarray]: angle in degrees and axis of rotation.
        """
        matrix = self.GetMatrix()
        angle = np.arccos(
            ( matrix.GetElement( 0, 0 ) + matrix.GetElement( 1, 1 ) + matrix.GetElement( 2, 2 ) - 1 ) / 2 )
        if angle == 0:
            return 0.0, np.array( [ 1.0, 0.0, 0.0 ] )
        rx = matrix.GetElement( 2, 1 ) - matrix.GetElement( 1, 2 )
        ry = matrix.GetElement( 0, 2 ) - matrix.GetElement( 2, 0 )
        rz = matrix.GetElement( 1, 0 ) - matrix.GetElement( 0, 1 )
        r = np.array( [ rx, ry, rz ] )
        r /= np.linalg.norm( r )
        return np.degrees( angle ), r

    def _getTranslation( self ) -> np.ndarray:
        """Get the translation vector.

        Returns:
            np.ndarray: translation vector.
        """
        matrix = self.GetMatrix()
        return np.array( [ matrix.GetElement( 0, 3 ), matrix.GetElement( 1, 3 ), matrix.GetElement( 2, 3 ) ] )

    def __getOBBTree( self, mesh: vtkUnstructuredGrid ) -> vtkOBBTree:
        """Get the OBB tree of the mesh.

        Args:
            mesh (vtkUnstructuredGrid): mesh to get the OBB tree from.

        Returns:
            vtkOBBTree: OBB tree of the mesh.
        """
        OBBTree = vtkOBBTree()
        surfFilter = vtkDataSetSurfaceFilter()
        surfFilter.SetInputData( mesh )
        surfFilter.Update()
        OBBTree.SetDataSet( surfFilter.GetOutput() )
        OBBTree.BuildLocator()
        pdata = vtkPolyData()
        OBBTree.GenerateRepresentation( 0, pdata )
        # at level 0 this should return 8 corners of the bounding box
        if pdata.GetNumberOfPoints() < 3:
            logging.warning( "Could not get OBB points, using bounding box points instead" )
            return self.__allpoints( mesh.GetBounds() )

        return pdata.GetPoints()

    def __allpoints( self, bounds: tuple[ float, float, float, float, float, float ] ) -> vtkPoints:
        """Get the 8 corners of the bounding box.

        Args:
            bounds (tuple[float, float, float, float, float, float]): bounding box.

        Returns:
            vtkPoints: 8 corners of the bounding box.
        """
        pts = vtkPoints()
        pts.SetNumberOfPoints( 8 )
        pts.SetPoint( 0, [ bounds[ 0 ], bounds[ 2 ], bounds[ 4 ] ] )
        pts.SetPoint( 1, [ bounds[ 1 ], bounds[ 2 ], bounds[ 4 ] ] )
        pts.SetPoint( 2, [ bounds[ 1 ], bounds[ 3 ], bounds[ 4 ] ] )
        pts.SetPoint( 3, [ bounds[ 0 ], bounds[ 3 ], bounds[ 4 ] ] )
        pts.SetPoint( 4, [ bounds[ 0 ], bounds[ 2 ], bounds[ 5 ] ] )
        pts.SetPoint( 5, [ bounds[ 1 ], bounds[ 2 ], bounds[ 5 ] ] )
        pts.SetPoint( 6, [ bounds[ 1 ], bounds[ 3 ], bounds[ 5 ] ] )
        pts.SetPoint( 7, [ bounds[ 0 ], bounds[ 3 ], bounds[ 5 ] ] )
        return pts

    def __getFramePoints( self, vpts: vtkPoints ) -> tuple[ vtkPoints, vtkPoints ]:
        """Get the source and target points for the transformation.

        Args:
            vpts (vtkPoints): points to transform.

        Returns:
            tuple[vtkPoints, vtkPoints]: source and target points for the transformation.
        """
        pts = dsa.numpy_support.vtk_to_numpy( vpts.GetData() )
        further_ix = np.argmax( np.linalg.norm( pts, axis=1 ) )  # by default take the min point furthest from origin
        org = pts[ further_ix, : ]
        if self.userTranslation is not None:
            org = dsa.numpy_support.vtk_to_numpy( self.userTranslation )
            logging.info( "Using user translation" )
        logging.info( f"Moving point {org} to origin for transformation" )
        # find 3 orthogonal vectors
        # we assume points are on a box
        dist_indexes = np.argsort( np.linalg.norm( pts - org, axis=1 ) )
        # find u,v,w
        v1 = pts[ dist_indexes[ 1 ], : ] - org
        v1 /= np.linalg.norm( v1 )
        v2 = pts[ dist_indexes[ 2 ], : ] - org
        v2 /= np.linalg.norm( v2 )
        # ensure orthogonality
        v2 -= np.dot( v2, v1 ) * v1
        v2 /= np.linalg.norm( v2 )
        v3 = np.cross( v1, v2 )
        v3 /= np.linalg.norm( v3 )

        sourcePts = vtkPoints()
        sourcePts.SetNumberOfPoints( 4 )
        sourcePts.SetPoint( 0, org )
        sourcePts.SetPoint( 1, v1 + org )
        sourcePts.SetPoint( 2, v2 + org )
        sourcePts.SetPoint( 3, v3 + org )

        targetPts = vtkPoints()
        targetPts.SetNumberOfPoints( 4 )
        targetPts.SetPoint( 0, [ 0., 0., 0. ] )
        targetPts.SetPoint( 1, [ 1., 0., 0. ] )
        targetPts.SetPoint( 2, [ 0., 1., 0. ] )
        targetPts.SetPoint( 3, [ 0., 0., 1. ] )

        return ( sourcePts, targetPts )


class ClipToMainFrameFilter( vtkTransformFilter ):
    """Filter to clip a mesh to the main frame using ClipToMainFrame class."""

    userTranslation: vtkFloatArray | None = None  # user provided translation

    def SetUserTranslation( self, userTranslation: vtkFloatArray ) -> None:
        """Set the user translation.

        Args:
            userTranslation (vtkFloatArray): user translation to set.
        """
        self.userTranslation = userTranslation

    def GetUserTranslation( self ) -> vtkFloatArray | None:
        """Get the user translation.

        Returns:
            vtkFloatArray | None: user translation if set, None otherwise.
        """
        return self.userTranslation

    def Update( self ) -> None:
        """Update the transformation."""
        # dispatch to ClipToMainFrame depending on input type
        if isinstance( self.GetInput(), vtkMultiBlockDataSet ):
            #locate reference point
            idBlock = self.__locate_reference_point( self.GetInput(), self.userTranslation )
            clip = ClipToMainFrame( self.GetInput().GetBlock( idBlock - 1 ) )
        else:
            clip = ClipToMainFrame( self.GetInput() )

        clip.SetUserTranslation( self.userTranslation )
        clip.Update()
        self.SetTransform( clip )
        super().Update()

    def __locate_reference_point( self, input: vtkMultiBlockDataSet, userTranslation: vtkFloatArray | None ) -> int:
        """Locate the block to use as reference for the transformation.

        Args:
            input (vtkMultiBlockDataSet): input multiblock mesh.
            userTranslation (vtkFloatArray | None): if provided use this translation instead of the computed one.

        Returns:
            int: index of the block to use as reference.
        """

        def __inside( pt: np.ndarray, bounds: tuple[ float, float, float, float, float, float ] ) -> bool:
            """Check if a point is inside a bounding box.

            Args:
                pt (np.ndarray): point to check
                bounds (tuple[float, float, float, float, float, float]): bounding box.

            Returns:
                bool: True if the point is inside the bounding box, False otherwise.
            """
            logging.info( f"Checking if point {pt} is inside bounds {bounds}" )
            return ( pt[ 0 ] >= bounds[ 0 ] and pt[ 0 ] <= bounds[ 1 ] and pt[ 1 ] >= bounds[ 2 ]
                     and pt[ 1 ] <= bounds[ 3 ] and pt[ 2 ] >= bounds[ 4 ] and pt[ 2 ] <= bounds[ 5 ] )

        #TODO (jacques) make a decorator for this
        iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
        iter.SetDataSet( input )
        iter.VisitOnlyLeavesOn()
        iter.GoToFirstItem()
        xmin, _, ymin, _, zmin, _ = getMultiBlockBounds( input )
        #TODO (jacques) : rewrite with a filter struct
        while iter.GetCurrentDataObject() is not None:
            block: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast( iter.GetCurrentDataObject() )
            if block.GetNumberOfPoints() > 0:
                bounds = block.GetBounds()
                if userTranslation is not None:
                    #check if user translation is inside the block
                    if __inside( dsa.numpy_support.vtk_to_numpy( self.userTranslation ), bounds ):
                        logging.info( f"Using block {iter.GetCurrentFlatIndex()} as reference for transformation" )
                        return iter.GetCurrentFlatIndex()
                else:
                    #use the lowest bounds corner as reference point
                    if __inside( np.asarray( [ xmin, ymin, zmin ] ), bounds ):
                        logging.info( f"Using block {iter.GetCurrentFlatIndex()} as reference for transformation" )
                        return iter.GetCurrentFlatIndex()
            iter.GoToNextItem()
