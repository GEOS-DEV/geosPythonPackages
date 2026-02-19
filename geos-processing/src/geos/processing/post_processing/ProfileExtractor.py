# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
import numpy as np
import pyvista as pv
import numpy.typing as npt

from vtkmodules.vtkCommonDataModel import vtkCellData, vtkDataSet
from vtkmodules.util.numpy_support import vtk_to_numpy

# ============================================================================
# PROFILE EXTRACTOR
# ============================================================================
class ProfileExtractor:
    """Utility class for extracting profiles along fault surfaces."""

    # -------------------------------------------------------------------
    @staticmethod
    def extractAdaptiveProfile(
        centers: npt.NDArray[ np.float64 ],
        values: npt.NDArray[ np.float64 ],
        xStart: npt.NDArray[ np.float64 ],
        yStart: npt.NDArray[ np.float64 ],
        zStart: npt.NDArray[ np.float64 ] | None = None,
        searchRadius: float | None = None,
        stepSize: float = 20.0,
        maxSteps: float = 500,
        verbose: bool = True,
        cellData: vtkCellData = None
    ) -> tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ],
                npt.NDArray[ np.float64 ] ]:
        """Extraction de profil vertical par COUCHES DE PROFONDEUR avec détection automatique de faille.

        Stratégie:
        1. Trouver le point de départ le plus proche
        2. Identifier automatiquement la faille via cellData (attribute, FaultMask, etc.)
        3. FILTRER pour ne garder QUE les cellules de cette faille
        4. Diviser en tranches Z
        5. Pour chaque tranche, prendre la cellule la plus proche en XY

        Parameters
        ----------
        centers : ndarray
            Cell centers (nCells, 3)
        values : ndarray
            Values at cells (nCells,)
        xStart, yStart : float
            Starting XY position
        zStart : float, optional
            Starting Z position (if None, uses highest point near XY)
        searchRadius : float, optional
            Not used (kept for compatibility)
        cellData : dict, optional
            Dictionary with cell data fields (e.g., {'attribute': array, 'FaultMask': array})
            Used to automatically detect and filter by fault ID
        verbose : bool
            Print detailed information

        Returns:
        -------
        depths, profileValues, pathX, pathY : ndarrays
            Extracted profile data
        """
        # Convert to np arrays
        centers = np.asarray( centers )
        values = np.asarray( values )

        if len( centers ) == 0:
            if verbose:
                print( "        ⚠️ No cells provided" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        # ===================================================================
        # ÉTAPE 1: TROUVER LE POINT DE DÉPART
        # ===================================================================

        if zStart is None:
            # Chercher en 2D (XY), prendre le plus haut
            if verbose:
                print( f"        Searching near ({xStart:.1f}, {yStart:.1f})" )

            dXY = np.sqrt( ( centers[ :, 0 ] - xStart )**2 + ( centers[ :, 1 ] - yStart )**2 )
            closestIndices = np.argsort( dXY )[ :20 ]

            if len( closestIndices ) == 0:
                print( "        ⚠️ No cells found near start point" )
                return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

            # Prendre le plus haut (plus grand Z)
            closestDepths = centers[ closestIndices, 2 ]
            startIdx = closestIndices[ np.argmax( closestDepths ) ]
        else:
            # Chercher en 3D
            if verbose:
                print( f"        Searching near ({xStart:.1f}, {yStart:.1f}, {zStart:.1f})" )

            d3D = np.sqrt( ( centers[ :, 0 ] - xStart )**2 + ( centers[ :, 1 ] - yStart )**2 +
                           ( centers[ :, 2 ] - zStart )**2 )
            startIdx = np.argmin( d3D )

        startPoint = centers[ startIdx ]

        if verbose:
            print( f"        Starting point: ({startPoint[0]:.1f}, {startPoint[1]:.1f}, {startPoint[2]:.1f})" )
            print( f"        Starting cell index: {startIdx}" )

        # ===================================================================
        # ÉTAPE 2: DÉTECTER AUTOMATIQUEMENT L'ID DE LA FAILLE
        # ===================================================================

        faultIds = None
        targetFaultId = None

        if cellData is not None:
            # Chercher dans l'ordre de priorité
            faultFieldNames = [ 'attribute', 'FaultMask', 'faultId', 'region' ]

            for fieldName in faultFieldNames:
                if cellData.HasArray( fieldName ):
                    faultIds = vtk_to_numpy( cellData[ fieldName ] )


                    if len( faultIds ) != len( centers ):
                        if verbose:
                            print( f"        ⚠️ Field '{fieldName}' length mismatch, skipping" )
                        continue

                    # Récupérer l'ID au point de départ
                    targetFaultId = faultIds[ startIdx ]

                    if verbose:
                        uniqueIds = np.unique( faultIds )
                        print( f"        Found fault field: '{fieldName}'" )
                        print( f"        Available fault IDs: {uniqueIds}" )
                        print( f"        Target fault ID at start point: {targetFaultId}" )

                    break

        # ===================================================================
        # ÉTAPE 3: FILTRER PAR FAILLE SI DÉTECTÉE
        # ===================================================================

        if targetFaultId is not None:
            # FILTRER: garder SEULEMENT cette faille
            maskSameFault = ( faultIds == targetFaultId )
            nTotal = len( centers )
            nOnFault = np.sum( maskSameFault )

            if verbose:
                print(
                    f"        Filtering to fault ID={targetFaultId}: {nOnFault}/{nTotal} cells ({nOnFault/nTotal*100:.1f}%)"
                )

            if nOnFault == 0:
                print( "        ⚠️ No cells found on target fault" )
                return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

            # REMPLACER centers et values par le subset filtré
            centers = centers[ maskSameFault ].copy()
            values = values[ maskSameFault ].copy()

            # Trouver le nouvel index de départ dans le subset
            dToStart = np.sqrt( np.sum( ( centers - startPoint )**2, axis=1 ) )
            startIdx = np.argmin( dToStart )

            if verbose:
                print( f"        ✅ Profile will stay on fault ID={targetFaultId}" )
        else:
            if verbose:
                print( "        ⚠️ No fault identification field found" )
                if cellData is not None:
                    print( f"        Available fields: {list(cellData.keys())}" )
                else:
                    print( "        cellData not provided" )
                print( "        Profile may jump between faults!" )

        # À partir d'ici, centers/values ne contiennent QUE la faille cible

        # ===================================================================
        # ÉTAPE 4: POSITION DE RÉFÉRENCE
        # ===================================================================

        refX = centers[ startIdx, 0 ]
        refY = centers[ startIdx, 1 ]

        if verbose:
            print( f"        Reference XY: ({refX:.1f}, {refY:.1f})" )

        # ===================================================================
        # ÉTAPE 5: GÉOMÉTRIE DE LA FAILLE
        # ===================================================================

        xRange = np.max( centers[ :, 0 ] ) - np.min( centers[ :, 0 ] )
        yRange = np.max( centers[ :, 1 ] ) - np.min( centers[ :, 1 ] )
        zRange = np.max( centers[ :, 2 ] ) - np.min( centers[ :, 2 ] )

        if zRange <= 0:
            print( f"        ⚠️ Invalid zRange: {zRange}" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        lateralExtent = max( xRange, yRange )
        xyTolerance = max( lateralExtent * 0.3, 100.0 )

        if verbose:
            print( f"        Fault extent: X={xRange:.1f}m, Y={yRange:.1f}m, Z={zRange:.1f}m" )
            print( f"        XY tolerance: {xyTolerance:.1f}m" )

        # ===================================================================
        # ÉTAPE 6: CALCUL DES TRANCHES
        # ===================================================================

        zCoordsSorted = np.sort( centers[ :, 2 ] )
        zDiffs = np.diff( zCoordsSorted )
        zDiffsPositive = zDiffs[ zDiffs > 1e-6 ]

        if len( zDiffsPositive ) == 0:
            if verbose:
                print( "        ⚠️ All cells at same Z" )

            dXY = np.sqrt( ( centers[ :, 0 ] - refX )**2 + ( centers[ :, 1 ] - refY )**2 )
            sortedIndices = np.argsort( dXY )

            return ( centers[ sortedIndices, 2 ], values[ sortedIndices ], centers[ sortedIndices,
                                                                                    0 ], centers[ sortedIndices, 1 ] )

        medianZSpacing = np.median( zDiffsPositive )

        # Vérifier que medianZSpacing est raisonnable
        if medianZSpacing <= 0 or medianZSpacing > zRange:
            medianZSpacing = zRange / 100  # Fallback

        # Taille de tranche = espacement médian
        sliceThickness = medianZSpacing

        zMin = np.min( centers[ :, 2 ] )
        zMax = np.max( centers[ :, 2 ] )

        nSlices = int( np.ceil( zRange / sliceThickness ) )
        nSlices = min( nSlices, 10000 )  # Limiter à 10k tranches max

        if nSlices <= 0:
            print( f"        ⚠️ Invalid nSlices: {nSlices}" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        if verbose:
            print( f"        Median Z spacing: {medianZSpacing:.1f}m" )
            print( f"        Creating {nSlices} slices" )

        try:
            zSlices = np.linspace( zMax, zMin, nSlices + 1 )
        except ( MemoryError, ValueError ) as e:
            print( f"        ⚠️ Error creating slices: {e}" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        # ===================================================================
        # ÉTAPE 7: EXTRACTION PAR TRANCHES
        # ===================================================================

        profileIndices = []

        for i in range( len( zSlices ) - 1 ):
            zTop = zSlices[ i ]
            zBottom = zSlices[ i + 1 ]

            # Cellules dans cette tranche
            maskInSlice = ( centers[ :, 2 ] <= zTop ) & ( centers[ :, 2 ] >= zBottom )
            indicesInSlice = np.where( maskInSlice )[ 0 ]

            if len( indicesInSlice ) == 0:
                continue

            # Distance XY à la référence
            dXYInSlice = np.sqrt( ( centers[ indicesInSlice, 0 ] - refX )**2 +
                                  ( centers[ indicesInSlice, 1 ] - refY )**2 )

            # Ne garder que celles dans la tolérance XY
            validMask = dXYInSlice < xyTolerance

            if not np.any( validMask ):
                # Aucune dans la tolérance → prendre la plus proche
                closestInSlice = indicesInSlice[ np.argmin( dXYInSlice ) ]
            else:
                # Prendre la plus proche parmi celles dans la tolérance
                validIndices = indicesInSlice[ validMask ]
                dXYValid = dXYInSlice[ validMask ]
                closestInSlice = validIndices[ np.argmin( dXYValid ) ]

            profileIndices.append( closestInSlice )

        # ===================================================================
        # ÉTAPE 8: SUPPRIMER DOUBLONS ET TRIER
        # ===================================================================

        # Supprimer doublons
        seen = set()
        uniqueIndices = []
        for idx in profileIndices:
            if idx not in seen:
                seen.add( idx )
                uniqueIndices.append( idx )

        if len( uniqueIndices ) == 0:
            if verbose:
                print( "        ⚠️ No points extracted" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        profileIndicesArr = np.array( uniqueIndices )

        # Trier par profondeur décroissante (haut → bas)
        sortOrder = np.argsort( -centers[ profileIndicesArr, 2 ] )
        profileIndicesArr = profileIndicesArr[ sortOrder ]

        # Extraire résultats
        depths = centers[ profileIndicesArr, 2 ]
        profileValues = values[ profileIndicesArr ]
        pathX = centers[ profileIndicesArr, 0 ]
        pathY = centers[ profileIndicesArr, 1 ]

        # ===================================================================
        # STATISTIQUES
        # ===================================================================

        if verbose:
            depthCoverage = ( depths.max() - depths.min() ) / zRange * 100 if zRange > 0 else 0
            xyDisplacement = np.sqrt( ( pathX[ -1 ] - pathX[ 0 ] )**2 + ( pathY[ -1 ] - pathY[ 0 ] )**2 )

            print( f"        ✅ Extracted {len(profileIndices)} points" )
            print( f"           Depth range: [{depths.max():.1f}, {depths.min():.1f}]m" )
            print( f"           Coverage: {depthCoverage:.1f}% of fault depth" )
            print( f"           XY displacement: {xyDisplacement:.1f}m" )

        return ( depths, profileValues, pathX, pathY )

    # -------------------------------------------------------------------
    @staticmethod
    def extractVerticalProfileTopologyBased(
        surfaceMesh: pv.DataSet,
        fieldName: str,
        xStart: float,
        yStart: float,
        zStart: float | None = None,
        maxSteps: int = 500,
        verbose: bool = True
    ) -> tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ],
                npt.NDArray[ np.float64 ] ]:
        """Extraction de profil vertical en utilisant la TOPOLOGIE du maillage de surface."""
        if fieldName not in surfaceMesh.cell_data:
            print( f"        ⚠️ Field '{fieldName}' not found in mesh" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        centers = surfaceMesh.cell_centers().points
        values = surfaceMesh.cell_data[ fieldName ]

        # ===================================================================
        # ÉTAPE 1: TROUVER LA CELLULE DE DÉPART
        # ===================================================================

        if zStart is None:
            if verbose:
                print( f"        Searching near ({xStart:.1f}, {yStart:.1f})" )

            dXY = np.sqrt( ( centers[ :, 0 ] - xStart )**2 + ( centers[ :, 1 ] - yStart )**2 )
            closestIndices = np.argsort( dXY )[ :20 ]

            if len( closestIndices ) == 0:
                print( "        ⚠️ No cells found" )
                return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

            closestDepths = centers[ closestIndices, 2 ]
            startIdx = closestIndices[ np.argmax( closestDepths ) ]
        else:
            if verbose:
                print( f"        Searching near ({xStart:.1f}, {yStart:.1f}, {zStart:.1f})" )

            d3D = np.sqrt( ( centers[ :, 0 ] - xStart )**2 + ( centers[ :, 1 ] - yStart )**2 +
                           ( centers[ :, 2 ] - zStart )**2 )
            startIdx = np.argmin( d3D )

        startPoint = centers[ startIdx ]

        if verbose:
            print( f"        Starting cell: {startIdx}" )
            print( f"        Starting point: ({startPoint[0]:.1f}, {startPoint[1]:.1f}, {startPoint[2]:.1f})" )

        # ===================================================================
        # ÉTAPE 2: IDENTIFIER LA FAILLE
        # ===================================================================

        targetFaultId = None
        faultIds = None
        faultFieldNames = [ 'attribute', 'FaultMask', 'faultId', 'region' ]

        for fieldNameCheck in faultFieldNames:
            if fieldNameCheck in surfaceMesh.cell_data:
                faultIds = surfaceMesh.cell_data[ fieldNameCheck ]
                targetFaultId = faultIds[ startIdx ]

                if verbose:
                    uniqueIds = np.unique( faultIds )
                    print( f"        Fault field: '{fieldNameCheck}'" )
                    print( f"        Target fault ID: {targetFaultId} (from {uniqueIds})" )

                break

        if targetFaultId is None and verbose:
            print( "        ⚠️ No fault ID found - will use all cells" )

        # ===================================================================
        # ÉTAPE 3: CONSTRUIRE LA CONNECTIVITÉ (VOISINS TOPOLOGIQUES)
        # ===================================================================

        if verbose:
            print( "        Building cell connectivity..." )

        nCells = surfaceMesh.n_cells
        connectivity: list[ list[ int ] ] = [ [] for _ in range( nCells ) ]

        # Construire un dictionnaire arête -> cellules
        edgeToCells: dict[ tuple[ int, int ], list[ int ] ] = {}

        for cellId in range( nCells ):
            cell = surfaceMesh.get_cell( cellId )
            nPoints = cell.n_points

            # Pour chaque arête de la cellule
            for i in range( nPoints ):
                p1 = cell.point_ids[ i ]
                p2 = cell.point_ids[ ( i + 1 ) % nPoints ]

                # Arête normalisée (ordre canonique)
                edge = tuple( sorted( [ p1, p2 ] ) )

                if edge not in edgeToCells:
                    edgeToCells[ edge ] = []
                edgeToCells[ edge ].append( cellId )

        # Pour chaque cellule, trouver ses voisins via arêtes partagées
        for cellId in range( nCells ):
            cell = surfaceMesh.get_cell( cellId )
            nPoints = cell.n_points

            neighborsSet = set()

            for i in range( nPoints ):
                p1 = cell.point_ids[ i ]
                p2 = cell.point_ids[ ( i + 1 ) % nPoints ]
                edge = tuple( sorted( [ p1, p2 ] ) )

                # Toutes les cellules partageant cette arête sont voisines
                for neighborId in edgeToCells[ edge ]:
                    if neighborId != cellId:
                        neighborsSet.add( neighborId )

            connectivity[ cellId ] = list( neighborsSet )

        if verbose:
            avgNeighbors = np.mean( [ len( c ) for c in connectivity ] )
            maxNeighbors = np.max( [ len( c ) for c in connectivity ] )
            print( f"        Connectivity built: avg={avgNeighbors:.1f} neighbors/cell, max={maxNeighbors}" )

        # ===================================================================
        # ÉTAPE 4: ALGORITHME DE DESCENTE PAR VOISINAGE TOPOLOGIQUE
        # ===================================================================

        profileIndices = [ startIdx ]
        visited = { startIdx }
        currentIdx = startIdx

        refXY = startPoint[ :2 ]  # Position XY de référence

        if verbose:
            print( f"        Starting descent from Z={startPoint[2]:.1f}m..." )

        stuckCount = 0
        maxStuck = 3

        for step in range( maxSteps ):
            currentZ = centers[ currentIdx, 2 ]

            # Obtenir les voisins topologiques
            neighborIndices = connectivity[ currentIdx ]

            # Filtrer les voisins:
            # 1. Non visités
            # 2. Même faille (si détectée)
            # 3. Plus bas en Z
            candidates = []

            for idx in neighborIndices:
                if idx in visited:
                    continue

                # Vérifier la faille
                if targetFaultId is not None and faultIds is not None and faultIds[ idx ] != targetFaultId:
                    continue

                # Vérifier qu'on descend
                if centers[ idx, 2 ] >= currentZ:
                    continue

                candidates.append( idx )

            if len( candidates ) == 0:
                # Si bloqué, essayer de regarder les voisins des voisins
                stuckCount += 1

                if stuckCount >= maxStuck:
                    if verbose:
                        print( f"        Reached bottom at Z={currentZ:.1f}m after {step+1} steps (no more neighbors)" )
                    break

                # Essayer niveau 2 (voisins des voisins)
                extendedCandidates = []
                for neighborIdx in neighborIndices:
                    if neighborIdx in visited:
                        continue

                    for secondNeighborIdx in connectivity[ neighborIdx ]:
                        if secondNeighborIdx in visited:
                            continue

                        if targetFaultId is not None and faultIds is not None and faultIds[
                                secondNeighborIdx ] != targetFaultId:
                            continue

                        if centers[ secondNeighborIdx, 2 ] < currentZ:
                            extendedCandidates.append( secondNeighborIdx )

                if len( extendedCandidates ) == 0:
                    if verbose:
                        print( f"        Reached bottom at Z={currentZ:.1f}m (extended search failed)" )
                    break

                candidates = extendedCandidates
                if verbose:
                    print( f"        Used extended search at step {step+1}" )
            else:
                stuckCount = 0

            # Parmi les candidats, choisir celui le plus proche en XY de la référence
            bestIdx = None
            bestDistanceXY = float( 'inf' )

            for idx in candidates:
                pos = centers[ idx ]
                dXY = np.sqrt( ( pos[ 0 ] - refXY[ 0 ] )**2 + ( pos[ 1 ] - refXY[ 1 ] )**2 )

                if dXY < bestDistanceXY:
                    bestDistanceXY = dXY
                    bestIdx = idx

            if bestIdx is None:
                if verbose:
                    print( f"        No valid neighbor at Z={currentZ:.1f}m" )
                break

            # Ajouter au profil
            profileIndices.append( bestIdx )
            visited.add( bestIdx )
            currentIdx = bestIdx

            # Debug
            if verbose and ( step + 1 ) % 100 == 0:
                print(
                    f"        Step {step+1}: Z={centers[currentIdx, 2]:.1f}m, XY=({centers[currentIdx, 0]:.1f}, {centers[currentIdx, 1]:.1f})"
                )

        # ===================================================================
        # ÉTAPE 5: EXTRAIRE LES RÉSULTATS
        # ===================================================================

        if len( profileIndices ) == 0:
            if verbose:
                print( "        ⚠️ No profile extracted" )
            return np.array( [] ), np.array( [] ), np.array( [] ), np.array( [] )

        depths = centers[ np.array( profileIndices ), 2 ]
        profileValues = values[ np.array( profileIndices ) ]
        pathX = centers[ np.array( profileIndices ), 0 ]
        pathY = centers[ np.array( profileIndices ), 1 ]

        # ===================================================================
        # STATISTIQUES
        # ===================================================================

        if verbose:
            zRange = np.max( centers[ :, 2 ] ) - np.min( centers[ :, 2 ] )
            depthCoverage = ( depths.max() - depths.min() ) / zRange * 100 if zRange > 0 else 0
            xyDisplacement = np.sqrt( ( pathX[ -1 ] - pathX[ 0 ] )**2 + ( pathY[ -1 ] - pathY[ 0 ] )**2 )

            print( f"        ✅ {len(profileIndices)} points extracted" )
            print( f"           Depth range: [{depths.max():.1f}, {depths.min():.1f}]m" )
            print( f"           Coverage: {depthCoverage:.1f}% of fault depth" )
            print( f"           XY displacement: {xyDisplacement:.1f}m" )

        return ( depths, profileValues, pathX, pathY )

    # -------------------------------------------------------------------
    @staticmethod
    def plotProfilePath3D( surface: pv.DataSet,
                           pathX: npt.NDArray[ np.float64 ],
                           pathY: npt.NDArray[ np.float64 ],
                           pathZ: npt.NDArray[ np.float64 ],
                           profileValues: npt.NDArray[ np.float64 ] | None = None,
                           scalarName: str = 'SCU',
                           savePath: str | None = None,
                           show: bool = True ) -> None:
        """Visualize the extracted profile path on the fault surface in 3D using PyVista.

        Parameters
        ----------
        surface : pyvista.PolyData
            Fault surface mesh
        pathX, pathY, pathZ : array-like
            Coordinates of the profile path
        profileValues : array-like, optional
            Values along the profile (for coloring the path)
        scalarName : str
            Name of the scalar to display on the surface
        savePath : Path or str, optional
            Path to save the screenshot
        show : bool
            Whether to display the plot interactively
        """
        if len( pathX ) == 0:
            print( "        ⚠️ No path to plot (empty profile)" )
            return

        print( f"        📊 Creating 3D visualization of profile path ({len(pathX)} points)" )

        # Create plotter
        plotter = pv.Plotter( window_size=[ 1600, 1200 ] )

        # Add fault surface with scalar field
        if scalarName in surface.cell_data:
            plotter.add_mesh( surface,
                              scalars=scalarName,
                              cmap='RdYlGn_r',
                              opacity=0.7,
                              show_edges=False,
                              lighting=True,
                              smooth_shading=True,
                              scalar_bar_args={
                                  'title': scalarName,
                                  'title_font_size': 20,
                                  'label_font_size': 16,
                                  'n_labels': 5,
                                  'italic': False,
                                  'fmt': '%.2f',
                                  'font_family': 'arial',
                              } )
        else:
            plotter.add_mesh( surface, color='lightgray', opacity=0.5, show_edges=True )

        # Create path as a polyline
        pathPoints = np.column_stack( [ pathX, pathY, pathZ ] )
        pathPolyline = pv.PolyData( pathPoints )

        # Add connectivity for line
        nPoints = len( pathPoints )
        lines = np.full( ( nPoints - 1, 3 ), 2, dtype=np.int_ )
        lines[ :, 1 ] = np.arange( nPoints - 1 )
        lines[ :, 2 ] = np.arange( 1, nPoints )
        pathPolyline.lines = lines.ravel()

        # Color the path by profile values or depth
        if profileValues is not None:
            pathPolyline[ 'profile_value' ] = profileValues
            colorField = 'profile_value'
            cmapPath = 'viridis'
        else:
            pathPolyline[ 'depth' ] = pathZ
            colorField = 'depth'
            cmapPath = 'turbo_r'

        # Add path as thick tube
        pathTube = pathPolyline.tube( radius=10.0 )  # Adjust radius as needed
        plotter.add_mesh( pathTube,
                          scalars=colorField,
                          cmap=cmapPath,
                          line_width=8,
                          render_lines_as_tubes=True,
                          lighting=True,
                          scalar_bar_args={
                              'title': 'Path ' + colorField,
                              'title_font_size': 20,
                              'label_font_size': 16,
                              'position_x': 0.85,
                              'position_y': 0.05,
                          } )

        # Add start and end markers
        startPoint = pv.Sphere( radius=30, center=pathPoints[ 0 ] )
        endPoint = pv.Sphere( radius=30, center=pathPoints[ -1 ] )

        plotter.add_mesh( startPoint, color='lime', label='Start (Top)' )
        plotter.add_mesh( endPoint, color='red', label='End (Bottom)' )

        # Add axes and labels
        plotter.add_axes( xlabel='X [m]', ylabel='Y [m]', zlabel='Z [m]', line_width=3, labels_off=False )

        # Add legend
        plotter.add_legend( labels=[ ( 'Start (Top)', 'lime' ), ( 'End (Bottom)', 'red' ) ],
                            bcolor='white',
                            border=True,
                            size=( 0.15, 0.1 ),
                            loc='upper left' )

        # Set camera and lighting
        plotter.camera_position = 'iso'
        plotter.add_light( pv.Light( position=( 1, 1, 1 ), intensity=0.8 ) )

        # Add title
        pathLength = np.sum( np.sqrt( np.sum( np.diff( pathPoints, axis=0 )**2, axis=1 ) ) )
        depthRange = pathZ.max() - pathZ.min()
        title = 'Profile Path Extraction\n'
        title += f'Points: {len(pathX)} | Length: {pathLength:.1f}m | Depth range: {depthRange:.1f}m'
        plotter.add_text( title, position='upper_edge', font_size=14, color='black' )

        # Save screenshot
        # if savePath is not None:
        # screenshot_path = savePath / 'profile_path_3d.png'
        # plotter.screenshot(str(screenshot_path))
        # print(f"        💾 Screenshot saved: {screenshot_path}")

        # Show
        if show:
            plotter.show()
        else:
            plotter.close()
