import vtk
import time
from vtkmodules.vtkCommonDataModel import vtkBoundingBox
from enum import IntEnum   
import numpy as np

######################COPILOT LAZY FRIDAY - TO REVIEW ############################

from collections import defaultdict
from vtk.util import numpy_support as ns

def _cell_centroids(ug: vtk.vtkUnstructuredGrid) -> np.ndarray:
    n = ug.GetNumberOfCells()
    centroids = np.zeros((n, 3), dtype=np.float64)
    pts = ug.GetPoints()
    for cid in range(n):
        cell = ug.GetCell(cid)
        ids = cell.GetPointIds()
        xyz = np.array([pts.GetPoint(ids.GetId(i)) for i in range(ids.GetNumberOfIds())], dtype=np.float64)
        centroids[cid] = xyz.mean(axis=0)
    return centroids

def _build_point_adjacency(ug: vtk.vtkUnstructuredGrid):
    n = ug.GetNumberOfCells()
    point2cells = defaultdict(list)
    for cid in range(n):
        ids = ug.GetCell(cid).GetPointIds()
        for i in range(ids.GetNumberOfIds()):
            point2cells[ids.GetId(i)].append(cid)
    neighbors = [set() for _ in range(n)]
    for cid in range(n):
        ids = ug.GetCell(cid).GetPointIds()
        for i in range(ids.GetNumberOfIds()):
            pid = ids.GetId(i)
            for nb in point2cells[pid]:
                if nb != cid:
                    neighbors[cid].add(nb)
    return [np.fromiter(s, dtype=np.int32) for s in neighbors]

def _build_face_adjacency(ug: vtk.vtkUnstructuredGrid):
    """
    Strict adjacency (shared face). Only works when VTK can enumerate faces.
    Falls back to empty for cells where faces can't be queried.
    """
    n = ug.GetNumberOfCells()
    face2cells = defaultdict(list)
    for cid in range(n):
        cell = ug.GetCell(cid)
        nf = cell.GetNumberOfFaces()
        if nf is None or nf <= 0:
            continue
        for fi in range(nf):
            face = cell.GetFace(fi)
            fids = [face.GetPointId(i) for i in range(face.GetNumberOfPoints())]
            key = tuple(sorted(fids))
            face2cells[key].append(cid)
    neighbors = [set() for _ in range(n)]
    for cells in face2cells.values():
        if len(cells) >= 2:
            for a in cells:
                for b in cells:
                    if a != b:
                        neighbors[a].add(b)
    return [np.fromiter(s, dtype=np.int32) for s in neighbors]

def gaussian_cell_smooth(
    ug: vtk.vtkUnstructuredGrid,
    array_name: str,
    sigma: float = 1.0,
    self_weight: float = 1.0,
    iterations: int = 1,
    adjacency: str = "point",  # 'point' (default) or 'face'
):
    """
    Gaussian local smoothing for CELL data on an unstructured grid.
    Weights = exp( -0.5 * (d/sigma)^2 ), where d is centroid distance.

    Parameters
    ----------
    ug : vtkUnstructuredGrid
        Input mesh (modified in-place by adding a new cell array).
    array_name : str
        Name of the cell data array to smooth.
    sigma : float
        Gaussian sigma in world units (same units as point coordinates).
    self_weight : float
        Weight for the cell's own value (stabilizes smoothing).
    iterations : int
        Number of smoothing passes (more passes ≈ stronger blur).
    adjacency : {'point', 'face'}
        How to define neighbors. 'point' is more inclusive and robust.
    out_name : str | None
        Name for the output array. Defaults to '{array_name}_gauss'.

    Returns
    -------
    ug, out_name
        The same ug with a new cell array added.
    """
    if sigma <= 0:
        raise ValueError("sigma must be > 0")

    n_cells = ug.GetNumberOfCells()
    in_vtk = ug.GetCellData().GetArray(array_name)
    if in_vtk is None:
        raise ValueError(f"Cell array '{array_name}' not found.")
    X = ns.vtk_to_numpy(in_vtk)
    if X.ndim == 1:
        X = X[:, None]  # (N,1) for scalars
    n_comp = X.shape[1]

    # Adjacency
    if adjacency == "face":
        N = _build_face_adjacency(ug)
        # Fallback to point neighbors for cells with no face neighbors
        if any(nb.size == 0 for nb in N):
            N_point = _build_point_adjacency(ug)
            N = [nb if nb.size > 0 else N_point[i] for i, nb in enumerate(N)]
    else:
        N = _build_point_adjacency(ug)

    # Geometry
    C = _cell_centroids(ug)

    Xk = X.copy()
    for _ in range(iterations):
        Xnext = np.empty_like(Xk)
        for cid in range(n_cells):
            nb = N[cid]
            if nb.size == 0:
                Xnext[cid] = Xk[cid]
                continue
            d = np.linalg.norm(C[nb] - C[cid], axis=1)  # Euclidean distance between centroids
            w = np.exp(-0.5 * (d / sigma) ** 2)
            wsum = w.sum() + self_weight
            num = (w[:, None] * Xk[nb]).sum(axis=0) + self_weight * Xk[cid]
            Xnext[cid] = num / (wsum if wsum > 0 else 1.0)
        Xk = Xnext

    out_name = f"{array_name}_gauss"

    out = ns.numpy_to_vtk(Xk if n_comp > 1 else Xk.ravel(), deep=True)
    out.SetName(out_name)
    ug.GetCellData().AddArray(out)
    return ug


