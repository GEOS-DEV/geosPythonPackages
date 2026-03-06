# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
import logging
import numpy as np
import numpy.typing as npt
from typing_extensions import Self, Union
from enum import Enum

from vtkmodules.vtkCommonDataModel import vtkCellData
from vtkmodules.util.numpy_support import vtk_to_numpy

from geos.utils.Logger import ( Logger, getLogger )

loggerTitle = "Profile Extractor"


class ProfileExtractor:

    def __init__( self: Self, logger: Union[ Logger, None ] = None ) -> None:
        """Utility class for extracting profiles along fault surfaces.

        Args:
            logger (Union[Logger, None], optional): A logger to manage the output messages.
                    Defaults to None, an internal logger is used.
        """
        # Logger
        self.logger: Logger
        if logger is None:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( f"{logger.name}" )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

    def extractAdaptiveProfile(
        self: Self,
        centers: npt.NDArray[ np.float64 ],
        values: npt.NDArray[ np.float64 ],
        xStart: float,
        yStart: float,
        zStart: float | None = None,
        stepSize: float = 20.0,
        maxSteps: int = 500,
        cellData: vtkCellData | None = None
    ) -> tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ],
                npt.NDArray[ np.float64 ] ]:
        """
        Extract a vertical depth profile with automatic fault detection.

        The algorithm adaptively follows a vertical sampling strategy guided by
        detected fault membership inside the provided cell data. It performs:

            1. Finding the closest starting point to the provided (xStart, yStart, zStart).
            2. Automatically detecting the target fault using the provided ``cellData``
                (e.g., fields like ``FaultMask`` or any other fault-identifying attribute).
            3. Filtering the dataset to keep **only cells belonging to that fault**.
            4. Splitting the remaining dataset into successive Z-depth slices.
            5. For each slice, selecting the nearest cell in the XY plane to build the
                final vertical profile.


        Args:
            centers (np.ndarray): Array of cell centers with shape ``(nCells, 3)``.
            values (np.ndarray): Scalar values associated with each cell (shape ``(nCells,)``).
            xStart (float or ndarray): Starting X coordinate.
            yStart (float or ndarray): Starting Y coordinate.
            zStart (float or ndarray | None): Starting Z coordinate. If ``None``, the method uses
                the highest point near the provided XY start position.
            stepSize (float): Vertical step size used when scanning depth layers.
                Default is 20.0.
            maxSteps (int): Maximum number of vertical layers to traverse.
                Default is 500.
            cellData (vtkCellData | None): VTK cell data object containing fields such as
                ``attribute``, ``FaultMask``, or other identifiers used to detect and filter
                the target fault.

        Returns:
            tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
                depth, profile values, X and Y coordinates of the profile path.
        """
        # Convert to np arrays
        centers = np.asarray( centers )
        values = np.asarray( values )

        if len( centers ) == 0:
            self.logger.warning( "        ⚠️ No cells provided" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        # ===================================================================
        # STEP 1 : Find starting point
        # ===================================================================

        if zStart is None:
            # Look in 2D (XY), take the highest values
            self.logger.info( f"        Searching near ({xStart:.1f}, {yStart:.1f})" )

            dXY = np.sqrt( ( centers[ :, 0 ] - xStart )**2 + ( centers[ :, 1 ] - yStart )**2 )
            closestIndices = np.argsort( dXY )[ :20 ]

            if len( closestIndices ) == 0:
                self.logger.warning( "        ⚠️ No cells found near start point" )
                return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

            # Take the highest Z value
            closestDepths = centers[ closestIndices, 2 ]
            startIdx = closestIndices[ np.argmax( closestDepths ) ]
        else:
            # Look in 3D
            self.logger.info( f"        Searching near ({xStart:.1f}, {yStart:.1f}, {zStart:.1f})" )

            d3D = np.sqrt( ( centers[ :, 0 ] - xStart )**2 + ( centers[ :, 1 ] - yStart )**2 +
                           ( centers[ :, 2 ] - zStart )**2 )
            startIdx = np.argmin( d3D )

        startPoint = centers[ startIdx ]

        self.logger.info( f"        Starting point: ({startPoint[0]:.1f}, {startPoint[1]:.1f}, {startPoint[2]:.1f})\n"
                          f"        Starting cell index: {startIdx}" )

        # ===================================================================
        # STEP 2: Auto-detection of target fault
        # ===================================================================
        faultIds = None
        targetFaultId = None

        if cellData is not None:
            faultFieldNames = [ 'attribute', 'FaultMask', 'faultId', 'region' ]

            for fieldName in faultFieldNames:
                if cellData.HasArray( fieldName ):
                    faultIds = vtk_to_numpy( cellData.GetArray( fieldName ) )

                    if len( faultIds ) != len( centers ):
                        self.logger.warning( f"        ⚠️ Field '{fieldName}' length mismatch, skipping" )
                        continue

                    # Get starting ID
                    targetFaultId = faultIds[ startIdx ]

                    uniqueIds = np.unique( faultIds )
                    self.logger.info( f"        Found fault field: '{fieldName}'\n"
                                      f"        Available fault IDs: {uniqueIds}\n"
                                      f"        Target fault ID at start point: {targetFaultId}\n" )

                    break

        # ===================================================================
        # STEP 3: Filter dataset to keep only fault cells
        # ===================================================================
        if targetFaultId is not None:
            maskSameFault = ( faultIds == targetFaultId )
            nTotal = len( centers )
            nOnFault = np.sum( maskSameFault )

            self.logger.info(
                f"        Filtering to fault ID={targetFaultId}: {nOnFault}/{nTotal} cells ({nOnFault/nTotal*100:.1f}%)"
            )

            if nOnFault == 0:
                self.logger.warning( "        ⚠️ No cells found on target fault" )
                return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

            # Replace centers and values by the filtered subset
            centers = centers[ maskSameFault ].copy()
            values = values[ maskSameFault ].copy()

            # Find new starting index in the subset
            dToStart = np.sqrt( np.sum( ( centers - startPoint )**2, axis=1 ) )
            startIdx = np.argmin( dToStart )

            self.logger.info( f"        ✅ Profile will stay on fault ID={targetFaultId}" )
        else:
            self.logger.warning( "        ⚠️ No fault identification field found" )
            if cellData is not None:
                fields = [ cellData.GetArrayName( i ) for i in range( cellData.GetNumberOfArrays() ) ]
                self.logger.info( f"        Available fields: {list(fields)}" )
            else:
                self.logger.warning( "        cellData not provided" )
            self.logger.warning( "        Profile may jump between faults!" )

        # ===================================================================
        # STEP 4: Z-slicing of the fault
        # ===================================================================

        refX = centers[ startIdx, 0 ]
        refY = centers[ startIdx, 1 ]

        self.logger.info( f"        Reference XY: ({refX:.1f}, {refY:.1f})" )

        # ===================================================================
        # STEP 5: Fault geometry
        # ===================================================================

        xRange = np.max( centers[ :, 0 ] ) - np.min( centers[ :, 0 ] )
        yRange = np.max( centers[ :, 1 ] ) - np.min( centers[ :, 1 ] )
        zRange = np.max( centers[ :, 2 ] ) - np.min( centers[ :, 2 ] )

        if zRange <= 0:
            self.logger.warning( f"        ⚠️ Invalid zRange: {zRange}" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        lateralExtent = max( xRange, yRange )
        xyTolerance = max( lateralExtent * 0.3, 100.0 )

        self.logger.info( f"        Fault extent: X={xRange:.1f}m, Y={yRange:.1f}m, Z={zRange:.1f}m"
                          f"        XY tolerance: {xyTolerance:.1f}m" )

        # ===================================================================
        # STEP 6: Slice computation
        # ===================================================================

        zCoordsSorted = np.sort( centers[ :, 2 ] )
        zDiffs = np.diff( zCoordsSorted )
        zDiffsPositive = zDiffs[ zDiffs > 1e-6 ]

        if len( zDiffsPositive ) == 0:
            self.logger.warning( "        ⚠️ All cells at same Z" )

            dXY = np.sqrt( ( centers[ :, 0 ] - refX )**2 + ( centers[ :, 1 ] - refY )**2 )
            sortedIndices = np.argsort( dXY )

            return ( centers[ sortedIndices, 2 ], values[ sortedIndices ], centers[ sortedIndices,
                                                                                    0 ], centers[ sortedIndices, 1 ] )

        medianZSpacing = np.median( zDiffsPositive )

        # Check that medianZSpacing is reasonable
        if medianZSpacing <= 0 or medianZSpacing > zRange:
            medianZSpacing = zRange / 100  # Fallback

        sliceThickness = medianZSpacing

        zMin = np.min( centers[ :, 2 ] )
        zMax = np.max( centers[ :, 2 ] )

        nSlices = int( np.ceil( zRange / sliceThickness ) )
        nSlices = min( nSlices, 10000 )  # Limit to 10k slices max

        if nSlices <= 0:
            self.logger.warning( f"        ⚠️ Invalid nSlices: {nSlices}" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        self.logger.info( f"        Median Z spacing: {medianZSpacing:.1f}m"
                          f"        Creating {nSlices} slices" )

        try:
            zSlices = np.linspace( zMax, zMin, nSlices + 1 )
        except ( MemoryError, ValueError ) as e:
            self.logger.error( f"        ⚠️ Error creating slices: {e}" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        # ===================================================================
        # STEP 7: Slice extraction
        # ===================================================================

        profileIndices = []

        for i in range( len( zSlices ) - 1 ):
            zTop = zSlices[ i ]
            zBottom = zSlices[ i + 1 ]

            # Cells in this slice
            maskInSlice = ( centers[ :, 2 ] <= zTop ) & ( centers[ :, 2 ] >= zBottom )
            indicesInSlice = np.where( maskInSlice )[ 0 ]

            if len( indicesInSlice ) == 0:
                continue

            # XY distance from reference
            dXYInSlice = np.sqrt( ( centers[ indicesInSlice, 0 ] - refX )**2 +
                                  ( centers[ indicesInSlice, 1 ] - refY )**2 )

            validMask = dXYInSlice < xyTolerance

            if not np.any( validMask ):
                closestInSlice = indicesInSlice[ np.argmin( dXYInSlice ) ]
            else:
                validIndices = indicesInSlice[ validMask ]
                dXYValid = dXYInSlice[ validMask ]
                closestInSlice = validIndices[ np.argmin( dXYValid ) ]

            profileIndices.append( closestInSlice )

        # ===================================================================
        # STEP 8: Delete duplicate and sort
        # ===================================================================
        seen = set()
        uniqueIndices = []
        for idx in profileIndices:
            if idx not in seen:
                seen.add( idx )
                uniqueIndices.append( idx )

        if len( uniqueIndices ) == 0:
            self.logger.warning( "        ⚠️ No points extracted" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        profileIndicesArr = np.array( uniqueIndices )

        # Sort by decreasing depth
        sortOrder = np.argsort( -centers[ profileIndicesArr, 2 ] )
        profileIndicesArr = profileIndicesArr[ sortOrder ]

        # Extract results
        depths = centers[ profileIndicesArr, 2 ]
        profileValues = values[ profileIndicesArr ]
        pathX = centers[ profileIndicesArr, 0 ]
        pathY = centers[ profileIndicesArr, 1 ]

        # ===================================================================
        # STATISTICS
        # ===================================================================
        depthCoverage = ( depths.max() - depths.min() ) / zRange * 100 if zRange > 0 else 0
        xyDisplacement = np.sqrt( ( pathX[ -1 ] - pathX[ 0 ] )**2 + ( pathY[ -1 ] - pathY[ 0 ] )**2 )

        self.logger.info( f"        ✅ Extracted {len(profileIndices)} points\n"
                          f"           Depth range: [{depths.max():.1f}, {depths.min():.1f}]m\n"
                          f"           Coverage: {depthCoverage:.1f}% of fault depth\n"
                          f"           XY displacement: {xyDisplacement:.1f}m\n" )

        return ( depths, profileValues, pathX, pathY )


class ProfileExtractorMethod( str, Enum ):
    """String Enum of profile extraction method."""
    VERTICAL_TOPO_BASED = "VerticalProfileTopologyBased"
    ADAPTATIVE = "AdaptativeProfile"
