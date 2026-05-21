# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Your Name
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, List, Tuple
import numpy as np
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk
import vtk

from geos.mesh.io.vtkIO import writeMesh, VtkOutput, readUnstructuredGrid
from geos.mesh_doctor.parsing.cliParsing import setupLogger


class IPType(StrEnum):
    TPFA = "TPFA"
    QTPFA = "QTPFA"
    BdLVM = "BdLVM"


@dataclass(frozen=True)
class Face:
    indexes: List[int]
    center: List[float]
    normal: List[float]
    area: float


VTK_TETRA_FACES = [
    [0, 1, 3],
    [1, 2, 3],
    [0, 3, 2],
    [0, 2, 1],
]

VTK_VOXEL_FACES = [
    [0, 2, 6, 4],
    [1, 3, 7, 5],
    [0, 1, 5, 4],
    [2, 3, 7, 6],
    [0, 1, 3, 2],
    [4, 5, 7, 6],
]

VTK_HEXAHEDRON_FACES = [
    [0, 3, 2, 1],
    [4, 5, 6, 7],
    [0, 1, 5, 4],
    [2, 3, 7, 6],
    [0, 4, 7, 3],
    [1, 2, 6, 5],
]

VTK_WEDGE_FACES = [
    [0, 1, 2],
    [3, 5, 4],
    [0, 3, 4, 1],
    [1, 4, 5, 2],
    [0, 2, 5, 3],
]

VTK_PYRAMID_FACES = [
    [0, 3, 2, 1],
    [0, 1, 4],
    [1, 2, 4],
    [2, 3, 4],
    [3, 0, 4],
]

_FACE_TABLE: Dict[int, List[List[int]]] = {
    vtk.VTK_TETRA: VTK_TETRA_FACES,
    vtk.VTK_VOXEL: VTK_VOXEL_FACES,
    vtk.VTK_HEXAHEDRON: VTK_HEXAHEDRON_FACES,
    vtk.VTK_WEDGE: VTK_WEDGE_FACES,
    vtk.VTK_PYRAMID: VTK_PYRAMID_FACES,
}


def get_cell_faces(cell: vtk.vtkCell) -> List[List[int]]:
    cell_type = cell.GetCellType()
    if cell_type not in _FACE_TABLE:
        unknown_name = vtk.vtkCellTypes.GetClassNameFromTypeId(cell_type) or str(cell_type)
        raise ValueError(f"Unsupported cell type '{unknown_name}' (id={cell_type}).")
    local_to_global = [cell.GetPointId(i) for i in range(cell.GetNumberOfPoints())]
    return [[local_to_global[local_idx] for local_idx in face] for face in _FACE_TABLE[cell_type]]


def _filterVolumeCells(mesh: vtk.vtkDataSet) -> vtk.vtkDataSet:
    volumeIds = vtk.vtkIdTypeArray()
    for i in range(mesh.GetNumberOfCells()):
        dim = mesh.GetCell(i).GetCellDimension()
        if dim == 3:
            volumeIds.InsertNextValue(i)

    sn = vtk.vtkSelectionNode()
    sn.SetFieldType(vtk.vtkSelectionNode.CELL)
    sn.SetContentType(vtk.vtkSelectionNode.INDICES)
    sn.SetSelectionList(volumeIds)

    sel = vtk.vtkSelection()
    sel.AddNode(sn)

    ext = vtk.vtkExtractSelection()
    ext.SetInputData(0, mesh)
    ext.SetInputData(1, sel)
    ext.Update()
    return ext.GetOutput()


def attach_matrix_as_multicomponent(mesh: vtk.vtkDataSet, matrices: List[np.ndarray], field_name: str = "MatrixField", on_points: bool = False) -> vtk.vtkDataSet:
    NF = matrices[0].shape[0]
    flat = np.array([m.flatten() for m in matrices], dtype=np.float64)
    vtk_arr = numpy_to_vtk(flat, deep=True, array_type=vtk.VTK_DOUBLE)
    vtk_arr.SetName(field_name)
    vtk_arr.SetNumberOfComponents(NF * NF)
    for i in range(1, NF + 1):
        for j in range(1, NF + 1):
            comp_idx = (i - 1) * NF + (j - 1)
            vtk_arr.SetComponentName(comp_idx, f"{i}/{j}")
    data_store = mesh.GetPointData() if on_points else mesh.GetCellData()
    data_store.AddArray(vtk_arr)
    return mesh


