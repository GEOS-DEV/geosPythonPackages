# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: jafranc
"""Mesh-building helpers for mesh-doctor unit tests.

Generators extracted from misc/mesh_gen.py (--gen branch) plus
synthetic defect configurations for testing each mesh-doctor check.

Public API
----------
Mesh generators (from gen branch):
    build_hex_mesh                      clean z-major hex grid
    build_tetra_mesh                    Delaunay3D tetra on z-major grid
    build_tetra_mesh_patterned          Delaunay3D on checkerboard-filtered points ("shifted")
    build_hex_mesh_with_fractures       hex + quad fractures, 'attribute' cell array
    build_tetra_mesh_with_fractures     tetra + tri fractures, 'attribute' cell array

Non-manifold configurations:
    build_surface_with_non_manifold_edge   3 quads sharing one edge (flap)
    build_volume_with_non_manifold_edge    2 hexes sharing only one edge (bowtie)

Mesh-doctor defect configurations:
    build_mesh_with_collocated_nodes        → collocatedNodes check
    build_mesh_with_orphan_2d_cells         → orphan2d check
    build_mesh_with_negative_volume         → elementVolumes check
    build_mesh_with_self_intersecting_elements → selfIntersectingElements check
"""

import numpy as np
import numpy.typing as npt
import vtk
from vtkmodules.vtkCommonCore import vtkIdList, vtkIntArray, vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkPolyData, vtkUnstructuredGrid, VTK_HEXAHEDRON, VTK_QUAD )
from vtkmodules.vtkFiltersCore import vtkAppendFilter
from vtkmodules.util.numpy_support import numpy_to_vtk

# ──────────────────────────────────────────────────────────────
# Private geometry primitives
# ──────────────────────────────────────────────────────────────


def _gen_box_z_major( Lx: float, Ly: float, Lz: float, nx: int, ny: int, nz: int ) -> npt.NDArray[ np.float64 ]:
    """Grid points with x slowest, y medium, z fastest (z-major ordering).

    Point at (i, j, k) has linear index  k + j*nz + i*nz*ny.
    """
    xs = np.linspace( 0.0, Lx, nx )
    ys = np.linspace( 0.0, Ly, ny )
    zs = np.linspace( 0.0, Lz, nz )
    return np.array( [ [ xs[ i ], ys[ j ], zs[ k ] ] for i in range( nx ) for j in range( ny ) for k in range( nz ) ],
                     dtype=float )


def _gen_rect_yz_z_major( Ly: float, Lz: float, ny: int, nz: int, fixx: float, offy: int,
                          offz: int ) -> npt.NDArray[ np.float64 ]:
    """Rectangular grid in the Y–Z plane at x = fixx; z fastest, then y.

    Trims offy rows on each y-side and offz rows on each z-side.
    Row stride in the returned array is  nz - 2*offz.
    """
    ys = np.linspace( 0.0, Ly, ny )
    zs = np.linspace( 0.0, Lz, nz )
    return np.array( [ [ fixx, ys[ j ], zs[ k ] ] for j in range( offy, ny - offy ) for k in range( offz, nz - offz ) ],
                     dtype=float )


def _patterned_indices_z_major( nx: int, ny: int, nz: int ) -> npt.NDArray[ np.intp ]:
    """Checkerboard-patterned index selection for the z-major point grid.

    Returns every other point per row with alternating start (parity),
    producing a non-uniform "shifted" distribution suitable for
    an irregular Delaunay tetra mesh.
    """
    blocks = []
    for row in range( nx * ny ):
        x = row // ny
        y = row % ny
        parity = ( x % 2 ) ^ ( y % 2 )
        start = row * nz + parity
        blocks.append( np.arange( start, ( row + 1 ) * nz, 2 ) )
    return np.concatenate( blocks )


