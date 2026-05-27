# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc, Copilot
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, Any
import numpy as np
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk
import vtk
import sys

from geos.mesh.io.vtkIO import writeMesh, VtkOutput, readUnstructuredGrid
from geos.mesh_doctor.parsing.cliParsing import setupLogger

if sys.version_info >= ( 3, 11 ):
    from enum import StrEnum
else:

    class StrEnum( str, Enum ):
        """String enumeration base class for Python versions < 3.11."""
        pass


class IPType( StrEnum ):
    """Interface Pressure" type for MFD indicators."""
    # TPFA = "TPFA"
    QTPFA = "QTPFA"
    BdLVM = "BdLVM"


@dataclass( frozen=True )
class Face:
    """Represents a face of a cell in the mesh, defined by its vertex indexes, center, normal vector, and area."""
    indexes: List[ int ]
    center: List[ float ]
    normal: List[ float ]
    area: float


VTK_TETRA_FACES = [
    [ 0, 1, 3 ],
    [ 1, 2, 3 ],
    [ 0, 3, 2 ],
    [ 0, 2, 1 ],
]

VTK_VOXEL_FACES = [
    [ 0, 2, 6, 4 ],
    [ 1, 3, 7, 5 ],
    [ 0, 1, 5, 4 ],
    [ 2, 3, 7, 6 ],
    [ 0, 1, 3, 2 ],
    [ 4, 5, 7, 6 ],
]

VTK_HEXAHEDRON_FACES = [
    [ 0, 3, 2, 1 ],
    [ 4, 5, 6, 7 ],
    [ 0, 1, 5, 4 ],
    [ 2, 3, 7, 6 ],
    [ 0, 4, 7, 3 ],
    [ 1, 2, 6, 5 ],
]

VTK_WEDGE_FACES = [
    [ 0, 1, 2 ],
    [ 3, 5, 4 ],
    [ 0, 3, 4, 1 ],
    [ 1, 4, 5, 2 ],
    [ 0, 2, 5, 3 ],
]

VTK_PYRAMID_FACES = [
    [ 0, 3, 2, 1 ],
    [ 0, 1, 4 ],
    [ 1, 2, 4 ],
    [ 2, 3, 4 ],
    [ 3, 0, 4 ],
]

_FACE_TABLE: Dict[ int, List[ List[ int ] ] ] = {
    vtk.VTK_TETRA: VTK_TETRA_FACES,
    vtk.VTK_VOXEL: VTK_VOXEL_FACES,
    vtk.VTK_HEXAHEDRON: VTK_HEXAHEDRON_FACES,
    vtk.VTK_WEDGE: VTK_WEDGE_FACES,
    vtk.VTK_PYRAMID: VTK_PYRAMID_FACES,
}


def get_cell_faces( cell: vtk.vtkCell ) -> List[ List[ int ] ]:
    """Returns the list of faces for a given cell, where each face is represented by a list of vertex indexes.

    Args:
        cell: The input cell for which to retrieve the faces.

    Returns:
        List[List[int]]: The list of faces for the given cell. Each face is represented as a list of vertex indexes.
    """
    cell_type = cell.GetCellType()
    if cell_type not in _FACE_TABLE:
        unknown_name = vtk.vtkCellTypes.GetClassNameFromTypeId( cell_type ) or str( cell_type )
        raise ValueError( f"Unsupported cell type '{unknown_name}' (id={cell_type})." )
    local_to_global = [ cell.GetPointId( i ) for i in range( cell.GetNumberOfPoints() ) ]
    return [ [ local_to_global[ local_idx ] for local_idx in face ] for face in _FACE_TABLE[ cell_type ] ]


