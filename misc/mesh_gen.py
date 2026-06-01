import vtk
import numpy as np
import numpy.typing as npt
from typing import List,Tuple
from vtk import (vtkUnstructuredGrid, vtkPoints, vtkIdList, vtkIdTypeArray, vtkPolyData,
                vtkHexahedron, vtkQuad,
                vtkAppendFilter, vtkCleanPolyData, vtkGeometryFilter, vtkDelaunay3D, vtkIntArray,
                VTK_HEXAHEDRON, VTK_QUAD,
                VTK_TETRA)
from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
import logging
from collections import defaultdict
import argparse
from time import perf_counter

TOLERANCE = 1e-6
CELL_ORDERING = [0,1,2,3,4,5,6,7] #none
CELL_ORDERING = [0,1,6,5,3,2,6,7] #x-major
CELL_ORDERING = [0,4,7,3,1,5,6,2] #z-major

def is_surface_cell_type(t):
    """Return True if cell type is surface-like."""
    surface_types = {
        vtk.VTK_TRIANGLE,
        vtk.VTK_QUAD,
        vtk.VTK_POLYGON,
        vtk.VTK_TRIANGLE_STRIP,
        # add VTK_LINE, VTK_VERTEX here if you want to accept them
    }
    return t in surface_types

def __globalFaces(main):
    """Mesh applier of __getCellFacePoints"""
    globalFaces = set()
    for i in range(main.GetNumberOfCells()):
        cell = main.GetCell(i)
        if not is_surface_cell_type(cell.GetCellType()):
            for face in __getCellFacePoints(cell):
                globalFaces.add(face)
    

    return globalFaces

def _face_edges(face):
   """Return sorted edges of a face (tri or quad)."""
   n = len(face)
   return [
        tuple(sorted((face[i], face[(i + 1) % n])))
        for i in range(n)
    ]

def __pointToFace(faceToPoint):
    pointToFace = defaultdict(list)
    for face in faceToPoint:
        for id in face:
            pointToFace[id].append(face)
    return pointToFace

def __getNormal(main,face):
    """
    Compute a unit normal from face vertex coordinates.

    Args:
        points: (N, 3) array of vertex coordinates (N >= 3)

    Returns:
        Unit normal vector (3,)
    """
    p0, p1, p2 = [ main.GetPoint(i) for i in face ]

    v1 = p1 - p0
    v2 = p2 - p0

    n = np.cross(v1, v2)
    norm = np.linalg.norm(n)

    if norm == 0.0:
        raise ValueError("Degenerate face: zero-area")

    return n / norm

def __getNormals(main,facelist):
    normals = defaultdict(list)
    for cellid in range(main.GetNumberOfCells()):
        for face in facelist[cellid]:
            normals[face].append(__getNormals(main,face))
    
    return normals



def build_face_adjacency_graph(mesh: vtk.vtkUnstructuredGrid):
    """
    Build a face adjacency graph from a 3D mesh.

    Returns:
        dict[tuple[int,...], set[tuple[int,...]]]
        Mapping: face -> adjacent faces
    """
    edge_to_faces = defaultdict(list)
    face_graph = defaultdict(set)

    # --- Extract all faces ---
    for cell_id in range(mesh.GetNumberOfCells()):
        cell = mesh.GetCell(cell_id)
        if is_surface_cell_type(cell.GetCellType()):
            continue
        faces = __getCellFacePoints(cell)

        for face in faces:
            for edge in _face_edges(face):
                edge_to_faces[edge].append(face)

    # --- Build adjacency ---
    for faces in edge_to_faces.values():
        if len(faces) > 1:
            for i in range(len(faces)):
                for j in range(i + 1, len(faces)):
                    f1, f2 = faces[i], faces[j]
                    face_graph[f1].add(f2)
                    face_graph[f2].add(f1)

    return face_graph