def _paint_and_append( main: vtkUnstructuredGrid, fracs: list[ vtkUnstructuredGrid ] ) -> vtkUnstructuredGrid:
    """Combine volume mesh and fracture meshes, attaching an 'attribute' array.

    The 'attribute' value is 1 for matrix cells and 2, 3, … for each fracture
    in the order they appear in *fracs*.  This is the layout expected by
    mesh-doctor's generateFractures action.
    """
    append = vtkAppendFilter()
    append.MergePointsOff()
    append.AddInputData( main )
    for frac in fracs:
        append.AddInputData( frac )
    append.Update()
    output: vtkUnstructuredGrid = append.GetOutput()

    n_main = main.GetNumberOfCells()
    n_total = output.GetNumberOfCells()

    attr = vtkIntArray()
    attr.SetName( "attribute" )
    attr.SetNumberOfComponents( 1 )
    attr.SetNumberOfTuples( n_total )

    for c in range( n_main ):
        attr.SetValue( c, 1 )
    offset = n_main
    for fi, frac in enumerate( fracs ):
        for c in range( frac.GetNumberOfCells() ):
            attr.SetValue( offset + c, fi + 2 )
        offset += frac.GetNumberOfCells()

    output.GetCellData().AddArray( attr )
    return output


# ──────────────────────────────────────────────────────────────
# Public mesh generators  (from mesh_gen.py --gen branch)
# ──────────────────────────────────────────────────────────────


def build_hex_mesh( nx: int = 5,
                    ny: int = 5,
                    nz: int = 5,
                    Lx: float = 1.0,
                    Ly: float = 1.0,
                    Lz: float = 1.0 ) -> vtkUnstructuredGrid:
    """Regular hexahedral mesh with z-major point ordering (the "shifted" variant).

    Points are stored with x slowest, z fastest.  VTK hex nodes follow the
    standard ordering: bottom face (k, k+1) then top face (i+1 slab), matching
    the z-major CELL_ORDERING from mesh_gen.py.

    Args:
        nx: Number of nodes in x (cells = nx-1).
        ny: Number of nodes in y (cells = ny-1).
        nz: Number of nodes in z (cells = nz-1).
        Lx: Domain length in x.
        Ly: Domain length in y.
        Lz: Domain length in z.

    Returns:
        vtkUnstructuredGrid with (nx-1)*(ny-1)*(nz-1) VTK_HEXAHEDRON cells.
    """
    pts = _gen_box_z_major( Lx, Ly, Lz, nx, ny, nz )

    mesh = vtkUnstructuredGrid()
    mesh.Allocate( ( nx - 1 ) * ( ny - 1 ) * ( nz - 1 ) )
    vpts = vtkPoints()
    vpts.SetData( numpy_to_vtk( pts ) )
    mesh.SetPoints( vpts )

    for i in range( nx - 1 ):
        for j in range( ny - 1 ):
            for k in range( nz - 1 ):
                # z-major base index: k + j*nz + i*nz*ny
                base = k + j * nz + i * nz * ny
                ids = vtkIdList()
                ids.InsertNextId( base )  # VTK node 0: (i  , j  , k  )
                ids.InsertNextId( base + nz * ny )  # VTK node 1: (i+1, j  , k  )
                ids.InsertNextId( base + nz * ny + nz )  # VTK node 2: (i+1, j+1, k  )
                ids.InsertNextId( base + nz )  # VTK node 3: (i  , j+1, k  )
                ids.InsertNextId( base + 1 )  # VTK node 4: (i  , j  , k+1)
                ids.InsertNextId( base + nz * ny + 1 )  # VTK node 5: (i+1, j  , k+1)
                ids.InsertNextId( base + nz * ny + nz + 1 )  # VTK node 6: (i+1, j+1, k+1)
                ids.InsertNextId( base + nz + 1 )  # VTK node 7: (i  , j+1, k+1)
                mesh.InsertNextCell( VTK_HEXAHEDRON, ids )

    return mesh