def attach_results(mesh: vtk.vtkDataSet, matrices: List[Tuple[float, float, float, float]], field_name: str = "MatrixField") -> vtk.vtkDataSet:
    flat = np.array([np.asarray(m, dtype=np.float64) for m in matrices])
    vtk_arr = numpy_to_vtk(flat, deep=True, array_type=vtk.VTK_DOUBLE)
    vtk_arr.SetName(field_name)
    vtk_arr.SetNumberOfComponents(4)
    vtk_arr.SetComponentName(0, "condM")
    vtk_arr.SetComponentName(1, "condMr")
    vtk_arr.SetComponentName(2, "lambda_m")
    vtk_arr.SetComponentName(3, "lambda_M")
    mesh.GetCellData().AddArray(vtk_arr)
    return mesh


class ComputeMFD:
    def __init__(self, mesh):
        self.faces, self.face2cell = ComputeMFD.compute_newell(mesh)
        self.cell_centers = ComputeMFD.compute_cell_centroids(mesh)

    def set_IP(self, ip_type: IPType):
        self.ip_type = ip_type

    def compute(self, mesh):
        if self.ip_type == IPType.TPFA:
            return self.compute_tpfa(mesh)
        elif self.ip_type == IPType.QTPFA:
            return self.compute_quasitpfa(mesh)
        elif self.ip_type == IPType.BdLVM:
            return self.compute_bdlvm(mesh)
        else:
            raise ValueError(f"Unsupported IP type: {self.ip_type}")

    def compute_tpfa(self, mesh) -> list[np.ndarray]:
        perm = vtk_to_numpy(mesh.GetCellData().GetArray("Permeability"))
        cell2face = {}
        [cell2face.setdefault(cell, []).append(k) for k, v in self.face2cell.items() for cell in v]
        ncells = len(self.cell_centers)
        M = [None] * ncells
        face_centers = np.array([self.faces[k].center for k in self.face2cell])
        face_normals = np.array([self.faces[k].normal for k in self.face2cell])
        face_area = np.array([self.faces[k].area for k in self.face2cell])

        def process_cell(cell):
            face_indices = cell2face.get(cell)
            nfacesPerCell = len(face_indices)
            Mloc = np.zeros((nfacesPerCell, nfacesPerCell))
            face_cell_vec = np.ndarray((ncells, nfacesPerCell, 3))
            face_cell_dist = np.ndarray((ncells, nfacesPerCell))
            face_cell_vec[cell, :, :] = face_centers[face_indices, :] - self.cell_centers[cell, :]
            face_cell_dist[cell, :] = np.linalg.norm(face_cell_vec[cell, :, :], axis=1)
            face_cell_vec[cell, :, :] /= face_cell_dist[cell, :].reshape(nfacesPerCell, 1)

            face_normals[face_indices, :] = ComputeMFD.reorient_normal(face_normals[face_indices, :], face_cell_vec[cell, :, :])
            T = np.einsum('ni,ni,ni->n', face_cell_vec[cell, :, :], np.tile(perm[cell, :], (nfacesPerCell, 1)), face_normals[face_indices, :])
            T *= face_area[face_indices] / face_cell_dist[cell, :]
            Mloc[range(nfacesPerCell), range(nfacesPerCell)] = 1 / T
            return cell, Mloc

        from concurrent.futures import ThreadPoolExecutor, as_completed
        total = len(cell2face)
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_cell, i) for i in range(total)]
            results = [future.result() for future in as_completed(futures)]

        for cell, Mloc in results:
            M[cell] = Mloc
        return M

    def compute_quasitpfa(self, mesh):
        perm = vtk_to_numpy(mesh.GetCellData().GetArray("Permeability"))
        invperm = 1.0 / perm
        vol = vtk_to_numpy(mesh.GetCellData().GetArray("Volume"))
        faces, self.face2cell = ComputeMFD.compute_newell(mesh)
        cell2face = {}
        [cell2face.setdefault(cell, []).append(k) for k, v in self.face2cell.items() for cell in v]
        cell_centers = ComputeMFD.compute_cell_centroids(mesh)
        ncells = len(cell_centers)
        M = [None] * ncells
        face_centers = np.array([faces[k].center for k in self.face2cell])
        face_normals = np.array([faces[k].normal for k in self.face2cell])
        face_area = np.array([faces[k].area for k in self.face2cell])

        def process_cell(cell):
            face_indices = cell2face.get(cell)
            nf = len(face_indices)
            fc_vec = face_centers[face_indices] - cell_centers[cell]
            c = fc_vec
            loc_normals = ComputeMFD.reorient_normal(face_normals[face_indices], c)
            n = loc_normals * face_area[face_indices, None]
            K = np.tile(perm[cell], (nf, 1))
            Kinv = np.tile(invperm[cell], (nf, 1))
            Mloc = np.einsum('ni,ni,mi->nm', c, Kinv, c) / vol[cell]
            w = np.einsum('ni,ni,ni->n', n, K, n)
            Q, _ = np.linalg.qr(n, mode='reduced')
            proj = np.eye(nf) - np.einsum('ni,mi->nm', Q, Q)
            S = np.einsum('ij,j,jk->ik', proj, w, proj)
            S = (vol[cell] / 2.0) * S
            indicators = ComputeMFD._get_indicators(proj, Mloc, S)
            return (cell, *indicators)

        from concurrent.futures import ThreadPoolExecutor, as_completed
        total = len(cell2face)
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_cell, i) for i in range(total)]
            results = [future.result() for future in as_completed(futures)]

        for cell, c, cr, lm, lM in results:
            M[cell] = (c, cr, lm, lM)
        return M

    def compute_bdlvm(self, mesh):
        perm = vtk_to_numpy(mesh.GetCellData().GetArray("Permeability"))
        cell2face = {}
        [cell2face.setdefault(cell, []).append(k) for k, v in self.face2cell.items() for cell in v]
        ncells = len(self.cell_centers)
        M = [None] * ncells
        face_centers = np.array([self.faces[k].center for k in self.face2cell])
        face_normals = np.array([self.faces[k].normal for k in self.face2cell])
        face_area = np.array([self.faces[k].area for k in self.face2cell])

        def process_cell(cell):
            face_indices = cell2face.get(cell)
            nf = len(face_indices)
            gamma = 1.0 / nf
            fc_vec = face_centers[face_indices] - self.cell_centers[cell]
            area = face_area[face_indices]
            c = np.einsum('ni,n->ni', fc_vec, area)
            n = face_normals[face_indices]
            K = np.tile(perm[cell], (nf, 1))
            n = np.einsum('ni,ni->ni', n, K)
            CtN_inv = np.linalg.pinv(c.T @ n)
            M0 = np.einsum('ni,ij,mj->nm', c, CtN_inv, c)
            NtN_inv = np.linalg.pinv(n.T @ n)
            proj = np.eye(nf) - np.einsum('ni,ij,mj->nm', n, NtN_inv, n)
            Mloc = M0
            S = gamma * proj
            Mloc = np.einsum('ij,i,j->ij', Mloc, 1.0 / area, 1.0 / area)
            S = np.einsum('ij,i,j->ij', S, 1.0 / area, 1.0 / area)
            indicators = ComputeMFD._get_indicators(proj, Mloc, S)
            return (cell, *indicators)

        from concurrent.futures import ThreadPoolExecutor, as_completed
        total = len(cell2face)
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_cell, i) for i in range(total)]
            results = [future.result() for future in as_completed(futures)]

        for cell, c, cr, lm, lM in results:
            M[cell] = (c, cr, lm, lM)
        return M

    @staticmethod
    def _get_indicators(K, M, S, compute_eigs=True):
        Sr = K.T @ S @ K
        Mr = K.T @ M @ K
        if compute_eigs:
            try:
                lambdas = np.linalg.eigvals(np.linalg.solve(Mr, Sr))
            except Exception:
                lambdas = np.linalg.eigvals(np.linalg.pinv(Mr) @ Sr)
        else:
            lambdas = []
        return np.linalg.cond(M + S), np.linalg.cond(Mr + Sr), np.min(lambdas.real), np.max(lambdas.real)

    @staticmethod
    def centroid_3d_polygon(mesh, point_indices: List[int], area_tolerance: float = 0.0):
        n = len(point_indices)
        if n < 2:
            raise ValueError(f"Polygon must have at least 2 points, got {n}.")
        points = vtk_to_numpy(mesh.GetPoints().GetData())
        origin = points[point_indices[0]].copy()
        normal = np.zeros(3)
        center = np.zeros(3)
        for a in range(n):
            current = points[point_indices[a]] - origin
            next_pt = points[point_indices[(a + 1) % n]] - origin
            cross = np.cross(current, next_pt)
            normal += cross
            center += next_pt
        area = np.linalg.norm(normal)
        center = center / n + origin
        if area > area_tolerance:
            normal /= area
            area *= 0.5
        elif area < -area_tolerance:
            raise ValueError("Negative area found")
        else:
            return center, normal, 0.0
        return center, normal, area

    @staticmethod
    def compute_newell(mesh):
        faces = {}
        face2cell = {}

        def process_cell(cellid):
            local_faces = []
            local_map = []
            list_indexes = get_cell_faces(mesh.GetCell(cellid))
            for indexes in list_indexes:
                center, normal, area = ComputeMFD.centroid_3d_polygon(mesh, indexes)
                key = tuple(sorted(indexes))
                local_faces.append((key, indexes, center, normal, area))
                local_map.append((key, cellid))
            return local_faces, local_map

        next_index = 0
        from concurrent.futures import ThreadPoolExecutor, as_completed
        total = mesh.GetNumberOfCells()
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(process_cell, i) for i in range(total)]
            results = [future.result() for future in as_completed(futures)]

        face_lookup = {}
        for local_faces, local_map in results:
            for key, indexes, center, normal, area in local_faces:
                if key not in face_lookup:
                    face_lookup[key] = next_index
                    faces[next_index] = Face(indexes=indexes, center=center, normal=normal, area=area)
                    next_index += 1
            for key, cellid in local_map:
                face_index = face_lookup[key]
                face2cell.setdefault(face_index, []).append(cellid)

        return faces, face2cell

    @staticmethod
    def reorient_normal(normals, cell2vec):
        flag = np.einsum('ni,ni->n', normals, cell2vec) < 0
        normals[flag] = -normals[flag]
        return normals

    @staticmethod
    def compute_cell_centroids(mesh) -> np.ndarray:
        vtkCellCenters = vtk.vtkCellCenters()
        vtkCellCenters.SetInputData(mesh)
        vtkCellCenters.Update()
        return vtk_to_numpy(vtkCellCenters.GetOutput().GetPoints().GetData())