def __getCellFacePoints( cell: vtk.vtkCell ) -> list[ tuple[ int, ...] ]:
    """Extract all face point sets from a 3D cell.

    Args:
        cell: A 3D VTK cell.

    Returns:
        List of tuples containing sorted global point IDs for each face.
    """
    faces = []
    cellType = cell.GetCellType()

    if cellType == vtk.VTK_TETRA:
        # 4 triangular faces
        faces = [ [ 0, 1, 2 ], [ 0, 1, 3 ], [ 0, 2, 3 ], [ 1, 2, 3 ] ]
    elif cellType == vtk.VTK_HEXAHEDRON:
        # 6 quadrilateral faces
        faces = [ [ 0, 1, 2, 3 ], [ 4, 5, 6, 7 ], [ 0, 1, 5, 4 ], [ 1, 2, 6, 5 ], [ 2, 3, 7, 6 ], [ 3, 0, 4, 7 ] ]
    elif cellType == vtk.VTK_WEDGE:
        # 2 triangular + 3 quadrilateral faces
        faces = [ [ 0, 1, 2 ], [ 3, 4, 5 ], [ 0, 1, 4, 3 ], [ 1, 2, 5, 4 ], [ 2, 0, 3, 5 ] ]
    elif cellType == vtk.VTK_PYRAMID:
        # 1 quadrilateral + 4 triangular faces
        faces = [ [ 0, 1, 2, 3 ], [ 0, 1, 4 ], [ 1, 2, 4 ], [ 2, 3, 4 ], [ 3, 0, 4 ] ]
    else:
        raise NotImplementedError(
            f"Orphan2d is not implemented for cell type {cellType}. It is supported for TETRAHEDRA ({vtk.VTK_TETRA}), HEXA ({vtk.VTK_HEXAHEDRON}), WEDGE ({vtk.VTK_WEDGE}) and PYRAMID ({vtk.VTK_PYRAMID})"
        )
    # Convert local indices to global point IDs
    pointIds = cell.GetPointIds()
    globalFaces = []
    for face in faces:
        #sort to make comparison permutation invariant
        globalFace = tuple( sorted( [ pointIds.GetId( i ) for i in face ] ) )
        globalFaces.append( globalFace )

    return globalFaces

# def patterned_indices_vectorized(nx, ny, nz)[0]:
#     rows = np.arange(ny * nz)
#     y = rows % ny
#     z = rows // ny

#     # Combined y–z stagger
#     parity = (y % 2) ^ (z % 2)

#     starts = rows * nx + parity
#     offs = np.arange(0, nx, 2)

#     idx = starts[:, None] + offs[None, :]
#     idx = idx[idx < nx * ny * nz]   # clip overflow from odd rows

#     return idx

# Recursive function to process blocks
def __process_block(block, append_filter,attrs):
    if isinstance(block, vtk.vtkMultiBlockDataSet):
        # Traverse sub-blocks recursively
        for i in range(block.GetNumberOfBlocks()):
            child = block.GetBlock(i)
            if child is not None:
                __process_block(child, append_filter,attrs)

    else:
    # Only vtkPointSet subclasses have cells
        if not hasattr(block, "GetNumberOfCells"):
            return

        n_cells = block.GetNumberOfCells()
        if n_cells == 0:
            return

        # Get first cell type
        cell_type = block.GetCellType(0)

        # If it's surface-like, keep it
        if is_surface_cell_type(cell_type):
            # Convert non-polydata surface datasets (e.g., unstructured grids)
            if (len(attrs)>0 and block.GetCellData().GetArray("attribute").GetTuple1(0) in attrs) or len(attrs)==0:
                if isinstance(block, vtk.vtkPolyData):
                        append_filter.AddInputData(block)
                else:
                    # Convert to PolyData (e.g., surface blocks stored in UGrid)
                    gf = vtk.vtkGeometryFilter()
                    gf.SetInputData(block)
                    gf.Update()
                    append_filter.AddInputData(gf.GetOutput())
       
def __extract_vol(block):
    if isinstance(block, vtk.vtkMultiBlockDataSet):
        # Traverse sub-blocks recursively
        for i in range(block.GetNumberOfBlocks()):
            child = block.GetBlock(i)
            if child is not None:
                return __extract_vol(child)

    else:
        # Only vtkPointSet subclasses have cells
        if not hasattr(block, "GetNumberOfCells"):
            return

        n_cells = block.GetNumberOfCells()
        if n_cells == 0:
            return

        is_vol = False
        # Get first cell type
        for i in range(block.GetNumberOfCells()):
            cell_type = block.GetCellType(i)
            is_vol |= not is_surface_cell_type(cell_type)
        
        return block if is_vol else None

def __clean_collocated(main):
    #CleanData
    clean_point_set = defaultdict(list)
    reverse_map = dict()
    start = perf_counter()
    for id in range(main.GetNumberOfPoints()):
        if len(clean_point_set[main.GetPoints().GetPoint(id)])>0:
            reverse_map[id] = clean_point_set[main.GetPoints().GetPoint(id)][0]
        clean_point_set[main.GetPoints().GetPoint(id)].append(id)
    end = perf_counter()
    print(f"  time[assemble_clean_set] {end-start:.5f}s")

    old_to_new = {}
    start = perf_counter()
    clean_points = vtk.vtkPoints()
    for pt,id in clean_point_set.items():
        new_id = clean_points.InsertNextPoint(pt)
        old_to_new[id[0]] = new_id
    end = perf_counter()
    print(f"  time[form mapping] {end-start:.5f}s")
    
    rewrite_mesh = vtk.vtkUnstructuredGrid()
    rewrite_mesh.SetPoints(clean_points)
    
    start = perf_counter()
    