####################################################################################
class PIECE(IntEnum):
    ONPOINT =  1
    ONCELL = 2


block2block = [[]] # map index of the source blocks itersecting the target blocks 

def clamp_interpolate(mesh_source, mesh_target, _get_points):

    #because of distributed vtm format we use distributed datastruct (e.g. list are list of list then reduced)
    kd = vtk.vtkKdTree()
    kd.BuildLocatorFromPoints( _get_points(mesh_source))

    tg_pts = _get_points( mesh_target)
    source2target = [[] for i in range(tg_pts.GetNumberOfPoints())] # map index from source to target
    for i in range(tg_pts.GetNumberOfPoints()):
        dist = vtk.reference(0.)
        id_source = kd.FindClosestPoint(tg_pts.GetPoint(i),dist)
        source2target[i].append( (dist,id_source) )
    
    return source2target

# def _within_block(i, box_target):

#     for iblock, block in mesh_source:
#         block2block[itarget].append( iblock if vtkBoundingBox( block.bounds() ).IntersectBox( box_target ) )


def reduce(listOfList):
    return [min(llist)[1] for llist in listOfList]


def _get_cellCenters(mesh):
    centers = vtk.vtkCellCenters()
    centers.SetInputData(mesh)
    centers.Update()

    return centers.GetOutput().GetPoints()

def _vectorize_fields_out(fieldnames, mesh, piece):
    from vtk.util.numpy_support import vtk_to_numpy
    #use numpy for some speedup
    #assuming any vector fields will not have more than 9 components
    fieldnc = []
    if piece == PIECE.ONPOINT: 
        fp = np.zeros(shape=(mesh.GetNumberOfPoints(), len(fieldnames),9), dtype=float)
    elif piece == PIECE.ONCELL:
        fp = np.zeros(shape=(mesh.GetNumberOfCells(), len(fieldnames),9), dtype=float)

    for j,field in enumerate(fieldnames):
        if piece == PIECE.ONPOINT:
            if not mesh.GetPointData().HasArray(field[0]):
                print(f"{field[0]} is not an array of  point data's source mesh")
            else:
                data = mesh.GetPointData().GetArray(field[0])
                fieldnc.append(data.GetNumberOfComponents())
        elif piece == PIECE.ONCELL:
            if not mesh.GetCellData().HasArray(field[0]):
                print(f"{field[0]} is not an array of cell data's source mesh")
            else:
                data = mesh.GetCellData().GetArray(field[0])
                fieldnc.append(data.GetNumberOfComponents())

        fp[:,j,:fieldnc[-1]] = vtk_to_numpy(data).reshape(-1,fieldnc[-1])
    
    return fp, fieldnc

def _vectorize_fields_in(fieldnames, fieldnc,  mesh, fp,  piece):
    from vtk.util.numpy_support import numpy_to_vtk
    #use numpy for some speedup

    for j,field in enumerate(fieldnames):
        arr = numpy_to_vtk(fp[:,j,:fieldnc[j]])
        arr.SetName(field[1])
        if piece == PIECE.ONPOINT:
            mesh.GetPointData().AddArray(arr)
        elif piece == PIECE.ONCELL:
            mesh.GetCellData().AddArray(arr)

    return fp

