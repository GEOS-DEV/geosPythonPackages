# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

import numpy
import vtk


class CellLocator:

    def __init__( self, fileName ):
        self.globalGrid = None
        self.locator = None
        self.pointLocator = None
        self._read_grid( fileName )
        self._create_locator()

        localPoints = vtk.vtkPoints()
        self.merge = vtk.vtkMergePoints()
        self.localGrid = vtk.vtkUnstructuredGrid()
        bounds = self.globalGrid.GetBounds()
        self.z = bounds[ 4:6 ]
        self.t = vtk.reference( -1.0e30 )
        self.pcoords = [ -1.0 ] * 3
        self.subId = vtk.reference( -1 )
        self.merge.InitPointInsertion( localPoints, bounds )
        self.localGrid.SetPoints( localPoints )

    def locate( self, x ):
        foundIndex, xr = None, x
        cellids = vtk.vtkIdList()
        x1, x2 = ( x[ 0 ], x[ 1 ], self.z[ 0 ] ), ( x[ 0 ], x[ 1 ], self.z[ 1 ] )
        self.locator.FindCellsAlongLine( x1, x2, 1.0e-4, cellids )
        cellCount = cellids.GetNumberOfIds()
        gridPoints = self.globalGrid.GetPoints()
        for ci in range( cellCount ):
            cellIndex = cellids.GetId( ci )
            cell = self.globalGrid.GetCell( cellIndex )

            intersections = []
            for faceIndex in range( cell.GetNumberOfFaces() ):
                face = cell.GetFace( faceIndex )
                facePointCount = face.GetNumberOfPoints()
                faceCentre = numpy.mean(
                    numpy.array( [ gridPoints.GetPoint( face.GetPointId( fi ) ) for fi in range( facePointCount ) ] ),
                    axis=0,
                )
                for i in range( facePointCount ):
                    xc0 = gridPoints.GetPoint( face.GetPointId( ( i + 0 ) % facePointCount ) )
                    xc1 = gridPoints.GetPoint( face.GetPointId( ( i + 1 ) % facePointCount ) )
                    xc2 = faceCentre
                    trianglePoints = [ -1 ] * 3
                    for ip, xp in enumerate( [ xc0, xc1, xc2 ] ):
                        self.merge.InsertUniquePoint( xp, self.subId )
                        trianglePoints[ ip ] = self.subId.get()
                    newCell = self.localGrid.InsertNextCell( vtk.VTK_TRIANGLE, 3, trianglePoints )
                    triangle = self.localGrid.GetCell( newCell )
                    xp = [ -1.0e30 ] * 3
                    res = triangle.IntersectWithLine( x1, x2, 1.0e-4, self.t, xp, self.pcoords, self.subId )
                    if res != 0:
                        intersections.append( xp[ 2 ] )

            zz = sorted( { int( i / 1.0e-3 ): i for i in intersections }.values() )
            if len( zz ) == 2:
                if ( zz[ 0 ] <= x[ 2 ] ) and ( x[ 2 ] <= zz[ 1 ] ):
                    foundIndex = cellIndex
                    xr = ( x[ 0 ], x[ 1 ], 0.5 * ( zz[ 0 ] + zz[ 1 ] ) )
                    break

        return foundIndex, xr

    def _read_grid( self, fileName ):
        print( "Reading mesh %s" % ( fileName ), flush=True, end=" ... " )
        reader = vtk.vtkXMLUnstructuredGridReader()
        reader.SetFileName( fileName )
        reader.Update()
        print( "[Done]", flush=True )
        self.globalGrid = reader.GetOutput()

    def _create_locator( self ):
        print( "Building cell locator", flush=True, end=" ... " )
        cellLocator = vtk.vtkCellLocator()
        cellLocator.SetDataSet( self.globalGrid )
        cellLocator.BuildLocator()
        print( "[Done]", flush=True )
        self.locator = cellLocator


def translate_connections( connections ):
    dx, dy = 2493.0, 531520.0
    for name in connections:
        x, y, z = connections[ name ][ "x" ]
        connections[ name ][ "x" ] = ( x + dx, y + dy, -z )


def locate_connections( connections, cellLocator ):
    print( "Locating connections", flush=True )
    connectionCount = len( connections )
    for _, connection in connections.items():
        index, xg = cellLocator.locate( connection[ "x" ] )
        assert index is not None
        connection[ "v" ] = ( index, xg )