# Reuse id lists to avoid reallocations
    for cell_id in range(main.GetNumberOfCells()):
        cell = main.GetCell(cell_id)

        # Collect remapped point IDs
        new_ids = []
        for i in range(cell.GetNumberOfPoints()):
            pid = cell.GetPointId(i)
            # new_ids.append(old_to_new[find_first_value(clean_point_set.values(),pid)])
            if pid in reverse_map.keys():
                new_ids.append(old_to_new[reverse_map[pid]])
            else:
                new_ids.append(old_to_new[pid])


        rewrite_mesh.InsertNextCell(cell.GetCellType(), len(new_ids), new_ids)
    end = perf_counter()
    print(f"  time[map cells] {end-start:.5f}s")

    
    start = perf_counter()
    # (4) Copy cell data
    rewrite_mesh.GetCellData().ShallowCopy(main.GetCellData())

    # (5) Copy point data for remaining points
    for array_i in range(main.GetPointData().GetNumberOfArrays()):
        arr = main.GetPointData().GetArray(array_i)
        new_arr = vtk.vtkDataArray.CreateDataArray(arr.GetDataType())
        new_arr.SetName(arr.GetName())
        new_arr.SetNumberOfComponents(arr.GetNumberOfComponents())
        new_arr.SetNumberOfTuples(clean_points.GetNumberOfPoints())

        for old_id, new_id in old_to_new.items():
            new_arr.SetTuple(new_id, arr.GetTuple(old_id))

        rewrite_mesh.GetPointData().AddArray(new_arr)
    end = perf_counter()
    print(f"  time[copy data] {end-start:.5f}s")

    return rewrite_mesh

def meshDoctor_to_surfaceGen(hierachical_mesh, attrs):
    #check collocation
    #write node set
    # Container to append surface meshes
    append_filter = vtk.vtkAppendPolyData()

    # Start recursion
    start = perf_counter()
    sstart = perf_counter()
    __process_block(hierachical_mesh,append_filter, attrs)
    send = perf_counter()
    print(f" time[_process_block] {send-sstart:.5f}s")

    sstart = perf_counter()
    main = __extract_vol(hierachical_mesh)
    send = perf_counter()
    print(f" time[_extract_vol] {send-sstart:.5f}s")
    
    sstart = perf_counter()
    rewrite_mesh = __clean_collocated(main)
    send = perf_counter()
    print(f" time[_clean_collocated] {send-sstart:.5f}s")

    end = perf_counter()
    print(f"time[_processBlocks] {end-start:.5f}s")

    # Combine all leaf surfaces
    append_filter.Update()

    # # Clean to merge duplicate points
    start = perf_counter()
    clean = vtk.vtkCleanPolyData()
    clean.SetInputConnection(append_filter.GetOutputPort())
    clean.Update()
    end = perf_counter()
    print(f"time[cleanFilter] {end-start:.5f}s")

    start = perf_counter()
    painted = __paintNodes(rewrite_mesh, clean.GetOutput())
    end = perf_counter()
    print(f"time[_paint_Nodes] {end-start:.5f}s")
    return polydata_to_ugrid( painted[0] )

def ugrid_to_polydata(ugrid):
    """
    Convert vtkPolyData (points + polys) to a vtkUnstructuredGrid.
    Assumes polys are triangles or polygons.
    """
    poly = vtk.vtkPolyData()

    # Copy points
    poly.SetPoints(ugrid.GetPoints())

    # Loop through all cells in polydata
    num_cells = ugrid.GetNumberOfCells()
    for cid in range(num_cells):
        cell = ugrid.GetCell(cid)
        cell_type = cell.GetCellType()
        point_ids = cell.GetPointIds()

        # Insert into unstructured grid
        poly.InsertNextCell(
            cell_type,
            point_ids
        )

    # Copy point/cell data
    poly.GetPointData().ShallowCopy(ugrid.GetPointData())
    poly.GetCellData().ShallowCopy(ugrid.GetCellData())

    return poly

def polydata_to_ugrid(poly):
    """
    Convert vtkPolyData (points + polys) to a vtkUnstructuredGrid.
    Assumes polys are triangles or polygons.
    """
    ugrid = vtk.vtkUnstructuredGrid()

    # Copy points
    ugrid.SetPoints(poly.GetPoints())

    # Loop through all cells in polydata
    num_cells = poly.GetNumberOfCells()
    for cid in range(num_cells):
        cell = poly.GetCell(cid)
        cell_type = cell.GetCellType()
        point_ids = cell.GetPointIds()

        # Insert into unstructured grid
        ugrid.InsertNextCell(
            cell_type,
            point_ids
        )

    # Copy point/cell data
    ugrid.GetPointData().ShallowCopy(poly.GetPointData())
    ugrid.GetCellData().ShallowCopy(poly.GetCellData())

    return ugrid

