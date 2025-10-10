# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
from enum import Enum
from typing import Any, Union

import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
from geos.utils.GeosOutputsConstants import (
    ComponentNameEnum,
    GeosMeshOutputsEnum,
)
from packaging.version import Version

# TODO: remove this condition when all codes are adapted for Paraview 6.0
import vtk
if Version( vtk.__version__ ) >= Version( "9.5" ):
    from vtkmodules.vtkFiltersParallel import vtkMergeBlocks
else:
    from paraview.modules.vtkPVVTKExtensionsMisc import (  # type: ignore[import-not-found]
        vtkMergeBlocks, )

from paraview.simple import (  # type: ignore[import-not-found]
    FindSource, GetActiveView, GetAnimationScene, GetDisplayProperties, GetSources, servermanager,
)
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkDataArraySelection,
    vtkDoubleArray,
    vtkPoints,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkDataObject,
    vtkMultiBlockDataSet,
    vtkPolyData,
    vtkTable,
    vtkUnstructuredGrid,
)

from geos.mesh.utils.arrayHelpers import (
    getArrayInObject,
    isAttributeInObject,
)

# valid sources for Python view configurator
# TODO: need to be consolidated
HARD_CODED_VALID_PVC_TYPE: set[ str ] = { "GeosLogReader", "RenameArrays" }


def vtkTableToDataframe( table: vtkTable ) -> pd.DataFrame:
    """From a vtkTable, creates and returns a pandas dataframe.

    Args:
        table (vtkTable): vtkTable object.

    Returns:
        pd.DataFrame: Pandas dataframe.
    """
    data: list[ dict[ str, Any ] ] = []
    for rowIndex in range( table.GetNumberOfRows() ):
        rowData: dict[ str, Any ] = {}
        for colIndex in range( table.GetNumberOfColumns() ):
            colName: str = table.GetColumnName( colIndex )
            cellValue: Any = table.GetValue( rowIndex, colIndex )
            # we have a vtkVariant value, we need a float
            cellValueF: float = cellValue.ToFloat()
            rowData[ colName ] = cellValueF
        data.append( rowData )
    df: pd.DataFrame = pd.DataFrame( data )
    return df


def vtkPolyDataToPointsDataframe( polydata: vtkPolyData ) -> pd.DataFrame:
    """Creates a pandas dataframe containing points data from vtkPolyData.

    Args:
        polydata (vtkPolyData): vtkPolyData object.

    Returns:
        pd.DataFrame: Pandas dataframe containing the points data.
    """
    points: vtkPoints = polydata.GetPoints()
    assert points is not None, "Points is undefined."
    nbrPoints: int = points.GetNumberOfPoints()
    data: dict[ str, Any ] = {
        "Point ID": np.empty( nbrPoints ),
        "PointsX": np.empty( nbrPoints ),
        "PointsY": np.empty( nbrPoints ),
        "PointsZ": np.empty( nbrPoints ),
    }
    for pointID in range( nbrPoints ):
        point: tuple[ float, float, float ] = points.GetPoint( pointID )
        data[ "Point ID" ][ pointID ] = pointID
        data[ "PointsX" ][ pointID ] = point[ 0 ]
        data[ "PointsY" ][ pointID ] = point[ 1 ]
        data[ "PointsZ" ][ pointID ] = point[ 2 ]
    pointData = polydata.GetPointData()
    nbrArrays: int = pointData.GetNumberOfArrays()
    for i in range( nbrArrays ):
        arrayToUse = pointData.GetArray( i )
        arrayName: str = pointData.GetArrayName( i )
        subArrayNames: list[ str ] = findSubArrayNames( arrayToUse, arrayName )
        # Collect the data for each sub array
        for ind, name in enumerate( subArrayNames ):
            data[ name ] = np.empty( nbrPoints )
            for k in range( nbrPoints ):
                # Every element of the tuple correspond to one distinct
                # sub array so we only need one value at a time
                value: float = arrayToUse.GetTuple( k )[ ind ]
                data[ name ][ k ] = value
    df: pd.DataFrame = pd.DataFrame( data ).set_index( "Point ID" )
    return df


