# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
from typing import Optional

import numpy as np
import numpy.typing as npt
import vtkmodules.util.numpy_support as vnp
from typing_extensions import Self
from vtk import VTK_INT  # type: ignore[import-untyped]
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkIdList,
    vtkInformation,
    vtkInformationVector,
    vtkPoints,
)
from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkUnstructuredGrid

from geos_posp.processing.ConnectionSet import (
    ConnectionSet,
    ConnectionSetCollection,
)
from geos_posp.processing.geometryFunctions import getCellSideAgainstPlane
from geos.utils.GeosOutputsConstants import PostProcessingOutputsEnum
from geos.utils.Logger import Logger, getLogger
from geos.utils.PhysicalConstants import (
    EPSILON,
)

__doc__ = """
VolumeSurfaceMeshMapper is a vtk filter that collects the cell of a volume mesh
adjacents to the faces of a surface mesh.

VolumeSurfaceMeshMapper inputs are a volume mesh of type vtkUnstructuredGrid
and a surface mesh of type vtkPolyData.

To use the filter:

.. code-block:: python

    from filters.VolumeSurfaceMeshMapper import VolumeSurfaceMeshMapper

    # filter inputs
    logger :Logger
    # input objects
    volumeMesh :vtkUnstructuredGrid
    surfaceMesh :vtkPolyData

    # instanciate the filter
    volumeSurfaceMeshMapper :VolumeSurfaceMeshMapper = VolumeSurfaceMeshMapper()
    # set parameters and logger
    volumeSurfaceMeshMapper.SetCreateAttribute(True)
    volumeSurfaceMeshMapper.SetAttributeName("Surface1_AdjacentCell")
    volumeSurfaceMeshMapper.SetLogger(logger)
    # set input objects
    volumeSurfaceMeshMapper.AddInputDataObject(0, volumeMesh)
    volumeSurfaceMeshMapper.AddInputDataObject(1, surfaceMesh)
    # do calculations
    volumeSurfaceMeshMapper.Update()
    # get filter output mesh (same as input volume mesh with new attribute if
    # volumeSurfaceMeshMapper.SetCreateAttribute(True))
    output :vtkUnstructuredGrid = volumeSurfaceMeshMapper.GetOutputDataObject(0)
    # get filter output mapping
    # surface faces to volume cell mapping
    surfaceToVolumeMap :dict[int, dict[int, bool]] = volumeSurfaceMeshMapper.GetSurfaceToVolumeMap()
    # volume cell to surface faces mapping
    volumeToSurfaceMap :dict[int, tuple[set[int], bool]] = volumeSurfaceMeshMapper.GetVolumeToSurfaceMap()
"""