def __gen_box( Lx: int, Ly: int, Lz: int, nx: int, ny: int, nz: int ) -> Tuple[ npt.NDArray[ np.double ], npt.NDArray[ np.double ] ]:
    pts: List[ npt.NDArray[ np.double ] ] = []
    x = np.linspace(0, Lx, nx)
    y = np.linspace(0, Ly, ny)
    z = np.linspace(0, Lz, nz)
    for k in range( nz ):
        for j in range( ny ):
            for i in range( nx ):
                pts.append( np.asarray( [ x[ i ], y[ j ], z[ k ] ] ) )

    return np.asarray( pts )


def __gen_box_z_major(Lx: float, Ly: float, Lz: float, nx: int, ny: int, nz: int) -> npt.NDArray[np.double]:

    pts = []

    x = np.linspace(0, Lx, nx)
    y = np.linspace(0, Ly, ny)
    z = np.linspace(0, Lz, nz)

    # z fastest, then y, then x
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                pts.append([x[i], y[j], z[k]])

    return np.asarray(pts)

def __gen_rect( Lx: int, Ly: int, nx: int, ny: int, fixz: int,  offx: int, offy: int) -> Tuple[ npt.NDArray[ np.double ], npt.NDArray[ np.double ] ]:
    pts: List[ npt.NDArray[ np.double ] ] = []
    x, y = np.meshgrid( np.linspace( 0, Lx, nx ), np.linspace( 0, Ly, ny ) , indexing ='ij')
    for j in range( offy, x.shape[ 1 ] - offy ):
        for i in range( offx,  x.shape[ 0 ] - offx):
                pts.append( np.asarray( [ x[ i, j ], y[ i, j ], fixz ] ) )

    return np.asarray( pts )

def __gen_rect_yz_z_major(
    Ly: float,
    Lz: float,
    ny: int,
    nz: int,
    fixx: float,
    offy: int,
    offz: int
) -> npt.NDArray[np.double]:
    """
    Generate a rectangular grid of points in the Y–Z plane at x = fixx.

    Ordering:
      - z is the fastest-varying direction (inner loop)
      - then y

    Linear index (after trimming):
      id = k + j * nz2
      where nz2 = nz - 2*offz
    """

    ys = np.linspace(0.0, Ly, ny)
    zs = np.linspace(0.0, Lz, nz)

    pts: List[npt.NDArray[np.double]] = []

    for j in range(offy, ny - offy):        # y (slow)
        for k in range(offz, nz - offz):    # z (fast)
            pts.append(
                np.asarray([fixx, ys[j], zs[k]], dtype=float)
            )

    return np.asarray(pts, dtype=float)

def __gen_rect_z_major(Lx: float, Ly: float,nx: int, ny: int,fixz: float,offx: int, offy: int) -> npt.NDArray[np.double]:
    """
    Generate a rectangular grid of points on the plane z = fixz.
    Points are ordered with x (i) varying fastest, then y (j),
    so linear indexing is id = i + j*nx2, where nx2 = nx - 2*offx.
    """
    # Sample coordinates
    xs = np.linspace(0.0, Lx, nx)
    ys = np.linspace(0.0, Ly, ny)

    pts: List[npt.NDArray[np.double]] = []

    # Trim margins by offx/offy and emit in (j, i) loops with i fastest
    for j in range(offy, ny - offy):
        for i in range(offx, nx - offx):
            pts.append(np.asarray([xs[i], ys[j], fixz], dtype=float))

    return np.asarray(pts, dtype=float)


def __globalIds(mesh):

    mapCallback = { "POINTS" : ( mesh.GetNumberOfPoints(), mesh.GetPointData() ),
                   "CELLS"  : ( mesh.GetNumberOfCells(), mesh.GetCellData() ) }

    for k,v in mapCallback.items():
        gids = vtkIdTypeArray()
        gids.SetName( f"GLOBAL_IDS_{k}" )
        gids.Allocate( v[0] )
        for i in range( v[0] ):
            gids.InsertNextValue( i )
        v[1].SetGlobalIds( gids )

# def __collocatedNodes(main, frac):


#     #no collocated nodes assumption
#     array = numpy_to_vtk( np.ones((frac.GetNumberOfPoints(), 0), dtype=int) * -1 )
#     array.SetName("collocated_nodes") 
#     frac.GetPointData().AddArray( array )

#     #todo later

def __paintAndAppend(main: vtkUnstructuredGrid, fracs: list) -> vtkUnstructuredGrid:

    # 1. Append raw geometry first, no attributes yet
    append = vtkAppendFilter()
    append.MergePointsOff()
    append.AddInputData(main)
    for frac in fracs:
        append.AddInputData(frac)
    append.Update()
    output: vtkUnstructuredGrid = append.GetOutput()

    # 2. Build the attribute array on the *output* cell count
    n_cells_main = main.GetNumberOfCells()
    n_cells_total = output.GetNumberOfCells()

    attr = vtkIntArray()
    attr.SetName("attribute")
    attr.SetNumberOfComponents(1)
    attr.SetNumberOfTuples(n_cells_total)   # sized against the final merged grid

    # main cells come first in vtkAppendFilter output order
    for c in range(n_cells_main):
        attr.SetValue(c, 1)

    # fracture cells follow, in the order they were added
    offset = n_cells_main
    for i, frac in enumerate(fracs):
        n = frac.GetNumberOfCells()
        for c in range(n):
            attr.SetValue(offset + c, i + 2)
        offset += n

    output.GetCellData().AddArray(attr)

    return output