def build_tetra_mesh( nx: int = 5,
                      ny: int = 5,
                      nz: int = 5,
                      Lx: float = 1.0,
                      Ly: float = 1.0,
                      Lz: float = 1.0 ) -> vtkUnstructuredGrid:
    """Tetrahedral mesh built via Delaunay3D on a full z-major grid.

    Uses all (nx*ny*nz) grid points as Delaunay input, yielding a structured
    but tetrahedral discretisation.  Equivalent to mesh_gen.py --tri --structured.

    Args:
        nx: Node count along x.
        ny: Node count along y.
        nz: Node count along z.
        Lx: Domain extent along x.
        Ly: Domain extent along y.
        Lz: Domain extent along z.

    Returns:
        vtkUnstructuredGrid of VTK_TETRA cells.
    """
    pts = _gen_box_z_major( Lx, Ly, Lz, nx, ny, nz )
    cloud = vtkPolyData()
    vpts = vtkPoints()
    vpts.SetData( numpy_to_vtk( pts ) )
    cloud.SetPoints( vpts )

    delaunay = vtk.vtkDelaunay3D()
    delaunay.SetInputData( cloud )
    delaunay.Update()
    return delaunay.GetOutput()


def build_tetra_mesh_patterned( nx: int = 5,
                                ny: int = 5,
                                nz: int = 5,
                                Lx: float = 1.0,
                                Ly: float = 1.0,
                                Lz: float = 1.0 ) -> vtkUnstructuredGrid:
    """Irregular ("shifted") tetrahedral mesh via Delaunay3D on checkerboard-filtered points.

    Every other grid point is dropped in a checkerboard pattern before
    Delaunay triangulation, producing a more irregular connectivity that
    exercises more code paths in mesh-doctor checks.  Equivalent to
    mesh_gen.py --tri (unstructured variant, odd nx forced if even).

    Args:
        nx: Node count in x; incremented to odd if even (required by patterning).
        ny: Node count along y.
        nz: Node count along z.
        Lx: Domain extent along x.
        Ly: Domain extent along y.
        Lz: Domain extent along z.

    Returns:
        vtkUnstructuredGrid of VTK_TETRA cells.
    """
    if nx % 2 == 0:
        nx += 1

    pts = _gen_box_z_major( Lx, Ly, Lz, nx, ny, nz )
    pts = pts[ _patterned_indices_z_major( nx, ny, nz ), : ]

    cloud = vtkPolyData()
    vpts = vtkPoints()
    vpts.SetData( numpy_to_vtk( pts ) )
    cloud.SetPoints( vpts )

    delaunay = vtk.vtkDelaunay3D()
    delaunay.SetInputData( cloud )
    delaunay.Update()
    return delaunay.GetOutput()


def build_hex_mesh_with_fractures( nx: int = 5,
                                   ny: int = 5,
                                   nz: int = 5,
                                   Lx: float = 1.0,
                                   Ly: float = 1.0,
                                   Lz: float = 1.0,
                                   offx: int = 1,
                                   offy: int = 1,
                                   nfrac: int = 1 ) -> vtkUnstructuredGrid:
    """Hex mesh with embedded quad fracture surfaces.

    Fractures are Y–Z planes located at  x = Lx / (2^nfrac) * (i+1)  for
    i = 0 … nfrac-1.  Each fracture surface is trimmed by *offx* nodes on
    each z-side and *offy* nodes on each y-side so it doesn't touch the domain
    boundary.

    The returned mesh has an 'attribute' cell data array:
      1  → matrix cells
      2, 3, …  → fracture cells (in insertion order).

    This layout is consumed by mesh-doctor's generateFractures action.

    Args:
        nx: Node count along x.
        ny: Node count along y.
        nz: Node count along z.
        Lx: Domain extent along x.
        Ly: Domain extent along y.
        Lz: Domain extent along z.
        offx: Trim margin in z (nodes to skip on each z-side of fracture).
        offy: Trim margin in y (nodes to skip on each y-side of fracture).
        nfrac: Number of fracture planes to embed.

    Returns:
        vtkUnstructuredGrid with VTK_HEXAHEDRON + VTK_QUAD cells and 'attribute'.
    """
    main = build_hex_mesh( nx, ny, nz, Lx, Ly, Lz )
    fracs: list[ vtkUnstructuredGrid ] = []
    stride = nz - 2 * offx  # points per row on the fracture surface (z-direction)

    for fi in range( nfrac ):
        x_pos = Lx / ( 2**nfrac ) * ( fi + 1 )
        pts = _gen_rect_yz_z_major( Ly, Lz, ny, nz, x_pos, offy, offx )

        frac = vtkUnstructuredGrid()
        vpts = vtkPoints()
        vpts.SetData( numpy_to_vtk( pts ) )
        frac.SetPoints( vpts )
        frac.Allocate()

        for j in range( ny - 1 - 2 * offy ):
            for k in range( nz - 1 - 2 * offx ):
                base = k + j * stride
                ids = vtkIdList()
                ids.InsertNextId( base )
                ids.InsertNextId( base + 1 )
                ids.InsertNextId( base + stride + 1 )
                ids.InsertNextId( base + stride )
                frac.InsertNextCell( VTK_QUAD, ids )
        fracs.append( frac )

    return _paint_and_append( main, fracs )


