# SPDX-License-Identifier: Apache 2.0
# SPDX-FileCopyrightText: Copyright 2023-2025 TotalEnergies
# SPDX-FileContributor: Jacques Franc

from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkFiltersGeneral import vtkOBBTree
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkMultiBlockDataSet, vtkDataObjectTreeIterator, vtkPolyData
from vtkmodules.vtkCommonTransforms import vtkLandmarkTransform
from vtkmodules.vtkFiltersGeneral import vtkTransformFilter

from geos.mesh.utils.genericHelpers import getMultiBlockBounds

import numpy as np
import logging

__doc__ = """
Module to clip a mesh to the main frame using rigid body transformation.

Methods include:
    - ClipToMainFrameElement class to compute the transformation
    - ClipToMainFrame class to apply the transformation to a mesh

To use it:

.. code-block:: python

    from geos.mesh.processing.ClipToMainFrame import ClipToMainFrame

    # Filter inputs.
    multiBlockDataSet: vtkMultiBlockDataSet

    # Instantiate the filter.
    filter: ClipToMainFrame = ClipToMainFrame()
    filter.SetInputData( multiBlockDataSet )

    # Do calculations.
    filter.Update()
    output: vtkMultiBlockDataSet = filter.GetOutput()

"""


class ClipToMainFrameElement( vtkLandmarkTransform ):

    sourcePts: vtkPoints
    targetPts: vtkPoints
    mesh: vtkUnstructuredGrid

    def __init__( self, mesh: vtkUnstructuredGrid ) -> None:
        """Clip mesh to main frame.

        Args:
            mesh (vtkUnstructuredGrid): Mesh to clip.
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

    def __str__( self ) -> str:
        """String representation of the transformation."""
        return super().__str__() + f"\nSource points: {self.sourcePts}" \
                  + f"\nTarget points: {self.targetPts}" \
                  + f"\nAngle-Axis: {self.__getAngleAxis()}" \
                  + f"\nTranslation: {self._getTranslation()}"

    def __getAngleAxis( self ) -> tuple[ float, np.ndarray ]:
        """Get the angle and axis of the rotation.

        Returns:
            tuple[float, np.ndarray]: Angle in degrees and axis of rotation.
        """
        matrix : vtkMatrix4x4 = self.GetMatrix()
        angle : np.ndarray = np.arccos(
            ( matrix.GetElement( 0, 0 ) + matrix.GetElement( 1, 1 ) + matrix.GetElement( 2, 2 ) - 1 ) / 2 )
        if angle == 0:
            return 0.0, np.array( [ 1.0, 0.0, 0.0 ] )
        rx : float = matrix.GetElement( 2, 1 ) - matrix.GetElement( 1, 2 )
        ry : float = matrix.GetElement( 0, 2 ) - matrix.GetElement( 2, 0 )
        rz : float = matrix.GetElement( 1, 0 ) - matrix.GetElement( 0, 1 )
        r = np.array( [ rx, ry, rz ] )
        r /= np.linalg.norm( r )
        return np.degrees( angle ), r

    def _getTranslation( self ) -> np.ndarray:
        """Get the translation vector.

        Returns:
            np.ndarray: The translation vector.
        """
        matrix = self.GetMatrix()
        return np.array( [ matrix.GetElement( 0, 3 ), matrix.GetElement( 1, 3 ), matrix.GetElement( 2, 3 ) ] )

    def __getOBBTree( self, mesh: vtkUnstructuredGrid ) -> vtkPoints:
        """Get the OBB tree of the mesh.

        Args:
            mesh (vtkUnstructuredGrid): Mesh to get the OBB tree from.

        Returns:
            vtkPoints: Points from the 0-level OBB tree of the mesh. Fallback on Axis Aligned Bounding Box
        """
        OBBTree = vtkOBBTree()
        surfFilter = vtkDataSetSurfaceFilter()
        surfFilter.SetInputData( mesh )
        surfFilter.Update()
        OBBTree.SetDataSet( surfFilter.GetOutput() )
        OBBTree.BuildLocator()
        pdata = vtkPolyData()
        OBBTree.GenerateRepresentation( 0, pdata )
        # at level 0 this should return 8 corners of the bounding box or fallback on AABB
        if pdata.GetNumberOfPoints() < 3:
            logging.warning( "Could not get OBB points, using bounding box points instead" )
            return self.__allpoints( mesh.GetBounds() )

        return pdata.GetPoints()

    def __allpoints( self, bounds: tuple[ float, float, float, float, float, float ] ) -> vtkPoints:
        """Get the 8 corners of the bounding box.

        Args:
            bounds (tuple[float, float, float, float, float, float]): Bounding box.

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

    # def _translateToNegQuadrant(self, )

    def __getFramePoints( self, vpts: vtkPoints ) -> tuple[ vtkPoints, vtkPoints ]:
        """Get the source and target points for the transformation.

        Args:
            vpts (vtkPoints): Points to transform.

        Returns:
            tuple[vtkPoints, vtkPoints]: Source and target points for the transformation.
        """
        pts = dsa.numpy_support.vtk_to_numpy( vpts.GetData() )
        #translate pts so they always lie on the -z,-y,-x quadrant
        off = np.asarray( [
            -2 * np.amax( np.abs( pts[ :, 0 ] ) ), -2 * np.amax( np.abs( pts[ :, 1 ] ) ),
            -2 * np.amax( np.abs( pts[ :, 2 ] ) )
        ] )
        pts += off
        further_ix = np.argmax( np.linalg.norm( pts, axis=1 ) )  # by default take the min point furthest from origin
        org = pts[ further_ix, : ]

        logging.info( f"Moving point {org} to origin for transformation" )
        # find 3 orthogonal vectors
        # we assume points are on a box
        dist_indexes = np.argsort( np.linalg.norm( pts - org, axis=1 ) )
        # find u,v,w
        v1 = pts[ dist_indexes[ 1 ], : ] - org
        v2 = pts[ dist_indexes[ 2 ], : ] - org
        v1 /= np.linalg.norm( v1 )
        v2 /= np.linalg.norm( v2 )
        if np.abs( v1[ 0 ] ) > np.abs( v2[ 0 ] ):
            v1, v2 = v2, v1

        # ensure orthogonality
        v2 -= np.dot( v2, v1 ) * v1
        v2 /= np.linalg.norm( v2 )
        v3 = np.cross( v1, v2 )
        v3 /= np.linalg.norm( v3 )

        #reorder axis if v3 points downward
        if v3[ 2 ] < 0:
            v3 = -v3
            v1, v2 = v2, v1

        sourcePts = vtkPoints()
        sourcePts.SetNumberOfPoints( 4 )
        sourcePts.SetPoint( 0, org - off )
        sourcePts.SetPoint( 1, v1 + org - off )
        sourcePts.SetPoint( 2, v2 + org - off )
        sourcePts.SetPoint( 3, v3 + org - off )

        targetPts = vtkPoints()
        targetPts.SetNumberOfPoints( 4 )
        targetPts.SetPoint( 0, [ 0., 0., 0. ] )
        targetPts.SetPoint( 1, [ 1., 0., 0. ] )
        targetPts.SetPoint( 2, [ 0., 1., 0. ] )
        targetPts.SetPoint( 3, [ 0., 0., 1. ] )

        return ( sourcePts, targetPts )