def __propagate(main,seeds,rounds):
    
    # kd = vtk.vtkKdTree()
    # kd.BuildLocatorFromPoints(main)

    globalFaces = __globalFaces(main)
    faceGraph = build_face_adjacency_graph(main)
    normals = __getNormals(main,globalFaces)
    
    for _ in range(rounds):
        new_seeds = []
        for seed in seeds:
            ids = vtk.vtkIdList()
            # kd.FindClosestNPoints(5,main.GetPoint(seed), ids)

            for id in range(ids.GetNumberOfIds()):
                if main.GetPointData().GetArray("faultNodes").GetTuple1(ids.GetId(id)) == 0:
                    new_seeds.append(ids.GetId(id))
                    new_faces = faceGraph(globalFaces,new_seeds)
                    main.GetPointData().GetArray("faultNodes").InsertTuple1(ids.GetId(id),1)
                    print(f"new points {ids.GetId(id)}")
                    

def __paintNodes(main,fracs):
    kd = vtk.vtkKdTree()
    kd.BuildLocatorFromPoints(main)
    
    narray = np.ones((main.GetNumberOfPoints(), 1), dtype=int) * 0
    # narrayc = np.ones((main.GetNumberOfCells(), 1), dtype=int)

    for frac in fracs:
        for i in range(frac.GetNumberOfPoints()):
            dist = vtk.reference(0.)
            id_source = kd.FindClosestPoint(frac.GetPoint(i), dist)
            if dist>TOLERANCE:
                logging.warning(f"[too far point] main point ({id_source}) is too far from frac point ({i}) = ({dist} > {TOLERANCE})")
            
            narray[id_source] = 1

        array = numpy_to_vtk(narray)
        array.SetName("faultNodes") 
        main.GetPointData().AddArray(array)

    return main,fracs

def __patterned_indices(nx, ny, nz):
    idx_blocks = []

    nrows = ny * nz

    for row in range(nrows):
        y = row % ny        # which row in y within the layer
        z = row // ny       # which layer in z

        # Combined stagger pattern in y and z
        parity = (y % 2) ^ (z % 2)

        start = row * nx + parity
        block_idx = np.arange(start, (row + 1) * nx, 2)
        idx_blocks.append(block_idx)

    return np.concatenate(idx_blocks)

def __patterned_indices_z_major(nx: int, ny: int, nz: int):
    idx_blocks = []

    nrows = nx * ny
    for row in range(nrows):
        y = row % ny
        x = row // ny

        # stagger in x/y instead of y/z
        parity = (x % 2) ^ (y % 2)

        start = row * nz + parity
        block_idx = np.arange(start, (row + 1) * nz, 2)

        idx_blocks.append(block_idx)

    return np.concatenate(idx_blocks)

# def __patterned_indices(nx, ny, nz):
#     idx_blocks = []

#     for k in range(ny * nz):
#         start = k * nx + (1 if (k % 2) == 1 else 0)
#         block_idx = np.arange(start, (k + 1) * nx, 2)
#         idx_blocks.append(block_idx)

#     return np.concatenate(idx_blocks)


def __build_reg_tri():

    pts: npt.NDArray[ np.double ]

    ny = np.ceil( Ly/(Lx/nx*np.sqrt(3)/2) )
    nz = ny
    print(f"Overwritten ny :: {ny}")
    pts = __gen_box( Lx, Ly, Lz, int(nx), int(ny), int(nz))
    pts = pts[__patterned_indices_z_major(int(nx),int(ny),int(nz)),:]

    # Creating multiple meshes, each time with a different angles
    mesh = vtkPolyData()
    vpts = vtkPoints()
    vpts.SetData( dsa.numpy_support.numpy_to_vtk( pts ) )
    mesh.SetPoints( vpts )
    tetra = vtk.vtkDelaunay3D()
    tetra.SetInputData(mesh)
    tetra.Update()

    yield tetra.GetOutput()

def __buid_test_mesh_tri():
     #test all quadrant
    pts: npt.NDArray[ np.double ]
    # pts = __gen_box( Lx, Ly, Lz, nx, ny, nz)
    pts = __gen_box_z_major( Lx, Ly, Lz, nx, ny, nz)

    # Creating multiple meshes, each time with a different angles
    mesh = vtkPolyData()
    vpts = vtkPoints()
    vpts.SetData( dsa.numpy_support.numpy_to_vtk( pts ) )
    mesh.SetPoints( vpts )
    tetra = vtk.vtkDelaunay3D()
    tetra.SetInputData(mesh)
    # tetra.SetAlpha(0.0)  # set >0 to clip away large empty regions (alpha shapes)
    tetra.Update()

    yield tetra.GetOutput()