def build_tetra_mesh_with_fractures( nx: int = 5,
                                     ny: int = 5,
                                     nz: int = 5,
                                     Lx: float = 1.0,
                                     Ly: float = 1.0,
                                     Lz: float = 1.0,
                                     offx: int = 1,
                                     offy: int = 1,
                                     nfrac: int = 1 ) -> vtkUnstructuredGrid:
    """Tetra mesh with embedded triangulated fracture surfaces.

    Fractures are Y–Z planes triangulated via vtkDelaunay2D on a trimmed
    rectangular point cloud.  Equivalent to mesh_gen.py --tri --quad=False.
    The returned mesh has an 'attribute' cell data array (same convention as
    build_hex_mesh_with_fractures).

    Args:
        nx: Node count along x.
        ny: Node count along y.
        nz: Node count along z.
        Lx: Domain extent along x.
        Ly: Domain extent along y.
        Lz: Domain extent along z.
        offx: Trim margin in z for fracture surfaces.
        offy: Trim margin in y for fracture surfaces.
        nfrac: Number of fracture planes.

    Returns:
        vtkUnstructuredGrid with VTK_TETRA + VTK_TRIANGLE cells and 'attribute'.
    """
    main = build_tetra_mesh( nx, ny, nz, Lx, Ly, Lz )
    fracs: list[ vtkUnstructuredGrid ] = []

    for fi in range( nfrac ):
        x_pos = Lx / ( 2**nfrac ) * ( fi + 1 )
        pts = _gen_rect_yz_z_major( Ly, Lz, ny, nz, x_pos, offy, offx )

        cloud = vtkPolyData()
        vpts = vtkPoints()
        vpts.SetData( numpy_to_vtk( pts ) )
        cloud.SetPoints( vpts )

        delaunay = vtk.vtkDelaunay2D()
        delaunay.SetInputData( cloud )
        delaunay.SetProjectionPlaneMode( vtk.VTK_BEST_FITTING_PLANE )
        delaunay.Update()
        tri_poly = delaunay.GetOutput()

        frac = vtkUnstructuredGrid()
        frac.SetPoints( tri_poly.GetPoints() )
        frac.Allocate()
        for c in range( tri_poly.GetNumberOfCells() ):
            cell = tri_poly.GetCell( c )
            frac.InsertNextCell( cell.GetCellType(), cell.GetPointIds() )
        fracs.append( frac )

    return _paint_and_append( main, fracs )


# ──────────────────────────────────────────────────────────────
# Non-manifold edge configurations
# ──────────────────────────────────────────────────────────────


