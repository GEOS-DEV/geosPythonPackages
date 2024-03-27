from paraview.util.vtkAlgorithm import *
from paraview.selection import *
from checks import element_volumes


@smproxy.filter(name="Mesh Doctor(GEOS)")
@smproperty.input(name="Input")
@smdomain.datatype(dataTypes=["vtkUnstructuredGrid"], composite_data_supported=False)
class ElementVolumesFilter(VTKPythonAlgorithmBase):
    """
        Example portage meshDoctor in PV Python plugins
    """
    def __init__(self):
        super().__init__(outputType='vtkUnstructuredGrid')
        self.opt = element_volumes.Options(0)

    def RequestData(self, request, inInfo, outInfo):
        inData = self.GetInputData(inInfo, 0, 0)
        outData = self.GetOutputData(outInfo, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
        extracted = self._Process(inData)
        outData.DeepCopy( extracted.GetOutput() )
        outInfo.GetInformationObject(0).Set(outData.DATA_OBJECT(), extracted.GetOutput())

        print("1> There are {} cells under {} m3 vol".format(outData.GetNumberOfCells(), self.opt))
        return 1

    def _Process(self,mesh):
        from paraview.vtk import vtkIdTypeArray, vtkSelectionNode, vtkSelection, vtkCollection
        from vtk import vtkExtractSelection
        res = element_volumes.check(mesh, self.opt)
        ids = vtkIdTypeArray()
        ids.SetNumberOfComponents(1)
        for val in res.element_volumes:
            ids.InsertNextValue(val[0])


        selectionNode = vtkSelectionNode()
        selectionNode.SetFieldType(vtkSelectionNode.CELL)
        selectionNode.SetContentType(vtkSelectionNode.INDICES)
        selectionNode.SetSelectionList(ids)
        selection = vtkSelection()
        selection.AddNode(selectionNode)

        extracted = vtkExtractSelection()
        extracted.SetInputDataObject(0, mesh)
        extracted.SetInputData(1, selection)
        extracted.Update()
        print("There are {} cells under {} m3 vol".format(extracted.GetOutput().GetNumberOfCells(), self.opt))
        print("There are {} arrays of cell data".format(extracted.GetOutput().GetCellData().GetNumberOfArrays(), self.opt))

        return extracted

    @smproperty.doublevector(name="Vol Threshold", default_values=["0.0"])
    def SetValue(self, val):
        self.opt = element_volumes.Options(val)
        print("Settings value:", self.opt)
        self.Modified()