def __build_test_mesh():
    # generate random points in a box Lx, Ly, Lz
    # np.random.seed(1) # for reproducibility


    #test all quadrant
    pts: npt.NDArray[ np.double ]
    # pts = __gen_box_z( Lx, Ly, Lz, nx, ny, nz)
    pts = __gen_box_z_major( Lx, Ly, Lz, nx, ny, nz)

    # Creating multiple meshes, each time with a different angles
    mesh = vtkUnstructuredGrid()
    mesh.Allocate( (nx-1)*(ny-1)*(nz-1) )
    vpts = vtkPoints()
    vpts.SetData( dsa.numpy_support.numpy_to_vtk( pts ) )
    mesh.SetPoints( vpts )

    ids = vtkIdList()
    # for k in range( nz - 1 ):
    #     for j in range( ny - 1 ):
    #         for i in range( nx - 1 ):
    #             hex = vtkHexahedron()
    #             ids = hex.GetPointIds()
    #             base = i + j * nx + k * nx * ny
    
    for i in range(nx - 1):
        for j in range(ny - 1):
            for k in range(nz - 1):

                hex = vtkHexahedron()
                ids = hex.GetPointIds()
                base = k + j*nz + i*nz*ny

                ids.SetId( CELL_ORDERING[0], g:= base )
                # print(f"point 0 : {g} {mesh.GetPoint(g)}")
                ids.SetId( CELL_ORDERING[1], g:= base + 1)
                ids.SetId( CELL_ORDERING[2], g:= base + 1 + nz )
                ids.SetId( CELL_ORDERING[3], g:= base + nz )

                ids.SetId( CELL_ORDERING[4], g:= base + nz*ny )
                ids.SetId( CELL_ORDERING[5], g:= base + nz*ny + 1 )
                ids.SetId( CELL_ORDERING[6], g:= base + nz * ny + 1 + nz)
                ids.SetId( CELL_ORDERING[7], g:= base + nz * ny + nz )
                mesh.InsertNextCell( VTK_HEXAHEDRON, ids )

    # __globalIds(mesh)
    yield mesh

# def __build_test_frac(off : Tuple[int, ... ],nfrac: int):
#        #test all quadrant
#     offx: int
#     offy: int
#     offx, offy = off
#     pts: npt.NDArray[ np.double ]
#     off: npt.NDArray[ np.double ]
#     # pts = __gen_rect(tag, Lz, Ly, nz, ny, fixz:= Lx/2, offx, offy )
#     for l in range(nfrac):
#         z = Lx/(2**nfrac) * (l+1)

#         pts = __gen_rect_yz_z_major(Ly, Lz, ny, nz, z, offx, offy )
#         print(f"check pts {pts}")

#         # Creating multiple meshes, each time with a different angles
#         mesh = vtkUnstructuredGrid()
#         vpts = vtkPoints()
#         vpts.SetData( dsa.numpy_support.numpy_to_vtk( pts ) )
#         mesh.SetPoints( vpts )
#         mesh.Allocate( (nz-1-2*offx)*(ny-1-2*offy) )

#         ids = vtkIdList()
#         for j in range( ny - 1 - 2*offy ):
#             for i in range( nz - 1 - 2*offx ):
#                     quad = vtkQuad()
#                     ids = quad.GetPointIds()
#                     base = i + j*(nz-2*offx)
#                     ids.SetId( 0, k:= base )
#                     ids.SetId( 1, k:= base + 1 )
#                     ids.SetId( 2, k:= base + (nz-2*offx) +1 )
#                     ids.SetId( 3, k:= base + (nz-2*offx)  )
#                     mesh.InsertNextCell( VTK_QUAD, ids )

#         # __globalIds(mesh)
#         # __collocatedNodes(mesh,mesh)
        # yield mesh 
def __build_test_frac(off: Tuple[int, ...], nfrac: int):
    offx: int
    offy: int
    offx, offy = off

    for fi in range(nfrac):                          # fix: renamed to fi, no shadowing
        z = Lx / (2 ** nfrac) * (fi + 1)

        pts: npt.NDArray[np.double] = __gen_rect_yz_z_major(Ly, Lz, ny, nz, z, offx, offy)
        print(f"check pts {pts}")

        mesh = vtkUnstructuredGrid()
        vpts = vtkPoints()
        vpts.SetData(dsa.numpy_support.numpy_to_vtk(pts))
        mesh.SetPoints(vpts)
        mesh.Allocate()                              # fix: required before InsertNextCell

        # row stride matches z-major layout from __gen_rect_yz_z_major
        # each row has (nz - 2*offx) points
        stride = nz - 2 * offx                      # fix: named once, verify against generator

        for j in range(ny - 1 - 2 * offy):
            for k in range(nz - 1 - 2 * offx):      # fix: renamed to k, no shadowing
                quad = vtkQuad()
                ids = quad.GetPointIds()
                base = k + j * stride
                ids.SetId(0, base)
                ids.SetId(1, base + 1)
                ids.SetId(2, base + stride + 1)
                ids.SetId(3, base + stride)
                mesh.InsertNextCell(VTK_QUAD, ids)

        yield mesh