def filter_connections( connections, grid ):
    fiteredConnections = {}
    attributeArray = grid.GetCellData().GetArray( "attribute", vtk.reference( -1 ) )
    assert attributeArray is not None
    selectedRegions = set( [ 3 ] )
    print( "Filtering connections", flush=True )
    connectionCount = len( connections )
    for name, connection in connections.items():
        cellIndex = connection[ "v" ][ 0 ]
        cellAttribute = attributeArray.GetValue( cellIndex )
        if cellAttribute in selectedRegions:
            fiteredConnections[ name ] = connection
    return fiteredConnections


def sort_connections( connections, grid ):
    wells = {}
    TF = 0.001 * 1.157407407407407e-05 * 1.0e-05
    print( "Sorting connections", flush=True )
    connectionCount = len( connections )
    for _, connection in connections.items():
        wellName = connection[ "w" ]
        cellIndex = connection[ "v" ][ 0 ]
        cell = grid.GetCell( cellIndex )
        bounds = cell.GetBounds()

        if wellName not in wells:
            wells[ wellName ] = []
        wells[ wellName ].append( {
            "x": connection[ "x" ],
            "g": connection[ "g" ],
            "l": connection[ "l" ][ 0 ],
            "v": cellIndex,
            "t": TF * connection[ "t" ],
            "b": bounds,
        } )
    for wellName in wells:
        wells[ wellName ] = sorted( wells[ wellName ], key=lambda c: -c[ "x" ][ 2 ] )

    return wells


def write_fluxes( wells, fileName, cellLocator ):
    strGeometry, strFlux, strFunction = "", "", ""
    xtol, ztol = 1.0, 1.0e-2
    print( "Writing wells", flush=True )
    wellCount = len( wells )
    for wellName, wellData in wells.items():
        bb = wellData[ 0 ][ "b" ]
        xx, yy, zz = numpy.array( [ bb[ 0 ], bb[ 1 ] ] ), numpy.array( [ bb[ 2 ], bb[ 3 ] ] ), []
        for c in wellData:
            bb = c[ "b" ]
            xx = numpy.array( [ min( xx[ 0 ], bb[ 0 ] ), max( xx[ 1 ], bb[ 1 ] ) ] )
            yy = numpy.array( [ min( yy[ 0 ], bb[ 2 ] ), max( yy[ 1 ], bb[ 3 ] ) ] )
            z0, z1 = bb[ 4 ], bb[ 5 ]
            found = False
            for zi, dz in enumerate( zz ):
                if ( dz[ 0 ] < z0 + ztol and z0 - ztol < dz[ 1 ] ) or ( dz[ 0 ] < z1 + ztol and z1 - ztol < dz[ 1 ] ):
                    found = True
                    zz[ zi ] = [ min( dz[ 0 ], z0 ), max( dz[ 1 ], z1 ) ]
                    break
            if not found:
                zz.append( [ z0, z1 ] )

        boxNames = []
        boxCount = len( zz )
        for zi, dz in enumerate( zz ):
            boxName = "%s.%03d" % ( wellName, zi + 1 )
            boxNames.append( boxName )
            xMin = "{ %.5e, %.5e, %.5e }" % ( xx[ 0 ] - xtol, yy[ 0 ] - xtol, dz[ 0 ] - ztol )
            xMax = "{ %.5e, %.5e, %.5e }" % ( xx[ 1 ] + xtol, yy[ 1 ] + xtol, dz[ 1 ] + ztol )

            strGeometry += """{tab}<Box
{tab}    name="{name}"
{tab}    xMin="{xMin}"
{tab}    xMax="{xMax}" />
""".format( tab="        ", name=boxName, xMin=xMin, xMax=xMax )

        strFlux += """{tab}<SourceFlux
{tab}    name="{name}"
{tab}    component="0"
{tab}    functionName="{name}"
{tab}    objectPath="ElementRegions"
{tab}    setNames="{{ {setNames} }}"
{tab}    scale="1.868272"
{tab}    logLevel="2" /><!-- scale="1.868272" (Surface density to convert volumetric rate to mass rate) -->
""".format( tab="        ", name=f"FLUX.{wellName}", setNames=", ".join( boxNames ) )

        strFunction += """{tab}<TableFunction
{tab}    name="{name}"
{tab}    inputVarNames="{{ time }}"
{tab}    interpolation="lower"
{tab}    coordinates="{{ -1.0e30, 1.0e30 }}"
{tab}    values="{{ 0.0, 0.0 }}" />
""".format( tab="        ", name=f"FLUX.{wellName}" )

    with open( fileName, mode="w", encoding="utf-8" ) as xml:
        xml.write( '<?xml version="1.0" ?>\n<Problem>\n' )
        xml.write( f"    <Geometry>\n{strGeometry}    </Geometry>\n" )
        xml.write( f"    <FieldSpecifications>\n{strFlux}    </FieldSpecifications>\n" )
        xml.write( f"    <Functions>\n{strFunction}    </Functions>\n" )
        xml.write( "</Problem>\n\n" )