def _filter_volume_cells(mesh, save_surfaces=True, output_prefix=""):
    """Keep only 3D volume cells; optionally save 2D cells to VTU."""
    print(f"  Input mesh: {mesh.GetNumberOfCells()} cells")

    volume_ids  = vtk.vtkIdTypeArray()
    surface_ids = vtk.vtkIdTypeArray()
    n_volume = n_surface = n_other = 0

    for i in range(mesh.GetNumberOfCells()):
        dim = mesh.GetCell(i).GetCellDimension()
        if   dim == 3: volume_ids.InsertNextValue(i);  n_volume  += 1
        elif dim == 2: surface_ids.InsertNextValue(i); n_surface += 1
        else:                                          n_other   += 1

    print(f"  Cell types: {n_volume} volume (3D) | "
          f"{n_surface} surface (2D) | {n_other} other")

    if n_surface > 0 and save_surfaces:
        sn = vtk.vtkSelectionNode()
        sn.SetFieldType(vtk.vtkSelectionNode.CELL)
        sn.SetContentType(vtk.vtkSelectionNode.INDICES)
        sn.SetSelectionList(surface_ids)
        sel = vtk.vtkSelection(); sel.AddNode(sn)
        ext = vtk.vtkExtractSelection()
        ext.SetInputData(0, mesh); ext.SetInputData(1, sel); ext.Update()
        surf = vtk.vtkUnstructuredGrid(); surf.ShallowCopy(ext.GetOutput())
        fname = f"{output_prefix}_surfaces_only.vtu" if output_prefix else "surfaces_only.vtu"
        w = vtk.vtkXMLUnstructuredGridWriter()
        w.SetFileName(fname); w.SetInputData(surf); w.Write()
        print(f"Saved surface cells → {fname}")

    if n_surface == 0 and n_other == 0:
        print("No filtering needed (all cells are 3D)")
        return mesh

    sn = vtk.vtkSelectionNode()
    sn.SetFieldType(vtk.vtkSelectionNode.CELL)
    sn.SetContentType(vtk.vtkSelectionNode.INDICES)
    sn.SetSelectionList(volume_ids)
    sel = vtk.vtkSelection(); sel.AddNode(sn)
    ext = vtk.vtkExtractSelection()
    ext.SetInputData(0, mesh); ext.SetInputData(1, sel); ext.Update()
    out = vtk.vtkUnstructuredGrid(); out.ShallowCopy(ext.GetOutput())
    print(f"  ✅ Filtered → {out.GetNumberOfCells()} cells "
          f"(removed {n_surface + n_other})")
    return out


# ============================================================
# REGION EXTRACTION HELPER
# ============================================================

def _extract_region(mesh, attr_name, region_ids):
    """
    Return a sub-mesh containing only cells whose integer attribute
    value is in *region_ids*, together with the original cell indices.

    Parameters
    ----------
    mesh       : vtkUnstructuredGrid
    attr_name  : str    name of the integer cell-data attribute
    region_ids : list[int]

    Returns
    -------
    sub_mesh      : vtkUnstructuredGrid  (shallow copy)
    orig_indices  : numpy (N_sub,) int   original cell indices in *mesh*
    """
    if not mesh.GetCellData().HasArray(attr_name):
        available = [mesh.GetCellData().GetArrayName(i)
                     for i in range(mesh.GetCellData().GetNumberOfArrays())]
        raise KeyError(
            f"Attribute '{attr_name}' not found.\n"
            f"  Available arrays: {available}")

    attr   = vtk_to_numpy(mesh.GetCellData().GetArray(attr_name)).astype(np.int64)
    mask   = np.zeros(len(attr), dtype=bool)
    for rid in region_ids:
        mask |= (attr == rid)

    orig_indices = np.where(mask)[0]

    if len(orig_indices) == 0:
        return None, orig_indices

    # Build vtkIdTypeArray of selected indices
    id_arr = vtk.vtkIdTypeArray()
    for idx in orig_indices:
        id_arr.InsertNextValue(int(idx))

    sn = vtk.vtkSelectionNode()
    sn.SetFieldType(vtk.vtkSelectionNode.CELL)
    sn.SetContentType(vtk.vtkSelectionNode.INDICES)
    sn.SetSelectionList(id_arr)
    sel = vtk.vtkSelection(); sel.AddNode(sn)

    ext = vtk.vtkExtractSelection()
    ext.SetInputData(0, mesh); ext.SetInputData(1, sel); ext.Update()

    sub = vtk.vtkUnstructuredGrid()
    sub.ShallowCopy(ext.GetOutput())

    return sub, orig_indices