def __build_test_frac_tri( off: Tuple[int, ...], nfrac: int ):
    #test all quadrant
    offx: int
    offy: int
    offx, offy = off
    pts: npt.NDArray[ np.double ]
    off: npt.NDArray[ np.double ]
    # pts = __gen_rect( Lx, Ly, nx, ny, fixz:= Lz/2, offx, offy )
    
    for i in range(nfrac):
        z = Lx/(2**nfrac) * (i+1)
        pts = __gen_rect_yz_z_major(Ly, Lz, ny, nz, z, offx, offy )

        # Creating multiple meshes, each time with a different angles
        mesh = vtkPolyData()
        vpts = vtkPoints()
        vpts.SetData( dsa.numpy_support.numpy_to_vtk( pts ) )
        mesh.SetPoints( vpts )

        delaunay = vtk.vtkDelaunay2D()
        delaunay.SetInputData(mesh)
        delaunay.SetProjectionPlaneMode(vtk.VTK_BEST_FITTING_PLANE)
        # Optional tweaks:
        # delaunay.SetTolerance(0.001)
        # delaunay.SetAlpha(0.0)  # alpha shapes; >0 to clip outside radius
        delaunay.Update()


        # __globalIds(mesh)
        # __collocatedNodes(mesh,mesh)
        yield polydata_to_ugrid(delaunay.GetOutput())


def __build_test_frac_tri_reg(off: Tuple[int, ...], nfrac: int):
    offx: int
    offy: int
    offx, offy = off

    # fix: compute ny once — it does not depend on the loop variable
    ny: int = int(np.ceil(Ly / (Lx / nx * np.sqrt(3) / 2)))
    print(f"Computed ny :: {ny}")

    for i in range(nfrac):
        # fix: linear Z spacing — original ternary produced (1, MAX, MAX, …)
        z = Lz / (2 ** nfrac) * (i + 1)

        pts: npt.NDArray[np.double] = __gen_rect(
            Lx, Ly, int(nx), ny, z, offx, offy
        )
        print(f"check n x off {nx} {ny} {offx} {offy}")
        print(f"check pts {pts}")
       
        patterned = __patterned_indices_z_major(int(nx), ny, 1)
        print(f"check patterned {patterned}")
        pts = pts[patterned, :]

        mesh = vtkPolyData()
        vpts = vtkPoints()
        vpts.SetData(dsa.numpy_support.numpy_to_vtk(pts))
        mesh.SetPoints(vpts)

        delaunay = vtk.vtkDelaunay2D()
        delaunay.SetInputData(mesh)
        # fix: force projection onto the best-fit plane so non-XY point
        #      clouds triangulate correctly
        delaunay.SetProjectionPlaneMode(vtk.VTK_BEST_FITTING_PLANE)
        delaunay.Update()

        yield delaunay.GetOutput()

def __preprocess_data(poly):
    # maybe preprocessed
    cl = vtk.vtkCleanPolyData()
    cl.SetInputData(poly)
    cl.PointMergingOn()
    cl.Update()
    tri = vtk.vtkTriangleFilter()
    tri.SetInputConnection(cl.GetOutputPort())
    tri.Update()
    nn = vtk.vtkPolyDataNormals()
    nn.SetInputConnection(tri.GetOutputPort())
    nn.ConsistencyOn()
    nn.SplittingOff()
    nn.AutoOrientNormalsOn()
    nn.Update()

    yield nn


def __set_union(main,frac):
    # maybe preprocessed
    cl = vtk.vtkCleanPolyData()
    cl.SetInputData(poly)
    cl.PointMergingOn()
    cl.Update()
    tri = vtk.vtkTriangleFilter()
    tri.SetInputConnection(cl.GetOutputPort())
    tri.Update()
    nn = vtk.vtkPolyDataNormals()
    nn.SetInputConnection(tri.GetOutputPort())
    nn.ConsistencyOn()
    nn.SplittingOff()
    nn.AutoOrientNormalsOn()
    nn.Update()

    boolean = vtk.vtkBooleanOperationPolyDataFilter()
    boolean.SetOperation(vtk.vtkBooleanOperationPolyDataFilter.VTK_INTERSECTION)
    boolean.SetInputData(0,nna)
    boolean.SetInputData(1,nnb)
    boolean.Update()

    yield boolean.GetOutput()