# TODO: Refactor the ComputeMFD class to separate the computation of indicators from the mesh processing logic, and to allow for more flexible input parameters (e.g., different permeability fields, additional indicators, etc.).
def filterVolumeCells( mesh: vtk.vtkDataSet ) -> vtk.vtkDataSet:
    """Filters the input mesh to retain only volume cells (3D cells) and returns the resulting mesh.

    Args:
        mesh: The input mesh to filter.

    Returns:
        vtk.vtkDataSet: The filtered mesh containing only volume cells (3D cells).
    """
    volumeIds = vtk.vtkIdTypeArray()
    for i in range( mesh.GetNumberOfCells() ):
        dim = mesh.GetCell( i ).GetCellDimension()
        if dim == 3:
            volumeIds.InsertNextValue( i )

    sn = vtk.vtkSelectionNode()
    sn.SetFieldType( vtk.vtkSelectionNode.CELL )
    sn.SetContentType( vtk.vtkSelectionNode.INDICES )
    sn.SetSelectionList( volumeIds )

    sel = vtk.vtkSelection()
    sel.AddNode( sn )

    ext = vtk.vtkExtractSelection()
    ext.SetInputData( 0, mesh )
    ext.SetInputData( 1, sel )
    ext.Update()

    setupLogger.info(
        f"Filtered {ext.GetOutput().GetNumberOfCells()}/{mesh.GetNumberOfCells()} volume cells from the input mesh." )
    return ext.GetOutput()


def __attach_results( mesh: vtk.vtkDataSet,
                      matrices: List[ Tuple[ float, float, float, float, float, float ] ],
                      field_name: str = "MatrixField" ) -> vtk.vtkDataSet:
    """Attaches the computed MFD indicators to the mesh as a new cell data array with the specified field name."""
    flat = np.array( [ np.asarray( m, dtype=np.float64 ) for m in matrices ] )
    vtk_arr = numpy_to_vtk( flat, deep=True, array_type=vtk.VTK_DOUBLE )
    vtk_arr.SetName( field_name )
    vtk_arr.SetNumberOfComponents( 6 )
    vtk_arr.SetComponentName( 0, "condM" )
    vtk_arr.SetComponentName( 1, "consistency" )
    vtk_arr.SetComponentName( 2, "lambda_m" )
    vtk_arr.SetComponentName( 3, "lambda_M" )
    vtk_arr.SetComponentName( 4, "idempotence" )
    vtk_arr.SetComponentName( 5, "orthogonality" )
    mesh.GetCellData().AddArray( vtk_arr )
    return mesh