def build_surface_with_non_manifold_edge() -> vtkUnstructuredGrid:
    """Surface mesh with one edge shared by three quad faces (non-manifold).

    Layout (edge 1–2 is the non-manifold edge)::

        Quad A  z=0 plane  x ∈ [0,1]
        Quad B  z=0 plane  x ∈ [1,2]
        Quad C  x=1 plane  perpendicular "flap"

        Points:
          0:(0,0,0)  1:(1,0,0)  2:(1,1,0)  3:(0,1,0)
          4:(2,0,0)  5:(2,1,0)
          6:(1,0,1)  7:(1,1,1)   ← flap top edge

        Edge 1–2 (x=1, y∈[0,1], z=0) appears in A, B, and C → non-manifold.

    Detected by ``euler.meshAction`` as ``numNonManifoldEdges > 0``
    (applied to the surface mesh directly, not via volume extraction).

    Returns:
        vtkUnstructuredGrid of 3 VTK_QUAD cells.
    """
    coords = [
        ( 0.0, 0.0, 0.0 ),  # 0
        ( 1.0, 0.0, 0.0 ),  # 1  ← shared-edge endpoint
        ( 1.0, 1.0, 0.0 ),  # 2  ← shared-edge endpoint
        ( 0.0, 1.0, 0.0 ),  # 3
        ( 2.0, 0.0, 0.0 ),  # 4
        ( 2.0, 1.0, 0.0 ),  # 5
        ( 1.0, 0.0, 1.0 ),  # 6
        ( 1.0, 1.0, 1.0 ),  # 7
    ]
    mesh = _make_ugrid( coords )
    for quad_pts in [ ( 0, 1, 2, 3 ), ( 1, 4, 5, 2 ), ( 1, 6, 7, 2 ) ]:
        _add_cell( mesh, VTK_QUAD, quad_pts )
    return mesh


def build_volume_with_non_manifold_edge() -> vtkUnstructuredGrid:
    """Two hexahedra sharing only one edge (bowtie / pinched configuration).

    Hex A occupies [0,1]³.  Hex B occupies [1,2]×[1,2]×[0,1].
    They share exactly the edge from (1,1,0) to (1,1,1).

    On the extracted boundary surface that edge is surrounded by four faces
    (two from each hex), making it a non-manifold boundary edge::

        Boundary faces containing edge (1,1,0)→(1,1,1):
          Hex A  x-max face: (1,0,0)-(1,1,0)-(1,1,1)-(1,0,1)
          Hex A  y-max face: (0,1,0)-(1,1,0)-(1,1,1)-(0,1,1)
          Hex B  x-min face: (1,1,0)-(1,2,0)-(1,2,1)-(1,1,1)
          Hex B  y-min face: (1,1,0)-(2,1,0)-(2,1,1)-(1,1,1)

    Detected by ``euler.meshAction`` as ``numNonManifoldEdges > 0``.

    Returns:
        vtkUnstructuredGrid of 2 VTK_HEXAHEDRON cells (14 points).
    """
    coords = [
        # Hex A: [0,1]³
        ( 0.0, 0.0, 0.0 ),
        ( 1.0, 0.0, 0.0 ),
        ( 1.0, 1.0, 0.0 ),
        ( 0.0, 1.0, 0.0 ),  # 0-3
        ( 0.0, 0.0, 1.0 ),
        ( 1.0, 0.0, 1.0 ),
        ( 1.0, 1.0, 1.0 ),
        ( 0.0, 1.0, 1.0 ),  # 4-7
        # Hex B: [1,2]×[1,2]×[0,1] — points 2 and 6 from Hex A are reused
        ( 2.0, 1.0, 0.0 ),
        ( 2.0, 2.0, 0.0 ),
        ( 1.0, 2.0, 0.0 ),  # 8-10
        ( 2.0, 1.0, 1.0 ),
        ( 2.0, 2.0, 1.0 ),
        ( 1.0, 2.0, 1.0 ),  # 11-13
    ]
    mesh = _make_ugrid( coords )
    _add_cell( mesh, VTK_HEXAHEDRON, ( 0, 1, 2, 3, 4, 5, 6, 7 ) )  # Hex A
    _add_cell( mesh, VTK_HEXAHEDRON, ( 2, 8, 9, 10, 6, 11, 12, 13 ) )  # Hex B (reuses 2,6)
    return mesh


# ──────────────────────────────────────────────────────────────
# Mesh-doctor targeted defect configurations
# ──────────────────────────────────────────────────────────────


