# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt
import logging
from typing_extensions import Self, Union, Any
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkKdTree, vtkBoundingBox, vtkSelectionNode, vtkSelection
from vtkmodules.vtkFiltersExtraction import vtkExtractSelection
from vtkmodules.vtkFiltersCore import vtkCellCenters
from vtkmodules.vtkCommonCore import reference, vtkIdTypeArray
from geos.mesh.utils.arrayHelpers import ( getAttributeSet)
from geos.utils.Logger import ( getLogger, Logger, CountVerbosityHandler, getLoggerHandlerType )
from geos.utils.pieceEnum import Piece


__doc__ = """
MeshToMeshInterpolator is a vtk filter that map data from a source mesh to a target mesh using by default nearest
neighbor interpolation rules.

It leverage KdPointTree structure to do so efficiently and numpy array storate for fast indexing.

To use the filter:

.. code-block:: python



"""

loggerTitle: str = "Mesh to mesh Mapping"


class MeshToMeshInterpolator:

    def __init__(
        self: Self,
        meshFrom: Union[ vtkDataSet,  ],
        meshTo: Union[ vtkDataSet,  ],
        attributeNames: set[ str ],
        speHandler: bool = False,
    ):
        # making sure that meshFrom is subset or whole of meshTo
        if not MeshToMeshInterpolator._is_subset(meshFrom, meshTo):
            raise NotImplementedError(f"meshFrom should be a subset or whole meshTo")

        self.meshFrom: Union[ vtkDataSet, ] = MeshToMeshInterpolator._filter_volume_cells(meshFrom)
        self.meshTo: Union[ vtkDataSet, ] = MeshToMeshInterpolator._filter_volume_cells(meshTo)
        
        if self.meshFrom.GetNumberOfCells() == 0:
            raise NotImplementedError("MeshFrom : Not implemented for pure surface mesh")
        if self.meshTo.GetNumberOfCells() == 0:
            raise NotImplementedError("MeshTo : Not implemented for pure surface mesh")

        self.attributes: dict[Piece, set[str] ] = {}
        self.isApplied : bool = False
        self.fill_in_value : float = 0.0
        
        # sorting attribute to map by support
        for piece in [Piece.POINTS,Piece.CELLS]:
            self.attributes[piece] = attributeNames.intersection(getAttributeSet(self.meshFrom,piece))

        # Logger
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

        counter: CountVerbosityHandler = CountVerbosityHandler()
        self.counter: CountVerbosityHandler
        self.nbWarnings: int = 0
        try:
            self.counter = getLoggerHandlerType( type( counter ), self.logger )
            self.counter.resetWarningCount()
        except ValueError:
            self.counter = counter
            self.counter.setLevel( logging.INFO )

        self.logger.addHandler( self.counter )

    def setFillInValue(self: Self, val : float = 0.):
        self.fill_in_value = val

    @staticmethod
    def _is_subset(meshSource: Union[vtkDataSet,],
                   meshTarget: Union[vtkDataSet,]):
        
        boundSource = np.asarray( meshSource.GetBounds() )
        boundTarget = np.asarray( meshTarget.GetBounds() )

        #find the lowest point and translate up
        minPoint = np.min(np.vstack([boundTarget[[0,0,2,2,4,4]],boundSource[[0,0,2,2,4,4]]]),axis=0)
        boundSource -= minPoint
        boundTarget -= minPoint

        return vtkBoundingBox(tuple(boundTarget)).Contains(vtkBoundingBox(tuple(boundSource)))

    @staticmethod
    def _clamp_interpolate(meshSource: Union[ vtkDataSet, ],
                           meshTarget: Union[ vtkDataSet, ],
                           _get_points : Any,
                           ):

        #because of distributed vtm format we use distributed datastruct (e.g. list are list of list then reduced)
        kd = vtkKdTree()
        kd.BuildLocatorFromPoints( _get_points(meshSource))

        tgPts = _get_points( meshTarget)
        source2target = [[] for i in range(tgPts.GetNumberOfPoints())] # map index from source to target
        box = vtkBoundingBox(meshSource.GetBounds())#.Inflate()
        for i in range(tgPts.GetNumberOfPoints()):
            if box.ContainsPoint(tgPts.GetPoint(i)):
                dist = reference(0.)
                id_source = kd.FindClosestPoint(tgPts.GetPoint(i),dist)
                source2target[i].append( (dist,id_source) )
            else:
                source2target[i].append( (np.inf,-1) )
        
        return source2target