class ComputeMFD:
    """Class responsible for computing MFD indicators for a given mesh and permeability field, based on the specified interface pressure type (TPFA, QTPFA, or BdLVM)."""

    def __init__( self, mesh: vtk.vtkDataSet, permeability_field: str = "Permeability" ) -> None:
        """Initializes the ComputeMFD instance by computing the faces, cell centers, and permeability field from the input mesh."""
        # make sure that we have always Volume and don't act on surfaces or lines
        self.mesh = filterVolumeCells( mesh )
        self.mesh = add_cell_volumes( self.mesh )
        # compute faces and cell centers after filtering to ensure we only process volume cells
        self.faces, self.face2cell = ComputeMFD.compute_newell( self.mesh )
        self.cell_centers = ComputeMFD.__compute_cell_centroids( self.mesh )
        self.permeability_field = permeability_field
        self.ip_type = IPType.QTPFA

    def set_IP( self, ip_type: IPType ) -> None:
        """Sets the interface pressure type for the MFD computation.

        Args:
            ip_type (IPType): The interface pressure type to use for the MFD computation (TPFA, QTPFA, or BdLVM).
        """
        self.ip_type = ip_type

    def compute( self ) -> List[ Tuple[ float, float, float, float, float, float ] ]:
        """Computes the MFD indicators for the input mesh based on the specified interface pressure type and returns the results as a list of tuples containing the indicators for each cell.

        Args:
            mesh (vtk.vtkDataSet): The input mesh for which to compute the MFD indicators.
        """
        # if self.ip_type == IPType.TPFA:
        # return self.compute_tpfa(mesh)

        if self.ip_type == IPType.QTPFA:
            return self.compute_quasitpfa( self.mesh )
        elif self.ip_type == IPType.BdLVM:
            return self.compute_bdlvm( self.mesh )
        else:
            raise ValueError( f"Unsupported IP type: {self.ip_type}" )

    # def compute_tpfa(self, mesh) -> list[np.ndarray]:
    #     """Computes the MFD indicators using the TPFA method for the input mesh and returns the results as a list of tuples containing the indicators for each cell.
    #         Args:
    #           mesh (vtk.vtkDataSet): The input mesh for which to compute the MFD indicators using the TPFA method.
    #     """
    #     perm = vtk_to_numpy(mesh.GetCellData().GetArray(self.permeability_field))
    #     cell2face = {}
    #     [cell2face.setdefault(cell, []).append(k) for k, v in self.face2cell.items() for cell in v]
    #     ncells = len(self.cell_centers)
    #     M = [None] * ncells
    #     face_centers = np.array([self.faces[k].center for k in self.face2cell])
    #     face_normals = np.array([self.faces[k].normal for k in self.face2cell])
    #     face_area = np.array([self.faces[k].area for k in self.face2cell])

    #     def process_cell(cell):
    #         face_indices = cell2face.get(cell)
    #         nfacesPerCell = len(face_indices)
    #         Mloc = np.zeros((nfacesPerCell, nfacesPerCell))
    #         face_cell_vec = np.ndarray((ncells, nfacesPerCell, 3))
    #         face_cell_dist = np.ndarray((ncells, nfacesPerCell))
    #         face_cell_vec[cell, :, :] = face_centers[face_indices, :] - self.cell_centers[cell, :]
    #         face_cell_dist[cell, :] = np.linalg.norm(face_cell_vec[cell, :, :], axis=1)
    #         face_cell_vec[cell, :, :] /= face_cell_dist[cell, :].reshape(nfacesPerCell, 1)

    #         face_normals[face_indices, :] = ComputeMFD.__reorient_normal(face_normals[face_indices, :], face_cell_vec[cell, :, :])
    #         T = np.einsum('ni,ni,ni->n', face_cell_vec[cell, :, :], np.tile(perm[cell, :], (nfacesPerCell, 1)), face_normals[face_indices, :])
    #         T *= face_area[face_indices] / face_cell_dist[cell, :]
    #         Mloc[range(nfacesPerCell), range(nfacesPerCell)] = 1 / T
    #         return cell, Mloc

    #     from concurrent.futures import ThreadPoolExecutor, as_completed
    #     total = len(cell2face)
    #     with ThreadPoolExecutor(max_workers=8) as executor:
    #         futures = [executor.submit(process_cell, i) for i in range(total)]
    #         results = [future.result() for future in as_completed(futures)]

    #     for cell, Mloc in results:
    #         M[cell] = Mloc
    #     return M

    def compute_quasitpfa( self, mesh: vtk.vtkDataSet ) -> List[ Tuple[ float, float, float, float, float, float ] ]:
        """Computes the MFD indicators using the QTPFA method for the input mesh and returns the results as a list of tuples containing the indicators for each cell.

        Args:
          mesh (vtk.vtkDataSet): The input mesh for which to compute the MFD indicators using the QTPFA method.
        """
        perm = vtk_to_numpy( mesh.GetCellData().GetArray( self.permeability_field ) )
        invperm = 1.0 / perm
        vol = vtk_to_numpy( mesh.GetCellData().GetArray( "Volume" ) )
        cell2face: Dict[ int, List[ int ] ] = {}

        for k, v in self.face2cell.items():
            for cell in v:
                cell2face.setdefault( cell, [] ).append( k )

        cell_centers = ComputeMFD.__compute_cell_centroids( mesh )
        ncells = len( cell_centers )
        M = [ ( 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ) ] * ncells
        face_centers = np.array( [ self.faces[ k ].center for k in self.face2cell ] )
        face_normals = np.array( [ self.faces[ k ].normal for k in self.face2cell ] )
        face_area = np.array( [ self.faces[ k ].area for k in self.face2cell ] )

        def process_cell( cell: int ) -> Tuple[ int, float, float, float, float, float, float ]:
            face_indices = cell2face.get( cell, [] )
            nf = len( face_indices )
            fc_vec = face_centers[ face_indices ] - cell_centers[ cell ]
            c = fc_vec
            loc_normals = ComputeMFD.__reorient_normal( face_normals[ face_indices ], c )
            n = loc_normals * face_area[ face_indices, None ]
            K = np.tile( perm[ cell ], ( nf, 1 ) )
            Kinv = np.tile( invperm[ cell ], ( nf, 1 ) )
            Mloc = np.einsum( 'ni,ni,mi->nm', c, Kinv, c ) / vol[ cell ]
            w = np.einsum( 'ni,ni,ni->n', n, K, n )
            Q, _ = np.linalg.qr( n, mode='reduced' )
            proj = np.eye( nf ) - np.einsum( 'ni,mi->nm', Q, Q )
            S = np.einsum( 'ij,j,jk->ik', proj, w, proj )
            S = ( vol[ cell ] / 2.0 ) * S
            indicators = ComputeMFD.__get_indicators( proj, Mloc, S )
            return ( cell, *indicators )

        from concurrent.futures import ThreadPoolExecutor, as_completed
        total = len( cell2face )
        with ThreadPoolExecutor( max_workers=8 ) as executor:
            futures = [ executor.submit( process_cell, i ) for i in range( total ) ]
            results = [ future.result() for future in as_completed( futures ) ]

        for cell, c, cr, lm, lM, idem, ortho in results:
            M[ cell ] = ( c, cr, lm, lM, idem, ortho )
        return M

    def compute_bdlvm( self, mesh: vtk.vtkDataSet ) -> List[ Tuple[ float, float, float, float, float, float ] ]:
        """Computes the MFD indicators using the BDLVM method for the input mesh and returns the results as a list of tuples containing the indicators for each cell.

        Args:
          mesh (vtk.vtkDataSet): The input mesh for which to compute the MFD indicators using the BDLVM method.
        """
        perm = vtk_to_numpy( mesh.GetCellData().GetArray( self.permeability_field ) )
        cell2face: Dict[ int, List[ int ] ] = {}

        for k, v in self.face2cell.items():
            for cell in v:
                cell2face.setdefault( cell, [] ).append( k )

        ncells = len( self.cell_centers )
        M = [ ( 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ) ] * ncells
        face_centers = np.array( [ self.faces[ k ].center for k in self.face2cell ] )
        face_normals = np.array( [ self.faces[ k ].normal for k in self.face2cell ] )
        face_area = np.array( [ self.faces[ k ].area for k in self.face2cell ] )

        def process_cell( cell: int ) -> Tuple[ int, float, float, float, float, float, float ]:
            face_indices = cell2face.get( cell, [] )
            nf = len( face_indices )
            gamma = 1.0 / nf
            fc_vec = face_centers[ face_indices ] - self.cell_centers[ cell ]
            area = face_area[ face_indices ]
            c = np.einsum( 'ni,n->ni', fc_vec, area )
            n = face_normals[ face_indices ]
            K = np.tile( perm[ cell ], ( nf, 1 ) )
            n = np.einsum( 'ni,ni->ni', n, K )
            CtN_inv = np.linalg.pinv( c.T @ n )
            M0 = np.einsum( 'ni,ij,mj->nm', c, CtN_inv, c )
            NtN_inv = np.linalg.pinv( n.T @ n )
            proj = np.eye( nf ) - np.einsum( 'ni,ij,mj->nm', n, NtN_inv, n )
            Mloc = M0
            S = gamma * proj
            Mloc = np.einsum( 'ij,i,j->ij', Mloc, 1.0 / area, 1.0 / area )
            S = np.einsum( 'ij,i,j->ij', S, 1.0 / area, 1.0 / area )
            indicators = ComputeMFD.__get_indicators( proj, Mloc, S )
            return ( cell, *indicators )

        from concurrent.futures import ThreadPoolExecutor, as_completed
        total = len( cell2face )
        with ThreadPoolExecutor( max_workers=8 ) as executor:
            futures = [ executor.submit( process_cell, i ) for i in range( total ) ]
            results = [ future.result() for future in as_completed( futures ) ]

        for cell, c, cr, lm, lM, idem, ortho in results:
            M[ cell ] = ( c, cr, lm, lM, idem, ortho )
        return M

    @staticmethod
    def __get_indicators( K: np.ndarray,
                          M: np.ndarray,
                          S: np.ndarray,
                          compute_eigs: bool = True ) -> Tuple[ Any, Any, float, float, Any, Any ]:
        """Computes the MFD indicators (condition number, consistency, eigenvalues, idempotence, and orthogonality) based on the local MFD matrices K, M, and S for a given cell."""
        Sr = K.T @ S @ K
        K.T @ M @ K

        def get_eigs( Mx: np.ndarray, Sx: np.ndarray ) -> np.ndarray:
            lambdas: np.ndarray = np.array( [] )
            if compute_eigs:
                lambdas = np.linalg.eigvals( Mx + Sx )

            return lambdas

        lambdas = get_eigs( M, S )
        return (
            np.linalg.cond( M + S ),
            np.linalg.matrix_norm( Sr ),
            np.min( lambdas.real ),
            np.max( lambdas.real ),
            np.linalg.matrix_norm( K - K @ K ),
            np.linalg.matrix_norm( ( S - Sr ) ),
        )

    @staticmethod
    def centroid_3d_polygon( mesh: vtk.vtkDataSet,
                             point_indices: List[ int ],
                             area_tolerance: float = 0.0 ) -> Tuple[ np.ndarray, np.ndarray, float ]:
        """Computes the centroid, normal vector, and area of a 3D polygon defined by the given point indices in the input mesh, using Newell's method."""
        n = len( point_indices )
        if n < 2:
            raise ValueError( f"Polygon must have at least 2 points, got {n}." )
        points = vtk_to_numpy( mesh.GetPoints().GetData() )
        origin = points[ point_indices[ 0 ] ].copy()
        normal = np.zeros( 3 )
        center = np.zeros( 3 )
        for a in range( n ):
            current = points[ point_indices[ a ] ] - origin
            next_pt = points[ point_indices[ ( a + 1 ) % n ] ] - origin
            cross = np.cross( current, next_pt )
            normal += cross
            center += next_pt
        area = np.linalg.norm( normal )
        center = center / n + origin
        if area > area_tolerance:
            normal /= area
            area *= 0.5
        elif area < -area_tolerance:
            raise ValueError( "Negative area found" )
        else:
            return center, normal, 0.0
        return center, normal, area

    @staticmethod
    def compute_newell( mesh: vtk.vtkDataSet ) -> Tuple[ Dict[ int, Face ], Dict[ int, List[ int ] ] ]:
        """Computes the faces of the mesh using Newell's method and returns a dictionary of faces and a mapping from face indices to cell indices.

        Args:
            mesh (vtk.vtkDataSet): The input mesh for which to compute the faces using Newell's method.
        """
        faces: Dict[ int, Face ] = {}
        face2cell: Dict[ int, List[ int ] ] = {}

        def process_cell( cellid: int ) -> Tuple[ List[ Tuple ], List[ Tuple ] ]:
            local_faces: List[ Tuple ] = []
            local_map: List[ Tuple ] = []
            list_indexes = get_cell_faces( mesh.GetCell( cellid ) )
            for indexes in list_indexes:
                center, normal, area = ComputeMFD.centroid_3d_polygon( mesh, indexes )
                key = tuple( sorted( indexes ) )
                local_faces.append( ( key, indexes, center, normal, area ) )
                local_map.append( ( key, cellid ) )
            return local_faces, local_map

        next_index = 0
        from concurrent.futures import ThreadPoolExecutor, as_completed
        total = mesh.GetNumberOfCells()
        with ThreadPoolExecutor( max_workers=8 ) as executor:
            futures = [ executor.submit( process_cell, i ) for i in range( total ) ]
            results = [ future.result() for future in as_completed( futures ) ]

        face_lookup = {}
        for local_faces, local_map in results:
            for key, indexes, center, normal, area in local_faces:
                if key not in face_lookup:
                    face_lookup[ key ] = next_index
                    faces[ next_index ] = Face( indexes=indexes, center=center, normal=normal, area=area )
                    next_index += 1
            for key, cellid in local_map:
                face_index = face_lookup[ key ]
                face2cell.setdefault( face_index, [] ).append( cellid )

        return faces, face2cell

    @staticmethod
    def __reorient_normal( normals: np.ndarray, cell2vec: np.ndarray ) -> np.ndarray:
        """Reorients the normal vectors of the faces based on the direction of the vector from the cell center to the face center, ensuring that the normals point outward from the cell."""
        flag = np.einsum( 'ni,ni->n', normals, cell2vec ) < 0
        normals[ flag ] = -normals[ flag ]
        return normals

    @staticmethod
    def __compute_cell_centroids( mesh: vtk.vtkDataSet ) -> np.ndarray:
        """Computes the centroids of the cells in the input mesh and returns them as a NumPy array."""
        vtkCellCenters = vtk.vtkCellCenters()
        vtkCellCenters.SetInputData( mesh )
        vtkCellCenters.Update()
        return vtk_to_numpy( vtkCellCenters.GetOutput().GetPoints().GetData() )