def build_mesh_with_collocated_nodes() -> vtkUnstructuredGrid:
    """Two adjacent hexahedra whose shared-face nodes are duplicated in place.

    The mesh has 16 points instead of 12: the four nodes on the shared face
    (x=1 plane) are represented twice at identical coordinates.

    Expected result from ``collocatedNodes.meshAction``::

        len(result.nodesBuckets) == 4
        each bucket contains 2 node IDs

    Returns:
        vtkUnstructuredGrid of 2 VTK_HEXAHEDRON cells with 16 points.
    """
    coords = [
        # Hex A  [0,1]³
        ( 0.0, 0.0, 0.0 ),
        ( 1.0, 0.0, 0.0 ),
        ( 1.0, 1.0, 0.0 ),
        ( 0.0, 1.0, 0.0 ),  # 0-3
        ( 0.0, 0.0, 1.0 ),
        ( 1.0, 0.0, 1.0 ),
        ( 1.0, 1.0, 1.0 ),
        ( 0.0, 1.0, 1.0 ),  # 4-7
        # Hex B  [1,2]³ — points 8,11,12,15 are collocated duplicates of 1,2,5,6
        ( 1.0, 0.0, 0.0 ),
        ( 2.0, 0.0, 0.0 ),
        ( 2.0, 1.0, 0.0 ),
        ( 1.0, 1.0, 0.0 ),  # 8-11
        ( 1.0, 0.0, 1.0 ),
        ( 2.0, 0.0, 1.0 ),
        ( 2.0, 1.0, 1.0 ),
        ( 1.0, 1.0, 1.0 ),  # 12-15
    ]
    mesh = _make_ugrid( coords )
    _add_cell( mesh, VTK_HEXAHEDRON, ( 0, 1, 2, 3, 4, 5, 6, 7 ) )
    _add_cell( mesh, VTK_HEXAHEDRON, ( 8, 9, 10, 11, 12, 13, 14, 15 ) )
    return mesh


def build_mesh_with_orphan_2d_cells() -> vtkUnstructuredGrid:
    """One hex with one matching quad face and one orphan quad not matching any 3D face.

    Layout::

        Hex:       unit cube [0,1]³   (nodes 0-7)
        Quad M:    z=0 face of the hex (nodes 0,1,2,3)  → matched
        Quad O:    z=2 plane          (nodes 8,9,10,11) → orphan

    Expected result from ``orphan2d.meshAction``::

        result.matched2dCells   == 1
        result.orphaned2dCells  == 1
        result.orphaned2dIndices == [2]   (third cell, 0-indexed)

    Returns:
        vtkUnstructuredGrid of 1 VTK_HEXAHEDRON + 2 VTK_QUAD cells.
    """
    coords = [
        ( 0.0, 0.0, 0.0 ),
        ( 1.0, 0.0, 0.0 ),
        ( 1.0, 1.0, 0.0 ),
        ( 0.0, 1.0, 0.0 ),  # 0-3 hex base
        ( 0.0, 0.0, 1.0 ),
        ( 1.0, 0.0, 1.0 ),
        ( 1.0, 1.0, 1.0 ),
        ( 0.0, 1.0, 1.0 ),  # 4-7 hex top
        ( 0.0, 0.0, 2.0 ),
        ( 1.0, 0.0, 2.0 ),
        ( 1.0, 1.0, 2.0 ),
        ( 0.0, 1.0, 2.0 ),  # 8-11 orphan
    ]
    mesh = _make_ugrid( coords )
    _add_cell( mesh, VTK_HEXAHEDRON, ( 0, 1, 2, 3, 4, 5, 6, 7 ) )  # hex
    _add_cell( mesh, VTK_QUAD, ( 0, 1, 2, 3 ) )  # matched  (face [0,1,2,3])
    _add_cell( mesh, VTK_QUAD, ( 8, 9, 10, 11 ) )  # orphan
    _add_cell( mesh, VTK_QUAD, ( 0, 3, 6, 5 ) )  # orphan
    return mesh