def create_hex_grid(nx=2, ny=2, nz=2) -> vtk.vtkUnstructuredGrid:
    mesh = vtk.vtkUnstructuredGrid()
    points = vtk.vtkPoints()
    for k in range(nz + 1):
        for j in range(ny + 1):
            for i in range(nx + 1):
                points.InsertNextPoint(i / nx, j / ny, k / nz)
    mesh.SetPoints(points)

    def pid(i, j, k):
        return k * (ny + 1) * (nx + 1) + j * (nx + 1) + i

    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                ids = vtk.vtkIdList()
                for node in [
                    pid(i, j, k),
                    pid(i + 1, j, k),
                    pid(i + 1, j + 1, k),
                    pid(i, j + 1, k),
                    pid(i, j, k + 1),
                    pid(i + 1, j, k + 1),
                    pid(i + 1, j + 1, k + 1),
                    pid(i, j + 1, k + 1),
                ]:
                    ids.InsertNextId(node)
                mesh.InsertNextCell(vtk.VTK_HEXAHEDRON, ids)
    return add_permeability(mesh)


def add_permeability(mesh):
    perm = np.ones((mesh.GetNumberOfCells(), 3))
    vtk_perm = numpy_to_vtk(perm, array_type=vtk.VTK_UNSIGNED_INT)
    vtk_perm.SetName("Permeability")
    mesh.GetCellData().AddArray(vtk_perm)
    return mesh