def add_cell_volumes( mesh: vtk.vtkUnstructuredGrid ) -> vtk.vtkUnstructuredGrid:
    """Computes the volumes of the cells in the input mesh and adds them as a new cell data array named 'Volume', returning the modified mesh.

    Args:
        mesh (vtk.vtkUnstructuredGrid): The input mesh for which to compute and add the cell volumes.

    Returns:
        vtk.vtkUnstructuredGrid: The modified mesh with the computed cell volumes added as a new cell data array named 'Volume'.
    """
    quality = vtk.vtkMeshQuality()
    quality.SetInputData( mesh )
    quality.SetHexQualityMeasureToVolume()
    quality.SetTetQualityMeasureToVolume()
    quality.SetWedgeQualityMeasureToVolume()
    quality.SetPyramidQualityMeasureToVolume()
    quality.Update()
    quality_array = vtk_to_numpy( quality.GetOutput().GetCellData().GetArray( "Quality" ) )
    volume_array = numpy_to_vtk( quality_array, deep=True )
    volume_array.SetName( "Volume" )
    mesh.GetCellData().AddArray( volume_array )
    return mesh


@dataclass( frozen=True )
class Options:
    """Configuration options for MFD computation, including the output settings, interface pressure type, and permeability field name."""
    vtkOutput: VtkOutput
    ip: str
    permeability: str = "Permeability"