def vtkUnstructuredGridCellsToDataframe( grid: vtkUnstructuredGrid ) -> pd.DataFrame:
    """Creates a pandas dataframe containing points data from vtkUnstructuredGrid.

    Args:
        grid (vtkUnstructuredGrid): vtkUnstructuredGrid object.

    Returns:
        pd.DataFrame: Pandas dataframe.
    """
    cellIdAttributeName = GeosMeshOutputsEnum.VTK_ORIGINAL_CELL_ID.attributeName
    cellData = grid.GetCellData()
    numberCells: int = grid.GetNumberOfCells()
    data: dict[ str, Any ] = {}
    for i in range( cellData.GetNumberOfArrays() ):
        arrayToUse = cellData.GetArray( i )
        arrayName: str = cellData.GetArrayName( i )
        subArrayNames: list[ str ] = findSubArrayNames( arrayToUse, arrayName )
        # Collect the data for each sub array
        for ind, name in enumerate( subArrayNames ):
            data[ name ] = np.empty( numberCells )
            for k in range( numberCells ):
                # Every element of the tuple correspond to one distinct
                # sub array so we only need one value at a time
                value: float = arrayToUse.GetTuple( k )[ ind ]
                data[ name ][ k ] = value
    df: pd.DataFrame = pd.DataFrame( data ).astype( { cellIdAttributeName: int } )

    # set cell ids as index

    # df = df.astype({cellIdAttributeName: int})
    return df.set_index( cellIdAttributeName )


def vtkToDataframe( dataset: vtkDataObject ) -> pd.DataFrame:
    """Creates a dataframe containing points data from vtkTable or vtkPolyData.

    Args:
        dataset (Any): dataset to convert if possible.

    Returns:
        pd.DataFrame: if the dataset is in the right format.
    """
    if isinstance( dataset, vtkTable ):
        return vtkTableToDataframe( dataset )
    elif isinstance( dataset, vtkPolyData ):
        return vtkPolyDataToPointsDataframe( dataset )
    elif isinstance( dataset, vtkUnstructuredGrid ):
        return vtkUnstructuredGridCellsToDataframe( dataset )
    else:
        raise AssertionError( f"Invalid dataset format {type(dataset)}. " +
                              "Supported formats are: vtkTable, vtkpolyData and vtkUnstructuredGrid" )


def findSubArrayNames( vtkArray: vtkDataArray, arrayName: str ) -> list[ str ]:
    """Get sub array names from multi array attributes.

    Because arrays in ParaView can be of multiple dimensions,
    it can be difficult to convert these arrays to numpy arrays.
    Therefore, we can split the original array into multiple sub
    one dimensional arrays. In that case, new sub names need to be
    derived from the original array to be used.

    Args:
        vtkArray (vtkDataArray): Array from vtk library.
        arrayName (str): Name of the array.

    Returns:
        list[str]: Sub array names from original array name.
    """
    # The ordering of six elements can seem odd but is adapted to
    # Geos output format of stress as :
    # sigma11, sigma22, sigma33, sigma23, sigma13, sigma12
    sixComponents: tuple[ str, str, str, str, str, str ] = ComponentNameEnum.XYZ.value
    nbrComponents: int = vtkArray.GetNumberOfComponents()
    subArrayNames: list[ str ] = []
    if nbrComponents == 1:
        subArrayNames.append( arrayName )
    elif nbrComponents < 6:
        for j in range( nbrComponents ):
            subArrayNames.append( arrayName + "_" + sixComponents[ j ] )
    else:
        for j in range( nbrComponents ):
            subArrayNames.append( arrayName + "_" + str( j ) )
    return subArrayNames


def getDataframesFromMultipleVTKSources( sourceNames: set[ str ], commonColumn: str ) -> list[ pd.DataFrame ]:
    """Creates the dataframe from each source if they have the commonColumn.

    Args:
        sourceNames (set[str]): list of sources.
        commonColumn (str): common column name.

    Returns:
        list[pd.DataFrame]: output dataframe.
    """
    # indexSource: int = commonColumn.rfind("__")
    # commonColumnNoSource: str = commonColumn[:indexSource]
    validDataframes: list[ pd.DataFrame ] = []
    for name in sourceNames:
        source = FindSource( name )
        assert source is not None, "Source is undefined."
        dataset = servermanager.Fetch( source )
        assert dataset is not None, "Dataset is undefined."
        currentDF: pd.DataFrame = vtkToDataframe( dataset )
        if commonColumn in currentDF.columns:
            dfModified = currentDF.rename(
                columns={ col: col + "__" + name
                          for col in currentDF.columns if col != commonColumn } )
            validDataframes.append( dfModified )
        else:
            print( f"The source <<{name}>> could not be used" + " to plot because the variable named <<" +
                   f"{commonColumn}>> could not be found." )
    return validDataframes