def build_mesh_with_negative_volume() -> vtkUnstructuredGrid:
    """Two hexahedra: one correctly oriented, one with top/bottom faces swapped (inverted).

    Swapping the bottom and top node groups of a VTK hex reverses the
    Jacobian sign, yielding a negative volume.

    Expected result from ``elementVolumes.meshAction(mesh, Options(minVolume=0))``::

        len(result.elementVolumes) == 1
        result.elementVolumes[0][0] == 1   (second cell)

    Returns:
        vtkUnstructuredGrid of 2 VTK_HEXAHEDRON cells.
    """
    coords = [
        # Hex A  [0,1]³  correct ordering
        ( 0.0, 0.0, 0.0 ),
        ( 1.0, 0.0, 0.0 ),
        ( 1.0, 1.0, 0.0 ),
        ( 0.0, 1.0, 0.0 ),  # 0-3
        ( 0.0, 0.0, 1.0 ),
        ( 1.0, 0.0, 1.0 ),
        ( 1.0, 1.0, 1.0 ),
        ( 0.0, 1.0, 1.0 ),  # 4-7
        # Hex B  [2,3]³  inverted: bottom/top groups swapped
        ( 2.0, 0.0, 0.0 ),
        ( 3.0, 0.0, 0.0 ),
        ( 3.0, 1.0, 0.0 ),
        ( 2.0, 1.0, 0.0 ),  # 8-11  ← physical bottom
        ( 2.0, 0.0, 1.0 ),
        ( 3.0, 0.0, 1.0 ),
        ( 3.0, 1.0, 1.0 ),
        ( 2.0, 1.0, 1.0 ),  # 12-15 ← physical top
    ]
    mesh = _make_ugrid( coords )
    _add_cell( mesh, VTK_HEXAHEDRON, ( 0, 1, 2, 3, 4, 5, 6, 7 ) )  # Hex A  correct
    _add_cell( mesh, VTK_HEXAHEDRON, ( 12, 13, 14, 15, 8, 9, 10, 11 ) )  # Hex B  top→bottom first
    return mesh


def build_mesh_with_self_intersecting_elements() -> vtkUnstructuredGrid:
    """Two hexahedra that geometrically overlap in the x ∈ [0.5, 1.0] band.

    Hex A spans [0,1]³; Hex B spans [0.5,1.5]×[0,1]×[0,1].  They share no
    mesh nodes but their geometric extents intersect.

    Expected result from ``selfIntersectingElements.meshAction``::

        The pair (0, 1) is reported as intersecting.

    Returns:
        vtkUnstructuredGrid of 2 VTK_HEXAHEDRON cells (16 points, no shared nodes).
    """
    coords = [
        # Hex A  [0,1]³
        ( 0.0, 0.0, 0.0 ),
        ( 1.0, 0.0, 0.0 ),
        ( 1.0, 1.0, 0.0 ),
        ( 0.0, 1.0, 0.0 ),  # 0-3
        ( 0.0, 0.0, 1.0 ),
        ( 1.0, 0.0, 1.0 ),
        ( 1.0, 1.0, 1.0 ),
        ( 0.0, 1.0, 1.0 ),  # 4-7
        # Hex B  [0.5,1.5]×[0,1]×[0,1]
        ( 0.5, 0.0, 0.0 ),
        ( 1.5, 0.0, 0.0 ),
        ( 1.5, 1.0, 0.0 ),
        ( 0.5, 1.0, 0.0 ),  # 8-11
        ( 0.5, 0.0, 1.0 ),
        ( 1.5, 0.0, 1.0 ),
        ( 1.5, 1.0, 1.0 ),
        ( 0.5, 1.0, 1.0 ),  # 12-15
    ]
    mesh = _make_ugrid( coords )
    _add_cell( mesh, VTK_HEXAHEDRON, ( 0, 1, 2, 3, 4, 5, 6, 7 ) )
    _add_cell( mesh, VTK_HEXAHEDRON, ( 8, 9, 10, 11, 12, 13, 14, 15 ) )
    return mesh


# ──────────────────────────────────────────────────────────────
# Internal construction helpers
# ──────────────────────────────────────────────────────────────


def _make_ugrid( coords: list[ tuple[ float, float, float ] ] ) -> vtkUnstructuredGrid:
    """Create an empty vtkUnstructuredGrid with the given point coordinates."""
    points = vtkPoints()
    for c in coords:
        points.InsertNextPoint( c )
    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.Allocate()
    return mesh


def _add_cell( mesh: vtkUnstructuredGrid, cell_type: int, point_ids: tuple[ int, ...] ) -> None:
    """Append one cell to *mesh* in-place."""
    ids = vtkIdList()
    for pid in point_ids:
        ids.InsertNextId( pid )
    mesh.InsertNextCell( cell_type, ids )
