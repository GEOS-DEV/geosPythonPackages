import argparse

import pyvista as pv
from vtkmodules.vtkCommonCore import (
    reference,
    vtkIdList,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCellLocator,
    vtkCellTreeLocator,
    vtkDataAssembly,
    vtkGenericCell,
    vtkPartitionedDataSetCollection,
    vtkStaticCellLocator,
)
from vtkmodules.vtkCommonSystem import vtkTimerLog
from vtkmodules.vtkFiltersCore import (
    vtkAppendFilter,
)
from vtkmodules.vtkFiltersFlowPaths import vtkModifiedBSPTree
from vtkmodules.vtkFiltersGeneral import (
    vtkOBBTree,
)
from vtkmodules.vtkIOXML import (
    vtkXMLPartitionedDataSetCollectionReader,
)


def parsing() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Test Cell Locator onto VTK files")

    parser.add_argument(
        "-vtpc",
        "--vtpcFilepath",
        type=str,
        default="",
        help="path to .vtpc file.",
        required=True,
    )

    return parser


def main(args: argparse.Namespace) -> None:
    reader = vtkXMLPartitionedDataSetCollectionReader()
    reader.SetFileName(args.vtpcFilepath)
    reader.Update()
    pdsc: vtkPartitionedDataSetCollection = reader.GetOutput()

    assembly: vtkDataAssembly = pdsc.GetDataAssembly()
    root_name: str = assembly.GetNodeName(assembly.GetRootNode())

    # 1. Get Mesh
    mesh = assembly.GetFirstNodeByPath("//" + root_name + "/Mesh")

    append_filter = vtkAppendFilter()
    append_filter.SetMergePoints(True)
    append_filter.SetTolerance(0.0)
    if mesh > 0:
        for sub_node in assembly.GetChildNodes(mesh, False):
            datasets = assembly.GetDataSetIndices(sub_node, False)
            for d in datasets:
                dataset = pdsc.GetPartitionedDataSet(d)
                append_filter.AddInputData(dataset.GetPartition(0))
    else:
        raise Exception("No mesh found")

    append_filter.Update()
    output = append_filter.GetOutputDataObject(0)

    # 2. Get Perforations
    # Create points array which are positions to probe data with
    # FindCell(), We also create an array to hold the results of this
    # probe operation.
    # ProbeCells = vtkPoints()
    # ProbeCells.SetDataTypeToDouble()
    ProbeCells: list[pv.PointSet] = []
    wells = assembly.GetFirstNodeByPath("//" + root_name + "/Wells")
    if wells > 0:
        for well in assembly.GetChildNodes(wells, False):
            sub_nodes = assembly.GetChildNodes(well, False)
            for sub_node in sub_nodes:
                if assembly.GetNodeName(sub_node) == "Perforations":
                    for i, perfos in enumerate(assembly.GetChildNodes(sub_node, False)):
                        datasets = assembly.GetDataSetIndices(perfos, False)
                        for d in datasets:
                            dataset = pdsc.GetPartitionedDataSet(d)
                            if dataset.GetPartition(0) is not None:
                                pointset = dataset.GetPartition(0)
                                ProbeCells.append(pv.wrap(pointset))
                                # ProbeCells.InsertNextPoint(pointset.GetPoint(0))
    else:
        raise Exception("No wells found")

    # numProbes = ProbeCells.GetNumberOfPoints()
    numProbes = len(ProbeCells)

    closest = vtkIdList()
    closest.SetNumberOfIds(numProbes)
    treeClosest = vtkIdList()
    treeClosest.SetNumberOfIds(numProbes)
    staticClosest = vtkIdList()
    staticClosest.SetNumberOfIds(numProbes)
    bspClosest = vtkIdList()
    bspClosest.SetNumberOfIds(numProbes)
    obbClosest = vtkIdList()
    obbClosest.SetNumberOfIds(numProbes)
    dsClosest = vtkIdList()
    dsClosest.SetNumberOfIds(numProbes)

    genCell = vtkGenericCell()
    pc = [0, 0, 0]
    weights = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    subId = reference(0)

    # Print initial statistics
    print(f"Processing NumCells: {output.GetNumberOfCells()}")
    print("\n")
    timer = vtkTimerLog()

    #############################################################
    # Time the creation and building of the static cell locator
    locator2 = vtkStaticCellLocator()
    locator2.SetDataSet(output)
    locator2.AutomaticOn()
    locator2.SetNumberOfCellsPerNode(20)

    timer.StartTimer()
    locator2.BuildLocator()
    timer.StopTimer()
    time = timer.GetElapsedTime()
    print(f"Build Static Cell Locator: {time}")

    # Probe the dataset with FindClosestPoint() and time it
    timer.StartTimer()
    for i, m in enumerate(ProbeCells):
        staticClosest.SetId(
            i, locator2.FindCell(m.GetPoint(0))
        )  # ,0.001,genCell,pc,weights))
    # for i in range (0,numProbes):
    #     staticClosest.SetId(i, locator2.FindCell(ProbeCells.GetPoint(i)) #,0.001,genCell,pc,weights))
    timer.StopTimer()
    opTime = timer.GetElapsedTime()
    print(f"    Find cell probing: {opTime}")

    # Time the deletion of the locator. The incremental locator is quite slow due
    # to fragmented memory.
    timer.StartTimer()
    del locator2
    timer.StopTimer()
    time2 = timer.GetElapsedTime()
    print(f"    Delete Static Cell Locator: {time2}")
    print(f"    Static Cell Locator (Total): {time + opTime + time2}")
    print("\n")

    #############################################################
    # Time the creation and building of the standard cell locator
    locator = vtkCellLocator()
    locator.SetDataSet(output)
    locator.SetNumberOfCellsPerBucket(25)
    locator.AutomaticOn()

    timer.StartTimer()
    locator.BuildLocator()
    timer.StopTimer()
    time = timer.GetElapsedTime()
    print(f"Build Cell Locator: {time}")

    # Probe the dataset with FindClosestPoint() and time it
    timer.StartTimer()
    for i, m in enumerate(ProbeCells):
        closest.SetId(i, locator.FindCell(m.GetPoint(0)))  # ,0.001,genCell,pc,weights))
    # for i in range (0,numProbes):
    #     closest.SetId(i, locator.FindCell(ProbeCells.GetPoint(i),0.001,genCell,pc,weights))
    timer.StopTimer()
    opTime = timer.GetElapsedTime()
    print(f"    Find cell probing: {opTime}")

    # Time the deletion of the locator. The standard locator is quite slow due
    # to fragmented memory.
    timer.StartTimer()
    del locator
    timer.StopTimer()
    time2 = timer.GetElapsedTime()
    print(f"    Delete Cell Locator: {time2}")
    print(f"    Cell Locator (Total): {time + opTime + time2}")
    print("\n")

    #############################################################
    # Time the creation and building of the cell tree locator
    locator1 = vtkCellTreeLocator()
    locator1.SetDataSet(output)
    locator1.AutomaticOn()

    timer.StartTimer()
    locator1.BuildLocator()
    timer.StopTimer()
    time = timer.GetElapsedTime()
    print(f"Build Cell Tree Locator: {time}")

    # Probe the dataset with FindClosestPoint() and time it
    timer.StartTimer()
    for i, m in enumerate(ProbeCells):
        treeClosest.SetId(
            i, locator1.FindCell(m.GetPoint(0))
        )  # ,0.001,genCell,pc,weights))
    # for i in range (0,numProbes):
    #     treeClosest.SetId(i, locator1.FindCell(ProbeCells.GetPoint(i),0.001,genCell,pc,weights))
    timer.StopTimer()
    opTime = timer.GetElapsedTime()
    print(f"    Find cell probing: {opTime}")

    # Time the deletion of the locator. The incremental locator is quite slow due
    # to fragmented memory.
    timer.StartTimer()
    del locator1
    timer.StopTimer()
    time2 = timer.GetElapsedTime()
    print(f"    Delete Cell Tree Locator: {time2}")
    print(f"    Cell Tree Locator (Total): {time + opTime + time2}")
    print("\n")

    #############################################################
    # Time the creation and building of the bsp tree
    locator3 = vtkModifiedBSPTree()
    locator3.SetDataSet(output)
    locator3.AutomaticOn()

    timer.StartTimer()
    locator3.BuildLocator()
    timer.StopTimer()
    time = timer.GetElapsedTime()
    print(f"Build BSP Tree Locator: {time}")

    # Probe the dataset with FindClosestPoint() and time it
    timer.StartTimer()
    for i, m in enumerate(ProbeCells):
        bspClosest.SetId(
            i, locator3.FindCell(m.GetPoint(0))
        )  # ,0.001,genCell,pc,weights))
    # for i in range (0,numProbes):
    #     bspClosest.SetId(i, locator3.FindCell(ProbeCells.GetPoint(i),0.001,genCell,pc,weights))
    timer.StopTimer()
    opTime = timer.GetElapsedTime()
    print(f"    Find cell probing: {opTime}")

    # Time the deletion of the locator. The incremental locator is quite slow due
    # to fragmented memory.
    timer.StartTimer()
    del locator3
    timer.StopTimer()
    time2 = timer.GetElapsedTime()
    print(f"    Delete BSP Tree Locator: {time2}")
    print(f"    BSP Tree Locator (Total): {time + opTime + time2}")
    print("\n")

    #############################################################
    # Time the creation and building of the obb tree
    locator4 = vtkOBBTree()
    locator4.SetDataSet(output)
    locator4.AutomaticOn()

    timer.StartTimer()
    locator4.BuildLocator()
    timer.StopTimer()
    time = timer.GetElapsedTime()
    print(f"Build OBB Locator: {time}")

    # Probe the dataset with FindClosestPoint() and time it
    timer.StartTimer()
    for i, m in enumerate(ProbeCells):
        obbClosest.SetId(
            i, locator4.FindCell(m.GetPoint(0))
        )  # ,0.001,genCell,pc,weights))
    # for i in range (0,numProbes):
    #     obbClosest.SetId(i, locator4.FindCell(ProbeCells.GetPoint(i))) #,0.001,genCell,pc,weights))
    timer.StopTimer()
    opTime = timer.GetElapsedTime()
    print(f"    Find cell probing: {opTime}")

    # Time the deletion of the locator. The incremental locator is quite slow due
    # to fragmented memory.
    timer.StartTimer()
    del locator4
    timer.StopTimer()
    time2 = timer.GetElapsedTime()
    print(f"    Delete OBB Locator: {time2}")
    print(f"    OBB Locator (Total): {time + opTime + time2}")
    print("\n")

    #############################################################
    # For comparison purposes compare to FindCell()
    timer.StartTimer()

    # output.FindCell(ProbeCells.GetPoint(0),genCell,-1,0.001,subId,pc,weights)
    timer.StopTimer()
    time = timer.GetElapsedTime()
    print(f"Point Locator: {time}")

    # Probe the dataset with FindClosestPoint() and time it
    timer.StartTimer()
    for i, m in enumerate(ProbeCells):
        dsClosest.SetId(
            i, output.FindCell(m.GetPoint(0), genCell, -1, 0.001, subId, pc, weights)
        )
    # for i in range (0,numProbes):
    #     dsClosest.SetId(i, output.FindCell(ProbeCells.GetPoint(0),genCell,-1,0.001,subId,pc,weights))
    timer.StopTimer()
    opTime = timer.GetElapsedTime()
    print(f"    Find cell probing: {opTime}")

    # Time the deletion of the locator. The incremental locator is quite slow due
    # to fragmented memory.
    timer.StartTimer()
    del output
    timer.StopTimer()
    time2 = timer.GetElapsedTime()
    print(f"    Delete Point Locator: {time2}")
    print(f"    Point Locator (Total): {time + opTime + time2}")
    print("\n")


def run() -> None:
    parser = parsing()
    args, unknown_args = parser.parse_known_args()
    main(args)


if __name__ == "__main__":
    run()