def main():

    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/4_GNL_Biot.vtu')
    # reader.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/GNL_update_biot.vtu') #name of the source mesh
    reader.Update()
    source_mesh = reader.GetOutput()

    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/4_GNL_refined_target.vtu')
    # reader.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/GNL_hexdom7.vtu') # name of the target mesh
    reader.Update()
    target_mesh = reader.GetOutput()

    section = 'mapping'
    start = time.perf_counter()
    pt_s2t = reduce( clamp_interpolate( source_mesh, target_mesh, lambda m : m.GetPoints() ) )
    c_s2t = reduce( clamp_interpolate( source_mesh, target_mesh, lambda m : _get_cellCenters(m) ) )
    end = time.perf_counter()
    print(f"[{section}] Elapsed time: {end - start:.6f} seconds")

    print("Checking for few index c2c and p2p mappings")
    print(pt_s2t[1:10])
    print(c_s2t[1:10])

    section = 'Vectorizing'
    start = time.perf_counter()
    c_fieldnames = [('Porosity','mapped_POROSITY'), ('PERM','mapped_PERM')] # for GNL test
    # pt_fieldnames = [('','')]
    c_source_vec, c_fieldnc = _vectorize_fields_out(c_fieldnames,source_mesh, PIECE.ONCELL)
    
    # ----------------------------------------------------------------
    # REGION-BASED MAPPING
    # ----------------------------------------------------------------
    section = 'Mapping (KD-tree, per region)'
    print(f"[{section}]")
    start = time.perf_counter()

    # Prepare output array (same shape as target, initialised to previous fields)
    N_tgt         = target_mesh.GetNumberOfCells()
    # c_target_vec  = np.zeros((N_tgt, len(FIELD_NAMES), 9), dtype=float)
    c_target_vec, _ = _vectorize_fields_out(FIELD_NAMES, target_mesh, PIECE.ONCELL)

    for src_ids, tgt_id in REGION_MAP:

        print(f"\n  ── Region: source {src_ids} → target [{tgt_id}] ──")

        # Extract source sub-mesh for this region
        src_sub, src_orig_idx = _extract_region(source_mesh, ATTRIBUTE_NAME,
                                                src_ids)
        if src_sub is None:
            print(f"No source cells found for ids {src_ids} — skipping.")
            continue
        print(f"     Source cells : {len(src_orig_idx)}")

        # Extract target sub-mesh for this region
        tgt_sub, tgt_orig_idx = _extract_region(target_mesh, ATTRIBUTE_NAME,
                                                [tgt_id])
        if tgt_sub is None:
            print(f"No target cells found for id {tgt_id} — skipping.")
            continue
        print(f"     Target cells : {len(tgt_orig_idx)}")

        # KD-tree mapping on sub-meshes (original clamp_interpolate logic)
        raw = clamp_interpolate(src_sub, tgt_sub,
                                lambda m: _get_cellCenters(m))
        # local_s2t: index within src_sub → map back to src_orig_idx
        local_s2t = reduce(raw)

        # local_s2t[i] is an index within src_sub  (0..N_src_sub-1)
        # src_orig_idx[local_s2t[i]] is the original index in source_mesh
        global_s2t = src_orig_idx[np.array(local_s2t, dtype=np.int64)]

        # Transfer: for each target sub-cell i, copy from global source index
        c_target_vec[tgt_orig_idx] = c_source_vec[global_s2t]

        # Quick value check
        for j, (fname, _) in enumerate(FIELD_NAMES):
            vals = c_target_vec[tgt_orig_idx, j, 0]
            print(f"     {fname:20s} range = [{vals.min():.4g}, {vals.max():.4g}]")

    print(f"\n  Elapsed time: {time.perf_counter() - start:.6f} s")
    print("")
    
    section = 'Gaussing'
    start = time.perf_counter()
    target_mesh =  gaussian_cell_smooth(target_mesh,'mapped_POROSITY',10)
    end = time.perf_counter()
    print(f"[{section}] Elapsed time: {end - start:.6f} seconds")
    
    section = 'Field transfer'
    print(f"[{section}]")
    start = time.perf_counter()
    _vectorize_fields_in(c_fieldnames, c_fieldnc, target_mesh, c_source_vec[c_s2t,:,:],  PIECE.ONCELL)
    end = time.perf_counter()
    print(f"[{section}] Elapsed time: {end - start:.6f} seconds")


    section = 'Writing'
    start = time.perf_counter()
    writer = vtk.vtkXMLUnstructuredGridWriter()
    # writer.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/4_GNL_refined_mapped.vtu')
    writer.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/mesh_mapped.vtu')
    writer.SetInputData(target_mesh)

    # writer.SetCompressorTypeToZLib()
    # writer.SetCompressionLevel(9)

    writer.Update()
    writer.Write()
    end = time.perf_counter()
    print(f"[{section}] Elapsed time: {end - start:.6f} seconds")

    # later tri-linear interp on simplexes
    #neigh = vtk.vtkIdList()
    #kd.FindClosestNPoints(3,(2,0,0),neigh)
    #neigh.GetId(0)


if __name__ == "__main__":
    main()