def add_cell_volumes(mesh: vtk.vtkUnstructuredGrid) -> vtk.vtkUnstructuredGrid:
    quality = vtk.vtkMeshQuality()
    quality.SetInputData(mesh)
    quality.SetHexQualityMeasureToVolume()
    quality.SetTetQualityMeasureToVolume()
    quality.SetWedgeQualityMeasureToVolume()
    quality.SetPyramidQualityMeasureToVolume()
    quality.Update()
    quality_array = vtk_to_numpy(quality.GetOutput().GetCellData().GetArray("Quality"))
    volume_array = numpy_to_vtk(quality_array, deep=True)
    volume_array.SetName("Volume")
    mesh.GetCellData().AddArray(volume_array)
    return mesh


@dataclass(frozen=True)
class Options:
    vtkOutput: VtkOutput
    ip: str


@dataclass(frozen=True)
class Result:
    info: str


def meshAction(mesh, options: Options) -> Result:
    mfd = ComputeMFD(mesh)
    try:
        mfd.set_IP(IPType[options.ip])
    except Exception:
        raise ValueError(f"Unsupported IP type: {options.ip}")

    res = mfd.compute(mesh)
    try:
        mesh = attach_results(mesh, res, f"{options.ip}_Results")
    except Exception:
        mesh = attach_matrix_as_multicomponent(mesh, res, f"{options.ip}_Results")

    writeMesh(mesh, options.vtkOutput, canOverwrite=True, logger=setupLogger)
    return Result(info=f"MFD {options.ip} computed and written to {options.vtkOutput.output}")


def action(vtuInputFile: str, options: Options) -> Result:
    mesh = readUnstructuredGrid(vtuInputFile)
    return meshAction(mesh, options)