@dataclass( frozen=True )
class Result:
    """Result of the MFD computation."""
    info: str


def meshAction( mesh: vtk.vtkDataSet, options: Options ) -> Result:
    """Performs the MFD computation on the input mesh using the specified options and returns the results as a Result object containing information about the computation.

    Args:
        mesh (vtk.vtkDataSet): The input mesh for which to compute the MFD indicators.
        options (Options): The configuration options for the MFD computation, including the output settings, interface pressure type, and permeability field name.

    Returns:
        Result: An object containing information about the MFD computation, including the output file path and the interface pressure type used for the computation.
    """
    mfd = ComputeMFD( mesh, permeability_field=options.permeability )
    try:
        mfd.set_IP( IPType[ options.ip ] )
    except Exception as e:
        raise ValueError( f"Unsupported IP type: {options.ip}" ) from e

    res = mfd.compute()
    mesh = __attach_results( mesh, res, f"{options.ip}_Results" )

    writeMesh( mesh, options.vtkOutput, canOverwrite=True, logger=setupLogger )
    return Result( info=f"MFD {options.ip} computed and written to {options.vtkOutput.output}" )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Main entry point for the MFD computation action, which reads the input mesh from the specified VTU file, performs the MFD computation using the provided options, and returns the results as a Result object containing information about the computation.

    Args:
        vtuInputFile (str): The file path to the input VTU mesh for which to compute the MFD indicators.
        options (Options): The configuration options for the MFD computation, including the output settings, interface pressure type, and permeability field name.

    Returns:
        Result: An object containing information about the MFD computation, including the output file path and the interface pressure type used for the computation.
    """
    mesh = readUnstructuredGrid( vtuInputFile )
    return meshAction( mesh, options )