def mergeDataframes( dataframes: list[ pd.DataFrame ], commonColumn: str ) -> pd.DataFrame:
    """Merge all dataframes into a single one by using the common column.

    Args:
        dataframes (list[pd.DataFrame]): List of dataframes from
            getDataframesFromMultipleVTKSources.
        commonColumn (str): Name of the only common column between
            all of the dataframes.

    Returns:
        pd.DataFrame: Merged dataframes into a single one by 'outer'
        on the commonColumn.
    """
    assert len( dataframes ) > 0
    if len( dataframes ) == 1:
        return dataframes[ 0 ]
    else:
        df0: pd.DataFrame = dataframes[ 0 ]
        df1: pd.DataFrame = dataframes[ 1 ]
        merged: pd.DataFrame = df0.merge( df1, on=commonColumn, how="outer" )
        if len( dataframes ) > 2:
            for df in dataframes[ 2: ]:
                merged = merged.merge( df, on=commonColumn, how="outer" )
        return merged


def addDataframeColumnsToVtkPolyData( polyData: vtkPolyData, df: pd.DataFrame ) -> vtkPolyData:
    """Add columns from a dataframe to a vtkPolyData.

    Args:
        polyData (vtkPolyData): vtkPolyData before modifcation.
        df (pd.DataFrame): Pandas dataframe.

    Returns:
        vtkPolyData: vtkPolyData with new arrays.
    """
    for column_name in df.columns:
        column = df[ column_name ].values
        array = vtkDoubleArray()
        array.SetName( column_name )
        array.SetNumberOfValues( polyData.GetNumberOfPoints() )
        for i in range( polyData.GetNumberOfPoints() ):
            array.SetValue( i, column[ i ] )
        polyData.GetPointData().AddArray( array )

    # Update vtkPolyData object
    polyData.GetPointData().Modified()
    polyData.Modified()
    return polyData


# Functions to help the processing of PythonViewConfigurator


def getPossibleSourceNames() -> set[ str ]:
    """Get the list of valid source names for PythonViewConfigurator.

    In PythonViewConfigurator, multiple sources can be considered as
    valid inputs. We want the user to know the names of every of these
    sources that can be used to plot data. This function therefore identifies
    which source names are valid to be used later as sources.

    Returns:
        set[str]: Source names in the paraview pipeline.
    """
    # get all sources different from PythonViewConfigurator
    validNames: set[ str ] = set()
    for k in GetSources():
        sourceName: str = k[ 0 ]
        source = FindSource( sourceName )
        if ( source is not None ) and ( "PythonViewConfigurator" not in source.__str__() ):
            dataset = servermanager.Fetch( source )
            if dataset.IsA( "vtkPolyData" ) or dataset.IsA( "vtkTable" ):
                validNames.add( sourceName )
    return validNames


def usefulSourceNamesPipeline() -> set[ str ]:
    """Get the list of valid pipelines for PythonViewConfigurator.

    When using the PythonViewConfigurator, we want to check if the sources
    in the ParaView pipeline are compatible with what the filter can take as
    input. So this function scans every sources of the pipeline and if it
    corresponds to one of the hardcoded valid types, we keep the name.
    They are right now : ["GeosLogReader", "RenameArrays"]

    Returns:
        set[str]: [sourceName1, ..., sourceNameN]
    """
    usefulSourceNames: set[ str ] = set()
    allSourceNames: set[ str ] = { n[ 0 ] for n, s in GetSources().items() }
    for name in allSourceNames:
        source = FindSource( name )
        if type( source ).__name__ in HARD_CODED_VALID_PVC_TYPE:
            usefulSourceNames.add( name )
    return usefulSourceNames


def getDatasFromSources( sourceNames: set[ str ] ) -> dict[ str, pd.DataFrame ]:
    """Get the data from input sources.

    Args:
        sourceNames (set[str]): [sourceName1, ..., sourceNameN]

    Returns:
        dict[[str, pd.DataFrame]]: dictionary where source names are keys and
        dataframe are values.
        { sourceName1: servermanager.Fetch(FindSource(sourceName1)),
        ...
        sourceNameN: servermanager.Fetch(FindSource(sourceNameN)) }
    """
    usefulDatas: dict[ str, Any ] = {}
    for name in sourceNames:
        dataset = servermanager.Fetch( FindSource( name ) )
        usefulDatas[ name ] = dataset
    return usefulDatas