class ClipToMainFrame( vtkTransformFilter ):
    """Filter to clip a mesh to the main frame using ClipToMainFrame class."""

    def Update( self ) -> None:
        """Update the transformation."""
        # dispatch to ClipToMainFrame depending on input type
        if isinstance( self.GetInput(), vtkMultiBlockDataSet ):
            #locate reference point
            idBlock = self.__locate_reference_point( self.GetInput())
            clip = ClipToMainFrameElement( self.GetInput().GetDataSet( idBlock ) )
        else:
            clip = ClipToMainFrameElement( self.GetInput() )

        clip.Update()
        self.SetTransform( clip )
        super().Update()

    def __locate_reference_point( self, input: vtkMultiBlockDataSet ) -> int:
        """Locate the block to use as reference for the transformation.

        Args:
            input (vtkMultiBlockDataSet): Input multiblock mesh.

        Returns:
            int: Index of the block to use as reference.
        """

        def __inside( pt: np.ndarray, bounds: tuple[ float, float, float, float, float, float ] ) -> bool:
            """Check if a point is inside a bounding box.

            Args:
                pt (np.ndarray): Point to check
                bounds (tuple[float, float, float, float, float, float]): Bounding box.

            Returns:
                bool: True if the point is inside the bounding box, False otherwise.
            """
            logging.info( f"Checking if point {pt} is inside bounds {bounds}" )
            return ( pt[ 0 ] >= bounds[ 0 ] and pt[ 0 ] <= bounds[ 1 ] and pt[ 1 ] >= bounds[ 2 ]
                     and pt[ 1 ] <= bounds[ 3 ] and pt[ 2 ] >= bounds[ 4 ] and pt[ 2 ] <= bounds[ 5 ] )

        #TODO (jacques) make a decorator for this
        DOIterator: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
        DOIterator.SetDataSet( input )
        DOIterator.VisitOnlyLeavesOn()
        DOIterator.GoToFirstItem()
        xmin, _, ymin, _, zmin, _ = getMultiBlockBounds( input )
        #TODO (jacques) : rewrite with a filter struct
        while DOIterator.GetCurrentDataObject() is not None:
            block: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast( DOIterator.GetCurrentDataObject() )
            if block.GetNumberOfPoints() > 0:
                bounds = block.GetBounds()

                #use the furthest bounds corner as reference point in the all negs quadrant
                if __inside( np.asarray( [ xmin, ymin, zmin ] ), bounds ):
                    logging.info( f"Using block {DOIterator.GetCurrentFlatIndex()} as reference for transformation" )
                    return DOIterator.GetCurrentFlatIndex()
            DOIterator.GoToNextItem()