def write_solver( wells, fileName ):
    strControls, strMesh, strFunction = "", "", ""
    tab = "            "
    ztol = 1.0e-3
    targetRegions = []
    for wellName, wellData in wells.items():
        Z = [ zz for w in wellData for zz in w[ "b" ][ 4: ] ]
        cz = [ w[ "x" ][ 2 ] for w in wellData ]
        nc = len( cz )
        Z.extend( [ 0.5 * ( cz[ i - 1 ] + cz[ i ] ) for i in range( 1, nc ) ] )
        Z = { int( z / ztol ): z for z in Z }.values()
        Z = sorted( Z, reverse=True )
        nz = len( Z )
        x, y = wellData[ 0 ][ "x" ][ :2 ]  # Assume vertical wells
        z0 = Z[ 0 ]
        coords, conns, perforations = "", "", ""

        coords = f",\n{tab}        ".join( [ "{ %.4e, %.4e, %.4e }" % ( x, y, z ) for z in Z ] )
        conns = ",".join( [ "{%d,%d}" % ( i - 1, i ) for i in range( 1, nz ) ] )

        targetRegions.append( f"WELL.{wellName}" )

        for c in wellData:
            lgrName = "" if c[ "l" ] is None else f"{c['l']}."
            boxName = "%s.%s%03d.%03d.%03d" % (
                wellName,
                lgrName,
                c[ "g" ][ 0 ],
                c[ "g" ][ 1 ],
                c[ "g" ][ 2 ],
            )
            distance = z0 - c[ "x" ][ 2 ]
            trans = c[ "t" ]

            newNode = ElementTree.Element( "Perforation" )

            target = root.find( ".//holidays" )
            target.append( newNode )

            from geos.models.schema import PerforationType

            pt = PerforationType( boxName, distance, trans )
            print( pt )

            perforations += f"""\n{tab}    <Perforation
{tab}        name="{boxName}"
{tab}        distance="{distance}"
{tab}        transmissibility="{trans}" />"""

        strMesh += f"""{tab}<InternalWell
{tab}    name="well.{wellName}"
{tab}    wellControlsName="{wellName}"
{tab}    wellRegionName="WELL.{wellName}"
{tab}    radius="0.10"
{tab}    polylineNodeCoords="{{
{tab}        {coords} }}"
{tab}    polylineSegmentConn="{{ {conns} }}"
{tab}    numElementsPerSegment="1"
{tab}    logLevel="2">{perforations}
{tab}</InternalWell>
"""

        strFunction += """{tab}<TableFunction
{tab}    name="{name}"
{tab}    inputVarNames="{{ time }}"
{tab}    interpolation="lower"
{tab}    coordinates="{{ -1.0e30, 1.0e30 }}"
{tab}    values="{{ 0.0, 0.0 }}" />
""".format( tab="        ", name=f"FLUX.{wellName}" )

        strControls += """{tab}<WellControls
{tab}    name="{name}"
{tab}    referenceElevation="{z0}"
{tab}    enableCrossflow="0"
{tab}    logLevel="2" />
""".format( tab="            ", name=wellName, z0=z0 )

    with open( fileName, mode="w", encoding="utf-8" ) as xml:
        xml.write( '<?xml version="1.0" ?>\n<Problem>\n' )
        xml.write( "    <Solvers>\n" )
        xml.write( """        <CompositionalMultiphaseWell
            name="WELL.SOLVER"
            targetRegions="{{ {targetRegions} }}"
            logLevel="1" />
""".format( targetRegions=", ".join( targetRegions ) ) )
        xml.write( strControls )
        xml.write( "        </CompositionalMultiphaseWell>\n" )
        xml.write( "    </Solvers>\n" )
        xml.write( f"    <Mesh>\n        <VTKMesh>\n{strMesh}        </VTKMesh>\n    </Mesh>\n" )
        xml.write( f"    <Functions>\n{strFunction}    </Functions>\n" )
        xml.write( "</Problem>\n\n" )