class VolumeSurfaceMeshMapper(VTKPythonAlgorithmBase):
    def __init__(self: Self) -> None:
        """Vtk filter to compute cell adjacency between volume and surface meshes.

        Inputs are vtkUnstructuredGrid for volume mesh, vtkPolyData for
        surface mesh, and attribute name.

        Ouputs are the volume mesh (vtkUnstructuredGrid) with a new attribute if
        SetCreateAttribute was set to True, and a map of surface face indexess
        as keys and adjacent volume cell indexes as values.
        """
        super().__init__(nInputPorts=2, nOutputPorts=1, outputType="vtkPolyData")

        #: input volume mesh
        self.m_volumeMesh: vtkUnstructuredGrid
        #: input surface mesh
        self.m_surfaceMesh: vtkPolyData
        #: cell adjacency mapping that will be computed
        # self.m_cellIdMap :dict[int, dict[int, bool]] = {}
        self.m_connectionSets: ConnectionSetCollection = ConnectionSetCollection()
        #: if set to True, will create an attribute in the volume mesh
        self.m_createAttribute = False
        #: name of the attribute to create in the volume mesh
        self.m_attributeName: str = (
            PostProcessingOutputsEnum.ADJACENT_CELL_SIDE.attributeName
        )
        #: logger
        self.m_logger: Logger = getLogger("Volume to Surface Mapper Filter")

    def SetLogger(self: Self, logger: Logger) -> None:
        """Set the logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

    def GetAttributeName(self: Self) -> str:
        """Get the name of the attribute to create.

        Returns:
            str: name of the attribute.
        """
        return self.m_attributeName

    def SetAttributeName(self: Self, name: str) -> None:
        """Set the name of the attribute to create.

        Args:
            name (str): name of the attribute.
        """
        self.m_attributeName = name

    def GetCreateAttribute(self: Self) -> bool:
        """Get the value of the boolean to create the attribute.

        Returns:
            bool: create attribute boolean value.
        """
        return self.m_createAttribute

    def SetCreateAttribute(self: Self, value: bool) -> None:
        """Set the value of the boolean to create the attribute.

        Returns:
            bool: True to create the attribute, False otherwise.
        """
        self.m_createAttribute = value

    def GetSurfaceToVolumeConnectionSets(self: Self) -> ConnectionSetCollection:
        """Get the collection of surface to volume cell ids.

        Returns:
            ConnectionSetCollection: collection of ConnectionSet.
        """
        return self.m_connectionSets

    def GetVolumeToSurfaceConnectionSets(self: Self) -> ConnectionSetCollection:
        """Get the ConnectionSetCollection of volume to surface cell ids.

        Returns:
            ConnectionSetCollection: reversed collection of connection set.
        """
        return self.m_connectionSets.getReversedConnectionSetCollection()

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[vtkInformationVector],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData = self.GetInputData(inInfoVec, 0, 0)
        outData = self.GetOutputData(outInfoVec, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfoVec, outInfoVec)

    def FillInputPortInformation(self: Self, port: int, info: vtkInformation) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set(self.INPUT_REQUIRED_DATA_TYPE(), "vtkUnstructuredGrid")
        else:
            info.Set(self.INPUT_REQUIRED_DATA_TYPE(), "vtkPolyData")
        return 1

    def RequestInformation(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[vtkInformationVector],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()  # noqa: F841
        outInfo = outInfoVec.GetInformationObject(0)  # noqa: F841
        return 1

    def RequestData(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[vtkInformationVector],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        try:
            # input volume mesh
            self.m_volumeMesh = vtkUnstructuredGrid.GetData(inInfoVec[0])
            # input surface
            self.m_surfaceMesh = vtkPolyData.GetData(inInfoVec[1])
            # output volume mesh
            outData: vtkUnstructuredGrid = self.GetOutputData(outInfoVec, 0)
            outData.ShallowCopy(self.m_volumeMesh)

            # volume mesh properties
            ptsVol: vtkPoints = self.m_volumeMesh.GetPoints()
            assert ptsVol is not None, "Volume mesh points are undefined."
            ptsCoordsVol: npt.NDArray[np.float64] = vnp.vtk_to_numpy(ptsVol.GetData())

            # surface mesh properties
            nbFaces: int = self.m_surfaceMesh.GetNumberOfCells()
            ptsSurf: vtkPoints = self.m_surfaceMesh.GetPoints()
            assert ptsSurf is not None, "Surface mesh points are undefined."
            ptsCoordsSurf: npt.NDArray[np.float64] = vnp.vtk_to_numpy(ptsSurf.GetData())

            # get cell ids for each face id
            self.m_connectionSets.clear()
            for faceId in range(nbFaces):
                # self.m_cellIdMap[faceId] = self.getAdjacentCells(
                #     faceId, ptsCoordsSurf, ptsCoordsVol)
                cellIdsSide: dict[int, bool] = self.getAdjacentCells(
                    faceId, ptsCoordsSurf, ptsCoordsVol
                )
                self.m_connectionSets.add(ConnectionSet(faceId, cellIdsSide))

            if self.m_createAttribute:
                self.createAttribute(outData)
        except AssertionError as e:
            mess: str = "Surface to Volume mesh mapping failed due to:"
            self.m_logger.error(mess)
            self.m_logger.error(e, exc_info=True)
            return 0
        except Exception as e:
            mess0: str = "Surface to Volume mesh mapping failed due to:"
            self.m_logger.critical(mess0)
            self.m_logger.critical(e, exc_info=True)
            return 0
        return 1

    def getAdjacentCells(
        self: Self,
        faceId: int,
        ptsCoordsSurf: npt.NDArray[np.float64],
        ptsCoordsVol: npt.NDArray[np.float64],
    ) -> dict[int, bool]:
        """Get the cells from volume mesh adjacent to the face cellIdSurf.

        Args:
            faceId (int): id of the face of the surface mesh.
            ptsCoordsSurf (npt.NDArray[np.float64]): coordinates of the points
                of the surface mesh
            ptsCoordsVol (npt.NDArray[np.float64]): coordinates of the points
                of the volume mesh

        Returns:
            dict[int, bool]: map of cell ids adjacent to the face as keys, and
            side as values
        """
        # Retrieve point ids of the face of the surface
        facePtIds: vtkIdList = vtkIdList()
        self.m_surfaceMesh.GetCellPoints(faceId, facePtIds)

        # number of face vertices
        nbPtsFace: int = facePtIds.GetNumberOfIds()
        # coordinates of the vertices of the face
        ptsCoordsFace: list[npt.NDArray[np.float64]] = [
            ptsCoordsSurf[facePtIds.GetId(p)] for p in range(nbPtsFace)
        ]

        # get the ids of all the cells that are adjacent to the face
        cellIds: set[int] = self.getCellIds(ptsCoordsFace, ptsCoordsVol)

        # get the side of each cell
        cellIdsSide: dict[int, bool] = {}
        for cellId in cellIds:
            side: bool = self.getCellSide(cellId, faceId, ptsCoordsFace, ptsCoordsVol)
            cellIdsSide[cellId] = side

        return cellIdsSide

    def getCellIds(
        self: Self,
        ptsCoordsFace: list[npt.NDArray[np.float64]],
        ptsCoordsVol: npt.NDArray[np.float64],
    ) -> set[int]:
        """Get the ids of all the cells that are adjacent to input face.

        A cell is adjacent to a face if it contains all the vertices of the face.

        .. WARNING::
            Face adjacency determination relies on a geometrical test of vertex
            location, it is error prone because of computational precision.

        Args:
            ptsCoordsFace (npt.NDArray[np.float64]): List of vertex coordinates
                of the face. The shape of the array should be (N,1).
            ptsCoordsVol (npt.NDArray[np.float64]): Coodinates of the vertices
                of the volume mesh. The shape of the array should be (N,M), where M
                is the number of vertices in the volume mesh.

        Returns:
            set[int]: set of cell ids adjacent to the face.
        """
        cellIds: list[set[int]] = []
        # get the ids of the cells that contains each vertex of the face.
        for coords in ptsCoordsFace:
            assert coords.shape[0] == ptsCoordsVol.shape[1]
            diffCoords: npt.NDArray[np.float64] = np.abs(ptsCoordsVol - coords)
            idPtsVol: tuple[npt.NDArray[np.int64], ...] = np.where(
                np.all(diffCoords < EPSILON, axis=-1)
            )

            assert len(idPtsVol) == 1
            idPt = idPtsVol[0]

            # In case of collocated points from the volume mesh
            if len(idPt) > 1:
                self.m_logger.warning(
                    "The volume mesh has collocated points: "
                    + f"{idPt}. Clean the mesh first."
                )

            # Retrieve all the cells attached to the point of the volume mesh
            cellList: vtkIdList = vtkIdList()
            self.m_volumeMesh.GetPointCells(idPt[0], cellList)
            cellIdsVertex: set[int] = {
                cellList.GetId(c) for c in range(cellList.GetNumberOfIds())
            }
            cellIds += [cellIdsVertex]
        # keep the cells that contain all the vertices of the face
        return set.intersection(*cellIds)

    def getCellSide(
        self: Self,
        cellId: int,
        faceId: int,
        ptsCoordsFace: list[npt.NDArray[np.float64]],
        ptsCoordsVol: npt.NDArray[np.float64],
    ) -> bool:
        """Get the side of the cell from volume mesh against the surface.

        Args:
            cellId (int): cell id in the volume mesh.
            faceId (int): cell id in the surface mesh.
            ptsCoordsFace (list[npt.NDArray[np.float64]]): coordinates of the
                vertices of the face.
            ptsCoordsVol (npt.NDArray[np.float64]): coordinates of the vertices
                of the cell.

        Returns:
            bool: True if the cell is the same side as surface normal, False
            otherwise.
        """
        # Retrieve vertex coordinates of the cell of the volume mesh
        cellPtIds: vtkIdList = vtkIdList()
        self.m_volumeMesh.GetCellPoints(cellId, cellPtIds)
        cellPtsCoords: npt.NDArray[np.float64] = np.array(
            [
                ptsCoordsVol[cellPtIds.GetId(i)]
                for i in range(cellPtIds.GetNumberOfIds())
            ]
        )
        # get face normal vector # type: ignore[no-untyped-call]
        normals: npt.NDArray[np.float64] = vnp.vtk_to_numpy(
            self.m_surfaceMesh.GetCellData().GetNormals()
        )
        normalVec: npt.NDArray[np.float64] = normals[faceId]
        normalVec /= np.linalg.norm(normalVec)  # normalization
        # get cell side
        return getCellSideAgainstPlane(cellPtsCoords, ptsCoordsFace[0], normalVec)

    def createAttribute(self: Self, mesh: vtkUnstructuredGrid) -> bool:
        """Create the cell adjacency attribute.

        Attribute yields -1 is a cell is not adjacent to input surface, 0 if
        the cell is along negative side, 1 if the cell is along positive side.

        Args:
            mesh (vtkUnstructuredGrid): mesh where to add the attribute

        Returns:
            bool: True if the new attribute was successfully added,
            False otherwise
        """
        adjacentCellIdsMap: ConnectionSetCollection = (
            self.GetVolumeToSurfaceConnectionSets()
        )
        array: npt.NDArray[np.float64] = -1 * np.ones(mesh.GetNumberOfCells())
        for i in range(mesh.GetNumberOfCells()):
            connectionSet: Optional[ConnectionSet] = adjacentCellIdsMap.get(i)
            # cell i is not in the collection
            if connectionSet is None:
                continue
            # get connected cell sides
            values: tuple[bool, ...] = tuple(
                connectionSet.getConnectedCellIds().values()
            )
            # assume that all boolean values are the same, keep the first one
            # convert boolean to int
            array[i] = int(values[0])
        newAttr: vtkDataArray = vnp.numpy_to_vtk(array, deep=True, array_type=VTK_INT)
        newAttr.SetName(self.m_attributeName)
        mesh.GetCellData().AddArray(newAttr)
        mesh.GetCellData().Modified()
        mesh.Modified()
        return True