if "__main__" == __name__:

    parser = argparse.ArgumentParser(description="A simple fracture mesh generator")

    parser.add_argument("-g","--gen", action="store_true" ,default=False)
    parser.add_argument("-n","--npoints",type=int,nargs=3,default=[5,5,101])
    parser.add_argument("-l","--size",type=float,nargs=3,default=[.1,.1,1.])
    parser.add_argument("-s","--shift",type=int,nargs=2,default=[0,0])
    
    parser.add_argument("-f","--nfrac",type=int,nargs=1,default=1)

    parser.add_argument("-t","--tri", action="store_true" ,default=False)
    parser.add_argument("-q","--quad",action="store_true" ,default=False)
    parser.add_argument("-x","--structured",action="store_true" ,default=False)
    
    # parser.add_argument("-o","--name",type=str, required=True)
    parser.add_argument("-o","--name",type=str, default="bobo")
    
    # convert 
    parser.add_argument("-c","--convert", type=str, nargs=1 ,default=False)
    parser.add_argument("-z","--attrs",type=int,nargs='+',default=[])

    # parser.add_argument("-p","--propagate", type=str, nargs=1 ,default=False)
    parser.add_argument("-p","--propagate",action="store_true" ,default=False)
    parser.add_argument("-m","--seeds", type=int, nargs='+' ,default=False)
    parser.add_argument("-r","--rounds", type=int, nargs=1 ,default=1)

    args = parser.parse_args()

    if args.gen:
        # Lx = 1.
        # Ly = 0.1
        # Lz = 0.1
        # nx = 101
        # ny = 5
        # nz = 5
        nx,ny,nz = args.npoints
        Lx,Ly,Lz = args.size
        sx,sy = args.shift

        l = [None]
        ts = [None]
        
        writer = vtk.vtkXMLUnstructuredGridWriter()
        writer.SetFileName(f'{args.name}.vtu')
        if args.quad and not args.tri:
            
            l = list(__build_test_mesh())
            print(l[0].GetBounds())
            print(l[0].GetNumberOfCells())
            
            # t = list(__build_test_frac((sx,sy)))
            ts = list(  __build_test_frac((sx,sy),nfrac=args.nfrac[0]) )
              


        elif not args.quad and args.tri:

            if args.structured:
                l = list(__buid_test_mesh_tri())
                print(l[0].GetBounds())
                print(l[0].GetNumberOfCells())

                ts = list(__build_test_frac_tri((sx,sy), nfrac= args.nfrac[0]))

            else:
                if (nx % 2) == 0:
                    nx+=1
                l = list(__build_reg_tri())
                print(l[0].GetBounds())
                print(l[0].GetNumberOfCells())

                for t in __build_test_frac_tri_reg((sx,sy), nfrac= args.nfrac[0]):
                    print(t.GetBounds())
                    print(t.GetNumberOfCells())
                    copy = vtk.vtkUnstructuredGrid()
                    copy.DeepCopy(t)
                    ts.append(copy)

                # _set_union(l[0],t[0])
            
        # surface generator versions 
        # __paintNodes(l[0],ts)
        # w2 = vtk.vtkXMLUnstructuredGridWriter()
        # w2.SetFileName(f"{args.name}_isg.vtu")
        # w2.SetInputData(l[0])
        # w2.Write()

        # mesh doctor versions

        m = __paintAndAppend(l[0],ts)
        print(f"m: {m.GetNumberOfCells()}")
        print(f"m: {m.GetNumberOfPoints()}")
        writer.SetInputData(m)
        writer.Write()


        # writer = vtk.vtkXMLMultiBlockDataWriter()
        # writer.SetFileName('base_hex.vtm')
        # mb = vtk.vtkMultiBlockDataSet()
        # mb.SetNumberOfBlocks(2)
        # mb.SetBlock(0, l[0])
        # mb.SetBlock(1, t[0])

        # name_key = vtk.vtkCompositeDataSet.NAME()
        # mb.GetMetaData(0).Set(name_key, "main")
        # mb.GetMetaData(1).Set(name_key, "fault")
        # writer.SetInputData(mb)
        # writer.Write()
    
    elif args.convert:

        r = vtk.vtkXMLMultiBlockDataReader()
        r.SetFileName(args.convert[0])
        r.Update()

        m = r.GetOutput()
        o = meshDoctor_to_surfaceGen(m, args.attrs)
        print(o.GetBounds())
        print(o.GetNumberOfPoints())
        print(o.GetNumberOfCells())
        
        if args.propagate:
            __propagate(o,args.seeds,args.rounds[0])

        bname = ''.join(args.convert[0].split('.')[:-1])

        w2 = vtk.vtkXMLUnstructuredGridWriter()
        w2.SetFileName(f"{bname}_converted.vtu")
        w2.SetInputData(o)
        w2.Write()
    
        

        