#  for vtm to vtm
# def _within_block(i, box_target):

#     for iblock, block in mesh_source:
#         block2block[itarget].append( iblock if vtkBoundingBox( block.bounds() ).IntersectBox( box_target ) )

    @staticmethod
    def _reduce(listOfList):
        return [ min(llist)[1] for llist in listOfList ]


    @staticmethod
    def _get_cellCenters(mesh):
        centers = vtkCellCenters()
        centers.SetInputData(mesh)
        centers.Update()

        return centers.GetOutput().GetPoints()

    def _vectorize_fields_out(self, fieldnames, mesh, piece):
        
        #use numpy for some speedup
        #assuming any vector fields will not have more than 9 components
        fieldnc = []
        if piece == Piece.POINTS: 
            fp = np.zeros(shape=(mesh.GetNumberOfPoints() + 1, len(fieldnames),9), dtype=float)
        elif piece == Piece.CELLS:
            fp = np.zeros(shape=(mesh.GetNumberOfCells() + 1, len(fieldnames),9), dtype=float)

        for j,field in enumerate(fieldnames):
            if piece == Piece.POINTS:
                if not mesh.GetPointData().HasArray(field):
                    self.logger.warning(f"{field} is not an array of  point data's source mesh")
                else:
                    data = mesh.GetPointData().GetArray(field)
                    fieldnc.append(data.GetNumberOfComponents())
            elif piece == Piece.CELLS:
                if not mesh.GetCellData().HasArray(field):
                    self.logger.warning(f"{field} is not an array of cell data's source mesh")
                else:
                    data = mesh.GetCellData().GetArray(field)
                    fieldnc.append(data.GetNumberOfComponents())

            fp[:-1,j,:fieldnc[-1]] = vtk_to_numpy(data).reshape(-1,fieldnc[-1])
        
        fp[-1,:,:] = self.fill_in_value

        return fp, fieldnc 

    @staticmethod
    def _vectorize_fields_in(fieldnames, fieldnc,  mesh, fp,  piece):
        #use numpy for some speedup

        for j,field in enumerate(fieldnames):
            arr = numpy_to_vtk(fp[:,j,:fieldnc[j]])
            arr.SetName(f'mapped_{field}')
            if piece == Piece.POINTS:
                mesh.GetPointData().AddArray(arr)
            elif piece == Piece.CELLS:
                mesh.GetCellData().AddArray(arr)

        return fp

    @staticmethod
    def _filter_volume_cells( mesh: vtkDataSet) -> Any:
        """Keep only 3D volume cells; optionally save 2D cells to VTU."""

        volume_ids  = vtkIdTypeArray()
        surface_ids = vtkIdTypeArray()
        n_volume = n_surface = n_other = 0

        for i in range(mesh.GetNumberOfCells()):
            dim = mesh.GetCell(i).GetCellDimension()
            if   dim == 3: 
                volume_ids.InsertNextValue(i)
                n_volume  += 1
            elif dim == 2: 
                surface_ids.InsertNextValue(i)
                n_surface += 1
            else:                                          
                n_other   += 1

        getLogger(loggerTitle, True).info(f"  Cell types: {n_volume} volume (3D) | "
              f"{n_surface} surface (2D) | {n_other} other")

        if n_surface == 0 and n_other == 0:
            print("No filtering needed (all cells are 3D)")
            return mesh

        sn = vtkSelectionNode()
        sn.SetFieldType(vtkSelectionNode.CELL)
        sn.SetContentType(vtkSelectionNode.INDICES)
        sn.SetSelectionList(volume_ids)
        sel = vtkSelection(); sel.AddNode(sn)
        ext = vtkExtractSelection()
        ext.SetInputData(0, mesh); ext.SetInputData(1, sel); ext.Update()
        getLogger(loggerTitle,True).info(f"Filtered → {n_volume} cells "
              f"(removed {n_surface + n_other})")
        
        if n_volume > 0:
            return ext.GetOutput()
        
        return mesh.NewInstance()

    # def _extract_region(self, mesh, attr_name, region_ids):
    #     """
    #     Return a sub-mesh containing only cells whose integer attribute
    #     value is in *region_ids*, together with the original cell indices.

    #     Parameters
    #     ----------
    #     mesh       : vtkUnstructuredGrid
    #     attr_name  : str    name of the integer cell-data attribute
    #     region_ids : list[int]

    #     Returns
    #     -------
    #     sub_mesh      : vtkUnstructuredGrid  (shallow copy)
    #     orig_indices  : numpy (N_sub,) int   original cell indices in *mesh*
    #     """
    #     if not mesh.GetCellData().HasArray(attr_name):
    #         available = [mesh.GetCellData().GetArrayName(i)
    #                      for i in range(mesh.GetCellData().GetNumberOfArrays())]
    #         raise KeyError(
    #             f"Attribute '{attr_name}' not found.\n"
    #             f"  Available arrays: {available}")

    #     attr   = vtk_to_numpy(mesh.GetCellData().GetArray(attr_name)).astype(np.int64)
    #     mask   = np.zeros(len(attr), dtype=bool)
    #     for rid in region_ids:
    #         mask |= (attr == rid)

    #     orig_indices = np.where(mask)[0]

    #     if len(orig_indices) == 0:
    #         return None, orig_indices

    #     # Build vtkIdTypeArray of selected indices
    #     id_arr = vtk.vtkIdTypeArray()
    #     for idx in orig_indices:
    #         id_arr.InsertNextValue(int(idx))

    #     sn = vtk.vtkSelectionNode()
    #     sn.SetFieldType(vtk.vtkSelectionNode.CELL)
    #     sn.SetContentType(vtk.vtkSelectionNode.INDICES)
    #     sn.SetSelectionList(id_arr)
    #     sel = vtk.vtkSelection(); sel.AddNode(sn)

    #     ext = vtk.vtkExtractSelection()
    #     ext.SetInputData(0, mesh); ext.SetInputData(1, sel); ext.Update()

    #     sub = vtk.vtkUnstructuredGrid()
    #     sub.ShallowCopy(ext.GetOutput())

    #     return sub, orig_indices



    def applyFilter(self : Self)->None:

        # reader = vtk.vtkXMLUnstructuredGridReader()
        # reader.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/4_GNL_Biot.vtu')
        # reader.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/GNL_update_biot.vtu') #name of the source mesh
        # reader.Update()
        # source_mesh = reader.GetOutput()

        # reader = vtk.vtkXMLUnstructuredGridReader()
        # reader.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/4_GNL_refined_target.vtu')
        # reader.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/GNL_hexdom7.vtu') # name of the target mesh
        # reader.Update()
        # target_mesh = reader.GetOutput()

        section : str = 'mapping'
        # start = time.perf_counter()
        s2t = {}
        s2t[Piece.POINTS]  = [ i if i!=-1 else self.meshFrom.GetNumberOfPoints() for i in  MeshToMeshInterpolator._reduce( 
            MeshToMeshInterpolator._clamp_interpolate( self.meshFrom, self.meshTo, lambda m : m.GetPoints() ) )  ]
        s2t[Piece.CELLS] = [i if i!=-1 else self.meshFrom.GetNumberOfCells() for i in MeshToMeshInterpolator._reduce( 
            MeshToMeshInterpolator._clamp_interpolate( self.meshFrom, self.meshTo, lambda m : MeshToMeshInterpolator._get_cellCenters(m))) ]
        # end = time.perf_counter()
        # print(f"[{section}] Elapsed time: {end - start:.6f} seconds")

        self.logger.debug(f"Checking for few index c2c and p2p mappings\n {s2t[Piece.POINTS]} \n {s2t[Piece.CELLS]}")

        section = 'Vectorizing'
        source_vec = {}
        fieldnc = {}
        # start = time.perf_counter()
        # c_fieldnames = [('Porosity','mapped_POROSITY'), ('PERM','mapped_PERM')] # for GNL test
        # pt_fieldnames = [('','')]
        if len(self.attributes[Piece.CELLS]) > 0:
            source_vec[Piece.CELLS], fieldnc[Piece.CELLS] = self._vectorize_fields_out(self.attributes[Piece.CELLS], self.meshFrom, Piece.CELLS)
        
        if len(self.attributes[Piece.POINTS]) > 0:
            source_vec[Piece.POINTS], fieldnc[Piece.POINTS] = self._vectorize_fields_out(self.attributes[Piece.POINTS], self.meshFrom, Piece.POINTS)

        # # ----------------------------------------------------------------
        # # REGION-BASED MAPPING
        # # ----------------------------------------------------------------
        # section = 'Mapping (KD-tree, per region)'
        # print(f"[{section}]")
        # start = time.perf_counter()

        # # Prepare output array (same shape as target, initialised to previous fields)
        # N_tgt         = target_mesh.GetNumberOfCells()
        # # c_target_vec  = np.zeros((N_tgt, len(FIELD_NAMES), 9), dtype=float)
        # c_target_vec, _ = _vectorize_fields_out(FIELD_NAMES, target_mesh, PIECE.ONCELL)

        # for src_ids, tgt_id in REGION_MAP:

        #     print(f"\n  ── Region: source {src_ids} → target [{tgt_id}] ──")

        #     # Extract source sub-mesh for this region
        #     src_sub, src_orig_idx = _extract_region(source_mesh, ATTRIBUTE_NAME,
        #                                             src_ids)
        #     if src_sub is None:
        #         print(f"No source cells found for ids {src_ids} — skipping.")
        #         continue
        #     print(f"     Source cells : {len(src_orig_idx)}")

        #     # Extract target sub-mesh for this region
        #     tgt_sub, tgt_orig_idx = _extract_region(target_mesh, ATTRIBUTE_NAME,
        #                                             [tgt_id])
        #     if tgt_sub is None:
        #         print(f"No target cells found for id {tgt_id} — skipping.")
        #         continue
        #     print(f"     Target cells : {len(tgt_orig_idx)}")

        #     # KD-tree mapping on sub-meshes (original clamp_interpolate logic)
        #     raw = clamp_interpolate(src_sub, tgt_sub,
        #                             lambda m: _get_cellCenters(m))
        #     # local_s2t: index within src_sub → map back to src_orig_idx
        #     local_s2t = reduce(raw)

        #     # local_s2t[i] is an index within src_sub  (0..N_src_sub-1)
        #     # src_orig_idx[local_s2t[i]] is the original index in source_mesh
        #     global_s2t = src_orig_idx[np.array(local_s2t, dtype=np.int64)]

        #     # Transfer: for each target sub-cell i, copy from global source index
        #     c_target_vec[tgt_orig_idx] = c_source_vec[global_s2t]

        #     # Quick value check
        #     for j, (fname, _) in enumerate(FIELD_NAMES):
        #         vals = c_target_vec[tgt_orig_idx, j, 0]
        #         print(f"     {fname:20s} range = [{vals.min():.4g}, {vals.max():.4g}]")

        # print(f"\n  Elapsed time: {time.perf_counter() - start:.6f} s")
    
        
        section = 'Field transfer'
        # print(f"[{section}]")
        # start = time.perf_counter()
        if len(self.attributes[Piece.CELLS]) > 0:
            MeshToMeshInterpolator._vectorize_fields_in(self.attributes[Piece.CELLS], fieldnc[Piece.CELLS], self.meshTo, source_vec[Piece.CELLS][s2t[Piece.CELLS],:,:],  Piece.CELLS)
        if len(self.attributes[Piece.POINTS]) > 0:
            MeshToMeshInterpolator._vectorize_fields_in(self.attributes[Piece.POINTS], fieldnc[Piece.POINTS], self.meshTo, source_vec[Piece.POINTS][s2t[Piece.POINTS],:,:],  Piece.POINTS)
        self.is_applied = True

        return
    

    def getOutput(self: Self) -> vtkDataSet:
        if self.is_applied:
            return self.meshTo
        
        # return empty is VTK behaviour on non-updated filter
        return self.meshTo.NewInstance()


        # end = time.perf_counter()
        # print(f"[{section}] Elapsed time: {end - start:.6f} seconds")


        # section = 'Writing'
        # start = time.perf_counter()
        # writer = vtk.vtkXMLUnstructuredGridWriter()
        # writer.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/4_GNL_refined_mapped.vtu')
        # writer.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/mesh_Jian/pain/mesh_mapped.vtu')
        # writer.SetInputData(target_mesh)

        # writer.SetCompressorTypeToZLib()
        # writer.SetCompressionLevel(9)

        # writer.Update()
        # writer.Write()
        # end = time.perf_counter()
        # print(f"[{section}] Elapsed time: {end - start:.6f} seconds")

        # later tri-linear interp on simplexes
        #neigh = vtk.vtkIdList()
        #kd.FindClosestNPoints(3,(2,0,0),neigh)
        #neigh.GetId(0)


    # if __name__ == "__main__":
        # main()
