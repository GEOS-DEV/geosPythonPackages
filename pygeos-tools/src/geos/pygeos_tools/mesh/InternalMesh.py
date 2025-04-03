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

import numpy as np
import numpy.typing as npt
from typing import Dict, List
from typing_extensions import Self

__doc__ = """
InternalMesh class uses a XML object from input/Xml.py that needs to have parsed a GEOS xml file where an 'InternalMesh'
block has been defined. This class gathers all the geometric informaion defined.
"""


class InternalMesh:
    """
    GEOSX Internal Mesh

    Attributes
    ----------
        xml : XML
            XML object containing the information on the mesh
        bounds : list of list
            Real bounds of the mesh [[xmin, xmax],[ymin,ymax],[zmin,zmax]]
        nx : int
            Number of elements in the x direction
        ny : int
            Number of elements in the y direction
        nz : int
            Number of elements in the z direction
        order : int
            Mesh order
        cellBlockNames : str
            Names of each mesh block
        cellBounds : npt.NDArray
        elementTypes : List[ str ]
            Element types of each mesh block
        numberOfCells : int
            Total number of cells
        numberOfPoints : int
            Total number of points
        fieldSpecifications : dict
            Dict containing the mesh field specifications
    """

    def __init__( self: Self, xml ):
        """
        Parameters
        ----------
            xml : XML
                XML object containing the information on the mesh
        """
        self.xml = xml
        try:
            mesh: Dict = xml.mesh[ "InternalMesh" ]
        except KeyError:
            raise KeyError( f"The XML file '{self.xml.filename}' does not contain an 'InternalMesh' block." )

        xCoords: List[ int ] = list( eval( mesh[ "xCoords" ] ) )
        yCoords: List[ int ] = list( eval( mesh[ "yCoords" ] ) )
        zCoords: List[ int ] = list( eval( mesh[ "zCoords" ] ) )

        self.bounds: List[ List[ float ] ] = [ [ xCoords[ 0 ], xCoords[ -1 ] ], [ yCoords[ 0 ], yCoords[ -1 ] ],
                                               [ zCoords[ 0 ], zCoords[ -1 ] ] ]

        nxStr: str = mesh[ "nx" ].strip( '' ).replace( '{', '' ).replace( '}', '' ).split( ',' )
        nyStr: str = mesh[ "ny" ].strip( '' ).replace( '{', '' ).replace( '}', '' ).split( ',' )
        nzStr: str = mesh[ "nz" ].strip( '' ).replace( '{', '' ).replace( '}', '' ).split( ',' )

        nx: List[ int ] = [ eval( nx ) for nx in nxStr ]
        ny: List[ int ] = [ eval( ny ) for ny in nyStr ]
        nz: List[ int ] = [ eval( nz ) for nz in nzStr ]

        self.nx: List[ int ] = nx
        self.ny: List[ int ] = ny
        self.nz: List[ int ] = nz

        order: int = 1
        self.order: int = order

        self.cellBlockNames = mesh[ "cellBlockNames" ].strip( '' ).replace( '{', '' ).replace( '}', '' ).split( ',' )

        xlayers: List[ List[ float ] ] = list()
        ylayers: List[ List[ float ] ] = list()
        zlayers: List[ List[ float ] ] = list()
        for i in range( len( nx ) ):
            xlayers.append( [ xCoords[ i ], xCoords[ i + 1 ] ] )
        for i in range( len( ny ) ):
            ylayers.append( [ yCoords[ i ], yCoords[ i + 1 ] ] )
        for i in range( len( nz ) ):
            zlayers.append( [ zCoords[ i ], zCoords[ i + 1 ] ] )

        self.layers: List[ List[ List[ float ] ] ] = [ xlayers, ylayers, zlayers ]

        xCellsBounds: npt.NDArray = np.zeros( sum( nx ) + 1 )
        yCellsBounds: npt.NDArray = np.zeros( sum( ny ) + 1 )
        zCellsBounds: npt.NDArray = np.zeros( sum( nz ) + 1 )

        for i in range( len( nx ) ):
            xstep: int = ( xlayers[ i ][ 1 ] - xlayers[ i ][ 0 ] ) / nx[ i ]
            if i == 0:
                xCellsBounds[ 0:nx[ i ] ] = np.arange( xlayers[ i ][ 0 ], xlayers[ i ][ 1 ], xstep )
            else:
                xCellsBounds[ nx[ i - 1 ]:sum( nx[ 0:i + 1 ] ) ] = np.arange( xlayers[ i ][ 0 ], xlayers[ i ][ 1 ],
                                                                              xstep )
        xCellsBounds[ nx[ -1 ] ] = xlayers[ i ][ 1 ]

        for i in range( len( ny ) ):
            ystep: int = ( ylayers[ i ][ 1 ] - ylayers[ i ][ 0 ] ) / ny[ i ]
            if i == 0:
                yCellsBounds[ 0:ny[ i ] ] = np.arange( ylayers[ i ][ 0 ], ylayers[ i ][ 1 ], ystep )
            else:
                xCellsBounds[ ny[ i - 1 ]:sum( ny[ 0:i + 1 ] ) ] = np.arange( ylayers[ i ][ 0 ], ylayers[ i ][ 1 ],
                                                                              ystep )
        yCellsBounds[ ny[ -1 ] ] = ylayers[ i ][ 1 ]

        for i in range( len( nz ) ):
            zstep: int = ( zlayers[ i ][ 1 ] - zlayers[ i ][ 0 ] ) / nz[ i ]
            if i == 0:
                zCellsBounds[ 0:nz[ i ] ] = np.arange( zlayers[ i ][ 0 ], zlayers[ i ][ 1 ], zstep )
            else:
                zCellsBounds[ nz[ i - 1 ]:sum( nz[ 0:i + 1 ] ) ] = np.arange( zlayers[ i ][ 0 ], zlayers[ i ][ 1 ],
                                                                              zstep )
        zCellsBounds[ nz[ -1 ] ] = zlayers[ i ][ 1 ]

        self.cellBounds: List[ npt.NDArray ] = [ xCellsBounds, yCellsBounds, zCellsBounds ]

        elementTypes: str = mesh[ "elementTypes" ].strip( '' ).replace( '{', '' ).replace( '}', '' ).split( ',' )

        self.elementTypes: List[ str ] = list()
        for type in elementTypes:
            if type == "C3D8":
                self.elementTypes.append( "Hexahedron" )
            else:
                self.elementTypes.append( type )

        self.numberOfCells: int = sum( nx ) * sum( ny ) * sum( nz )
        self.numberOfPoints: int = ( sum( nx ) + 1 ) * ( sum( ny ) + 1 ) * ( sum( nz ) + 1 )

        self.fieldSpecifications: Dict[ str, any ] = xml.fieldSpecifications
        self.isSet: bool = True