def usefulVisibleDatasPipeline() -> dict[ str, Any ]:
    """Get the list of visible pipelines.

    When using the PythonViewConfigurator, we want to collect the data of
    each source that is visible in the paraview pipeline and that is
    compatible as input data for the filter. Therefore, only certain types of
    sources will be considered as valid. They are right now :
    ["GeosLogReader", "RenameArrays"]

    Finally, if the sources are visible and valid, we access their data and
    return the names of the source and their respective data.

    Returns:
        dict[str, 'vtkInformation']: dictionary of source names and data from
        pipeline.
        { sourceName1: servermanager.Fetch(FindSource(sourceName1)),
        ...
        sourceNameN: servermanager.Fetch(FindSource(sourceNameN)) }
    """
    usefulDatas: dict[ str, Any ] = {}
    sourceNamesVisible: set[ str ] = set()
    for n, s in GetSources().items():
        if servermanager.GetRepresentation( s, GetActiveView() ) is not None:
            displayProperties = GetDisplayProperties( s, view=GetActiveView() )
            if ( displayProperties is not None ) and ( displayProperties.Visibility == 1 ):
                sourceNamesVisible.add( n[ 0 ] )

    for name in sourceNamesVisible:
        source = FindSource( name )
        if type( source ).__name__ in HARD_CODED_VALID_PVC_TYPE:
            usefulDatas[ name ] = servermanager.Fetch( FindSource( name ) )
    return usefulDatas


def isFilter( sourceName: str ) -> bool:
    """Identify if a source name can link to a filter in the ParaView pipeline.

    Args:
        sourceName (str): name of a source object in the pipeline

    Returns:
        bool: True if filter, False instead.
    """
    source: Any = FindSource( sourceName )
    if source is None:
        print( f"sourceName <<{sourceName}>> does not exist in the pipeline" )
        return False
    else:
        try:
            test: Any = source.GetClientSideObject().GetInputAlgorithm()  # noqa: F841
            return True
        except Exception:
            return False


def getFilterInput( sourceName: str ) -> vtkDataObject:
    """Access the vtk dataset that is used as input for a filter.

    Args:
        sourceName (str): name of a source object in the pipeline.

    Returns:
        Any: The vtk dataset that serves as input for the filter.
    """
    filtre = FindSource( sourceName )
    assert filtre is not None, "Source is undefined."
    clientSideObject = filtre.GetClientSideObject()
    assert clientSideObject is not None, "Client Side Object is undefined."
    inputAlgo = clientSideObject.GetInputAlgorithm()
    assert inputAlgo is not None, "Input Algorithm is undefined."
    inputValues = inputAlgo.GetInput()
    if isinstance( inputValues, vtkDataObject ):
        return inputValues
    return vtkDataObject()


def getArrayChoices( array: vtkDataArraySelection ) -> list[ str ]:
    """Extracts the column names of input array when they are enabled.

    Args:
        array (vtkDataArraySelection): input data

    Returns:
        set[str]: [columnName1, ..., columnNameN]
    """
    checkedColumns: list[ str ] = []
    for i in range( array.GetNumberOfArrays() ):
        columnName: str = array.GetArrayName( i )
        if array.ArrayIsEnabled( columnName ):
            checkedColumns.append( columnName )
    return checkedColumns


def integrateSourceNames( sourceNames: set[ str ], arrayChoices: set[ str ] ) -> set[ str ]:
    """Aggregate source and arrayChoices names.

    When creating the user choices in PythonViewConfigurator, you need
    to take into account both the source names and the choices of curves
    to have user choices corresponding to the column names of the dataframe
    with the data to be plot.

    Args:
        sourceNames (set[str]): Name of sources found in ParaView pipeline.
        arrayChoices (set[str]): Column names of the vtkdataarrayselection.

    Returns:
        set[str]: [sourceName1__choice1, sourceName1__choice2,
                    ..., sourceNameN__choiceN]
    """
    completeNames: set[ str ] = set()
    for sourceName in sourceNames:
        for choice in arrayChoices:
            completeName: str = choice + "__" + sourceName
            completeNames.add( completeName )
    return completeNames


