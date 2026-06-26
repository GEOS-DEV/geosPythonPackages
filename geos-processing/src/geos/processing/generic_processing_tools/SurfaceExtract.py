from abc import ABC, abstractmethod
from typing import Union
import logging

import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtk import VTK_QUAD, VTK_TRIANGLE, VTK_POLYGON
from vtkmodules.vtkCommonCore import vtkIdTypeArray, vtkIdList 
from vtkmodules.vtkCommonDataModel import (
    vtkDataSet,
    vtkSelection,
    vtkSelectionNode,
    vtkUnstructuredGrid,
    vtkMultiBlockDataSet,
)
from vtkmodules.vtkFiltersExtraction import vtkExtractSelection
from geos.utils.Logger import ( getLogger, Logger, CountVerbosityHandler, isHandlerInLogger, getLoggerHandlerType )

loggerTitle: str = "SurfaceExtract"

class ExtractBase(ABC):

    def __init__(self: Self, speHandler: bool = False,) -> None:
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

    def setInputData(self: Self, mesh: vtkDataSet) -> None:
        self.mesh = mesh

    @abstractmethod
    def _getMask(self: Self) -> npt.NDArray:
        """Return a mask array to extract cells"""
        ...

    def _extractRegion(
        self: Self, meshFrom: Union[vtkDataSet,], mask: npt.NDArray
    ) -> vtkUnstructuredGrid:
        """Wrapping extract Selection on the mask.

        Args:
            meshFrom (Union[vtkDataSet,]): mesh to extract from
            mask (npt.NDArray): boolean array of cells to extract
        """
        # Build vtkIdTypeArray of selected indices
        idArr = vtkIdTypeArray()
        for idx in np.where(mask)[0]:
            idArr.InsertNextValue(int(idx))

        sn = vtkSelectionNode()
        sn.SetFieldType(vtkSelectionNode.CELL)
        sn.SetContentType(vtkSelectionNode.INDICES)
        sn.SetSelectionList(idArr)
        sel = vtkSelection()
        sel.AddNode(sn)

        ext = vtkExtractSelection()
        ext.SetInputData(0, meshFrom)
        ext.SetInputData(1, sel)
        ext.Update()

        sub = vtkUnstructuredGrid()
        sub.ShallowCopy(ext.GetOutput())

        return sub

    def Update(self) -> None:

        mask = self._getMask()
        try:
            self.mesh = self._extractRegion(self.mesh, mask)
        except Exception as e:
            self.logger.error(f"Error occurred while updating the filter: {e}")
            raise

        result: str = f"The filter { self.logger.name } succeeded"
        if self.counter.warningCount > 0:
            self.logger.warning( f"{ result } but { self.counter.warningCount } warnings have been logged." )
        else:
            self.logger.info( f"{ result }." )

        # Keep number of warnings logged during the filter application and reset the warnings count in case the filter is applied again.
        self.nbWarnings = self.counter.warningCount
        self.counter.resetWarningCount()

        return

    def SetLoggerHandler( self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not isHandlerInLogger( handler, self.logger ):
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has this handler, it has not been added." )

    def GetOutput(self) -> vtkDataSet:

        return self.mesh
    
    def applyFilter(self: Self, inputMesh: vtkDataSet, outputMesh: vtkDataSet) -> None:
        """Apply the filter to extract the nearest cells layer to a surface.

        Args:
            inputMesh (vtkDataSet): The input mesh to process.
            outputMesh (vtkDataSet): The output mesh after processing.
        """
        self.setInputData(inputMesh)
        self.Update()
        outputMesh.ShallowCopy(self.GetOutput())

class ExtractCellsNearSurface(ExtractBase):

    def __init__(self: Self, speHandler: bool = False,) -> None:
        super().__init__( speHandler )
    
   

    # TODO snake_case to camelCase
    def _getMask(self: Self) -> npt.NDArray:

        mask = np.zeros(self.mesh.GetNumberOfCells(), dtype=bool)
        numCells = self.mesh.GetNumberOfCells()

        surface_cell_ids = []
        for cid in range(numCells):
            if self.mesh.GetCellType(cid) in [
                VTK_TRIANGLE,
                VTK_QUAD,
                VTK_POLYGON,
            ]:  # bit 0 == 1 → FACE_GHOST → surface cell
                # print(f"{cid} is a surface")
                surface_cell_ids.append(cid)

        # Build point-to-cell map using GetPointCells
        pointToCells: dict[int, list[int]] = {}
        for pid in range(self.mesh.GetNumberOfPoints()):
            cell_ids = vtkIdList()
            self.mesh.GetPointCells(pid, cell_ids)
            pointToCells[pid] = [cell_ids.GetId(i) for i in range(cell_ids.GetNumberOfIds())]

        # Collect neighbors
        neighborCells = set()
        for cid in surface_cell_ids:
            cell = self.mesh.GetCell(cid)
            for i in range(cell.GetNumberOfPoints()):
                pid = cell.GetPointId(i)
                cell_ids = vtkIdList()
                self.mesh.GetPointCells(pid, cell_ids)
                for j in range(cell_ids.GetNumberOfIds()):
                    neigh = cell_ids.GetId(j)
                    if neigh != cid and self.mesh.GetCellType(neigh) not in [
                        VTK_TRIANGLE,
                        VTK_QUAD,
                        VTK_POLYGON,
                    ]:
                        neighborCells.add(neigh)

        mask[list(neighborCells)] = True

        return mask