def getVtkOriginalCellIds( mesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet, vtkDataObject ] ) -> list[ str ]:
    """Get vtkOriginalCellIds from a vtkUnstructuredGrid object.

    Args:
        mesh (vtkMultiBlockDataSet|vtkCompositeDataSet|vtkDataObject): input mesh.

    Returns:
        list[str]: ids of the cells.
    """
    # merge blocks for vtkCompositeDataSet
    mesh2: vtkUnstructuredGrid = mergeFilterPV( mesh )
    name: str = GeosMeshOutputsEnum.VTK_ORIGINAL_CELL_ID.attributeName
    assert isAttributeInObject( mesh2, name, False ), f"Attribute {name} is not in the mesh."
    return [ str( int( ide ) ) for ide in getArrayInObject( mesh2, name, False ) ]


def strEnumToEnumerationDomainXml( enumObj: Enum ) -> str:
    """Creates an enumeration domain from an Enum objec.

    Creates an enumeration domain from an Enum objec
    for the dropdown widgets of paraview plugin.

    Args:
        enumObj (Enum): Enumeration values to put in the dropdown widget.

    Returns:
        str: the XML string.
    """
    xml: str = """<EnumerationDomain name='enum'>"""
    for i, unitObj in enumerate( list( enumObj ) ):  # type: ignore[call-overload]
        xml += f"""<Entry text='{unitObj.value}' value='{i}'/>"""
    xml += """</EnumerationDomain>"""
    return xml


def strListToEnumerationDomainXml( properties: Union[ list[ str ], set[ str ] ] ) -> str:
    """Creates an enumeration domain from a list of strings.

    Creates an enumeration domain from a list of strings
    for the dropdown widgets of paraview plugin.

    Args:
        properties (set[str] | list[str]): Properties to put in the dropdown widget.

    Returns:
        str: the XML string.
    """
    xml: str = """<EnumerationDomain name='enum'>"""
    for i, prop in enumerate( list( properties ) ):
        xml += f"""<Entry text='{prop}' value='{i}'/>"""
    xml += """</EnumerationDomain>"""
    return xml


def dataframeForEachTimestep( sourceName: str ) -> dict[ str, pd.DataFrame ]:
    """Get the data from source at each time step.

    In ParaView, a source object can contain data for multiple
    timesteps. If so, knowing the source name, we can access its data
    for each timestep and store it in a dict where the keys are the
    timesteps and the values the data at each one of them.

    Args:
        sourceName (str): Name of the source in ParaView pipeline.

    Returns:
        dict[str, pd.DataFrame]: dictionary where time is the key and dataframe
        is the value.
    """
    animationScene = GetAnimationScene()
    assert animationScene is not None, "animationScene is undefined."
    # we set the animation to the initial timestep
    animationScene.GoToFirst()
    source = FindSource( sourceName )
    dataset: vtkDataObject = servermanager.Fetch( source )
    assert dataset is not None, "Dataset is undefined."
    dataset2: vtkUnstructuredGrid = mergeFilterPV( dataset )
    time: str = str( animationScene.TimeKeeper.Time )
    dfPerTimestep: dict[ str, pd.DataFrame ] = { time: vtkToDataframe( dataset2 ) }
    # then we iterate on the other timesteps of the source
    for _ in range( animationScene.NumberOfFrames ):  # type: ignore
        animationScene.GoToNext()
        source = FindSource( sourceName )
        dataset = servermanager.Fetch( source )
        dataset2 = mergeFilterPV( dataset )
        time = str( animationScene.TimeKeeper.Time )
        dfPerTimestep[ time ] = vtkToDataframe( dataset2 )
    return dfPerTimestep


def getTimeStepIndex( time: float, timeSteps: npt.NDArray[ np.float64 ] ) -> int:
    """Get the time step index of input time from the list of time steps.

    Args:
        time (float): time
        timeSteps (npt.NDArray[np.float64]): Array of time steps

    Returns:
        int: time step index
    """
    indexes: npt.NDArray[ np.int64 ] = np.where( np.isclose( timeSteps, time ) )[ 0 ]
    assert ( indexes.size > 0 ), f"Current time {time} does not exist in the selected object."
    return int( indexes[ 0 ] )


def mergeFilterPV( input: vtkDataObject, ) -> vtkUnstructuredGrid:
    """Apply Paraview merge block filter.

    Args:
        input (vtkMultiBlockDataSet | vtkCompositeDataSet | vtkDataObject): composite
            object to merge blocks

    Returns:
        vtkUnstructuredGrid: merged block object

    """
    mergeFilter: vtkMergeBlocks = vtkMergeBlocks()
    mergeFilter.SetInputData( input )
    mergeFilter.Update()
    return mergeFilter.GetOutputDataObject( 0 )
