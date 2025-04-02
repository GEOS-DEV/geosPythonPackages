# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
import contextlib
import re
from copy import deepcopy
from typing import Any, Union

from geos_utils.enumUnits import Unit, convert

__doc__ = """Functions to read and process Geos log."""


def extractRegion( geosLogLine: str ) -> str:
    """Extracts the name of the region from a Geos log line.

    Args:
        geosLogLine (str): #expected line : "Adding Object CellElementRegion
        named Reservoir from ObjectManager::Catalog."

    Raises:
        ValueError: "Not enough elements to unpack in line."
        ValueError: "An error has occured while parsing a line."


    Returns:
        str: "Reservoir"
    """
    try:
        lineElements: list[ str ] = geosLogLine.split()
        namedElementIndex: int = lineElements.index( "named" )
        if len( lineElements ) > namedElementIndex + 1:
            return lineElements[ namedElementIndex + 1 ]
        else:
            raise ValueError( "Not enough elements to unpack in region line <<" + geosLogLine + ">>" )
    except Exception as e:
        raise ValueError( "An error has occured while parsing region line <<" + geosLogLine + ">>" ) from e


def extractWell( geosLogLine: str ) -> str:
    """Extracts the name of the well from a Geos log line.

    Args:
        geosLogLine (str): #expected line :
            "   TableFunction: wellControls_ConstantBHP_table"
            Or
            "   TableFunction: wellControls_ConstantPhaseRate_table"

    Raises:
        ValueError: "An error has occured while parsing <<" + geosLogLine + ">>"

    Returns:
        str: "wellControls"
    """
    try:
        lineElements: list[ str ] = geosLogLine.split( ":" )
        wellName: str = lineElements[ 1 ].replace( " ", "" )
        indexEndName: int
        if "_ConstantBHP_table" in wellName:
            indexEndName = wellName.index( "_ConstantBHP_table" )
        elif "_ConstantPhaseRate_table" in wellName:
            indexEndName = wellName.index( "_ConstantPhaseRate_table" )
        else:
            raise ValueError( "The expected format was not found when parsing line <<" + geosLogLine + ">>" )
        return wellName[ :indexEndName ]
    except Exception as e:
        raise ValueError( "An error has occured while parsing region line <<" + geosLogLine + ">>" ) from e


def extractAquifer( geosLogLine: str ) -> str:
    """Extracts the name of the aquifer from a Geos log line.

    Args:
        geosLogLine (str): #expected line : "   TableFunction:
            aquifer1_pressureInfluence_table"

    Raises:
        ValueError: "An error has occured while parsing <<"
            + geosLogLine
            + ">>"

    Returns:
        str: "aquifer1"
    """
    try:
        lineElements: list[ str ] = geosLogLine.split( ":" )
        aquiferName: str = lineElements[ 1 ].replace( " ", "" )
        indexEndName: int = aquiferName.index( "_pressureInfluence_table" )
        return aquiferName[ :indexEndName ]
    except Exception as e:
        raise ValueError( "An error has occured while parsing region line <<" + geosLogLine + ">>" ) from e


def extractStatsName( geosLogLine: str ) -> str:
    """Extracts the name of the computed statistics name from a Geos log line.

    Args:
        geosLogLine (str): #expected line :"compflowStatistics, Reservoir:
            Pressure (min, average, max): 2.86419e+07, 2.93341e+07, 3.006e+07 Pa"

    Returns:
        str: "compflowStatistics"
    """
    lineElements: list[ str ] = geosLogLine.split( "," )
    return lineElements[ 0 ]


def extractPhaseModel( geosLogLine: str ) -> str:
    """Extracts the name of a phase model from a Geos log line.

    Args:
        geosLogLine (str): #expected line : "   TableFunction:
            fluid_phaseModel1_PhillipsBrineDensity_table"

    Raises:
        ValueError: "Not enough elements to unpack in line <<" + geosLogLine + ">>."
        ValueError: "An error has occured while parsing <<" + geosLogLine + ">>"

    Returns:
        str: "PhillipsBrineDensity"
    """
    try:
        cleanLine: str = replaceSpecialCharactersWithWhitespace( geosLogLine )
        lineElements: list[ str ] = cleanLine.split()
        phaseModels: list[ str ] = [ elt for elt in lineElements if "phaseModel" in elt ]
        matchingPhaseModel: str = phaseModels[ 0 ]
        phaseModelElementIndex: int = lineElements.index( matchingPhaseModel )
        if len( lineElements ) > phaseModelElementIndex + 1:
            return lineElements[ phaseModelElementIndex + 1 ]
        else:
            raise ValueError( "Not enough elements to unpack in <<" + geosLogLine + ">>" )
    except Exception as e:
        raise ValueError( "An error has occured while parsing <<" + geosLogLine + ">>" ) from e


def extractPropertiesFlow( geosLogLine: str, phasesName: list[ str ] ) -> list[ str ]:
    """Extracts flow property from a Geos log line.

    Args:
        geosLogLine (str): #expected line :
            "compflowStatistics, Reservoir: Delta pressure (min, max): 0, 0 Pa"
        phasesName (list[str]): ["CO2","Water"]

    Raises:
        ValueError: "Not enough elements to unpack in line <<" + geosLogLine + ">>."
        ValueError: "An error has occured while parsing <<" + geosLogLine + ">>"

    Returns:
        list[str]: ["Reservoir__DeltaPressureMin", "Reservoir__DeltaPressureMax"]
    """
    try:
        lineBlocks: list[ str ] = geosLogLine.split( ":" )
        if len( lineBlocks ) == 3:
            propertyLineBlock: str = lineBlocks[ 1 ]
            propertiesName: list[ str ] = buildPropertiesNameFromGeosProperties( propertyLineBlock, phasesName )
            statsBlock: str = lineBlocks[ 0 ]
            statsElements: list[ str ] = statsBlock.split()
            if len( statsElements ) >= 2:
                regionName: str = statsElements[ 1 ]
                formattedRegion: str = formatPropertyName( regionName )
                formattedProps = [ formatPropertyName( prop ) for prop in propertiesName ]
                propertiesFlow: list[ str ] = [ formattedRegion + "__" + prop for prop in formattedProps ]
                return propertiesFlow
        else:
            raise ValueError( "Incorrect number of blocks in line <<" + geosLogLine +
                              ">> for it to find property name." )
    except Exception as e:
        raise ValueError( "An error has occured while parsing <<" + geosLogLine + ">>" ) from e
    return []


def buildPropertiesNameFromGeosProperties( geosProperties: str, phasesName: list[ str ] ) -> list[ str ]:
    """Extracts the property name and its extensions like min, max, average.

    Args:
        geosProperties (str): " Delta pressure (min, max)"
        phasesName (list[str]): ["CO2","Water"]

    Returns:
        list[str]: [" Delta pressure  min", " Delta pressure  max"]
    """
    separatedNameAndExtension: list[ str ] = geosProperties.split( "(" )
    nameBlock: str = separatedNameAndExtension[ 0 ]
    finalPropertiesName: list[ str ] = []
    if " phase " in geosProperties or " Phase " in geosProperties:
        finalPropertiesName = buildPropertiesNameForPhases( nameBlock, phasesName )
    elif " component " in geosProperties or " Component " in geosProperties:
        finalPropertiesName = buildPropertiesNameForComponents( phasesName )
    else:
        # means that extensions have been found
        if len( separatedNameAndExtension ) == 2:
            extensions: str = separatedNameAndExtension[ 1 ]
            finalPropertiesName = buildPropertiesNameNoPhases( nameBlock, extensions )
        else:
            finalPropertiesName = buildPropertiesNameNoPhases( nameBlock )
    return finalPropertiesName


def buildPropertiesNameForPhases( nameBlock: str, phasesName: list[ str ] ) -> list[ str ]:
    """Replace phase by phase names.

    Args:
        nameBlock (str): " Mobile phase mass"
        phasesName (list[str]): ["CO2","Water"]

    Returns:
        list[str]: ['Mobile CO2 mass', 'Mobile Water mass']
    """
    propertiesName: list[ str ] = []
    for phaseName in phasesName:
        if " phase " in nameBlock:
            newName: str = nameBlock.replace( "phase", phaseName )
        else:
            newName = nameBlock.replace( "Phase", phaseName )
        propertiesName.append( newName )
    return propertiesName


def buildPropertiesNameForComponents( phasesName: list[ str ] ) -> list[ str ]:
    """Builds the list of component property names from the list of phases name.

    Args:
        phasesName (list): ["CO2","Water"]

    Returns:
        list: ['Dissolved mass CO2 in CO2','Dissolved mass Water in CO2',
        'Dissolved mass CO2 in Water','Dissolved mass Water in Water']
    """
    propertiesName: list[ str ] = []
    for i in range( len( phasesName ) ):
        for j in range( len( phasesName ) ):
            newName: str = f"Dissolved mass {phasesName[j]} in {phasesName[i]}"
            propertiesName.append( newName )
    return propertiesName


def buildPropertiesNameNoPhases( nameBlock: str, extensions: str = "" ) -> list[ str ]:
    """From a name block and extensions, builds a list of properties name.

    Args:
        nameBlock (str): " Delta pressure "
        extensions (str): "min, max)"

    Returns:
        list: [" Delta pressure  min", " Delta pressure  max"]
    """
    if extensions != "" and "metric" not in extensions:
        extensionsClean = replaceSpecialCharactersWithWhitespace( extensions )
        extensionsName = extensionsClean.split()
        propertiesName = [ nameBlock + " " + ext for ext in extensionsName ]
    else:
        propertiesName = [ nameBlock ]
    return propertiesName


def identifyProperties( properties: list[ str ] ) -> list[ str ]:
    """Identify properties and add identifer.

    From a list of properties name, identifies each of them with a certain
    integer, to link it to a meta property by adding an id in front of the
    property name.

    Args:
        properties (list[str]): ["CaprockPressureMax", "CaprockPressureMin"]

    Returns:
        list[tuple[str, int]]: [1:"CaprockPressureMax", 1:"CaprockPressureMin"]
    """
    idProps: list[ str ] = []
    # the order of the first element of every tuple is mandatory
    propertiesIdentifiers: list[ tuple[ str, str ] ] = [
        ( "deltapressure", "0" ),
        ( "pressure", "1" ),
        ( "temperature", "2" ),
        ( "totaldynamicporevolume", "3" ),
        ( "dynamicporevolumes", "4" ),
        ( "nontrapped", "5" ),
        ( "trapped", "6" ),
        ( "immobile", "7" ),
        ( "mobile", "8" ),
        ( "dissolved", "9" ),
        ( "meanbhp", "15" ),
        ( "meantotalmassrate", "16" ),
        ( "meantotalvolumetricrate", "17" ),
        ( "meansurfacevolumetricrate", "18" ),
        ( "totalmassrate", "12" ),
        ( "totalvolumetricrate", "13" ),
        ( "totalsurfacevolumetricrate", "13" ),
        ( "surfacevolumetricrate", "14" ),
        ( "totalfluidmass", "36" ),
        ( "cellfluidmass", "37" ),
        ( "mass", "10" ),
        ( "bhp", "11" ),
        ( "cumulatedvolumetricrate", "19" ),
        ( "cumulatedvolume", "20" ),
        ( "volumetricrate", "21" ),
        ( "volume", "22" ),
        ( "newtoniter", "23" ),
        ( "lineariter", "24" ),
        ( "stress", "25" ),
        ( "displacement", "26" ),
        ( "permeability", "27" ),
        ( "porosity", "28" ),
        ( "ratio", "29" ),
        ( "fraction", "30" ),
        ( "bulkmodulus", "31" ),
        ( "shearmodulus", "32" ),
        ( "oedometricmodulus", "33" ),
        ( "points", "34" ),
        ( "density", "35" ),
        ( "time", "38" ),
        ( "dt", "39" ),
    ]
    for prop in properties:
        identification: bool = False
        for propId in propertiesIdentifiers:
            if propId[ 0 ] in prop.lower():
                idProps.append( propId[ 1 ] + ":" + prop )
                identification = True
                break
        if not identification:
            raise ValueError( f"The property <<{prop}>> could not be identified.\n" +
                              "Check that your list of meta properties is updated." )
    return idProps


# TODO check if this function works when having more than 2 components


def extractValuesFlow( geosLogLine: str ) -> list[ float ]:
    """Extract values from a Geos log line.

    Args:
        geosLogLine (str): Geos log line
            "compflowStatistics, Reservoir: "
            "Dissolved component mass: { { 0, 0 }, { 0, -6.38235e+10 } } kg"

    Returns:
        list[float]: list of values in the line.
        [0.0, 0.0, 0.0, -6.38235e+10]
    """
    lineElements: list[ str ] = geosLogLine.split( ":" )
    valuesBlock: str = lineElements[ -1 ]
    valuesBlock = valuesBlock.replace( ",", " " )
    valuesFound: list[ float ] = extractFloatsFromString( valuesBlock )
    return valuesFound


def convertValues(
    propertyNames: list[ str ],
    propertyValues: list[ float ],
    propertiesUnit: dict[ str, Unit ],
) -> list[ float ]:
    """Convert properties to the desired units.

    Knowing two lists : 1) float numbers that are supposed to be in
    SI units ; 2) properties name linked to the float numbers.
    And that these lists are of same dimension, creates a new list of
    float values converted to a specific unit linked to the property name.

    Args:
        propertyNames (list[str]): list of property names
        propertyValues (list[float]): list of property values.
        propertiesUnit (dict[str, Unit]): dictionary of desired units for each
            property
            {"pressure": UnitPressure, ..., "propertyTypeN": UnitPropertyTypeN}

    Returns:
        list[float]: list of converted values.
    """
    assert len( propertyNames ) == len( propertyValues )
    valuesConverted: list[ float ] = []
    for index, name in enumerate( propertyNames ):
        unitObj: Unit = propertiesUnit[ "nounit" ]
        for propertyType in propertiesUnit:
            if propertyType.lower() in name.lower():
                unitObj = propertiesUnit[ propertyType ]
                break
        valueConverted: float = convert( propertyValues[ index ], unitObj )
        valuesConverted.append( valueConverted )
    return valuesConverted


def identifyCurrentWell( geosLogLine: str, lastWellName: str ) -> str:
    """Identify the current name of the well rom a Geos log line.

    Because properties values of wells can be output without specifying
    the name of the well which they belong to, we have to assume that
    the name of well for the current properties observed is either :

    - the name of the well that can be found inside the line
    - the name of the last well name found in former lines.

    Args:
        geosLogLine (str): line from Geos log file
            #expected lines with well name :
            "Rank 18: well.CO2001: BHP (at the specified reference
            elevation): 19318538.400682557 Pa"
            Or
            "wellControls1: BHP (at the specified reference
            elevation): 12337146.157562563 Pa"
            #line with no well name :
            "The total rate is 0 kg/s, which corresponds to a
            total surface volumetric rate of 0 sm3/s"
        lastWellName (str): name of the last well found

    Raises:
        ValueError: "An error has occured while parsing <<geosLogLine>>."

    Returns:
        str: "wellControls"
    """
    if ":" in geosLogLine:
        lineElements: list[ str ] = geosLogLine.split( ":" )
        if geosLogLine.startswith( "Rank" ):
            wellName: str = lineElements[ 1 ]
        else:
            wellName = lineElements[ 0 ]
    else:
        wellName = lastWellName
    wellName = wellName.lstrip().rstrip()
    return wellName


def extractPropertiesWell( geosLogLine: str, wellName: str, phaseName: str ) -> list[ str ]:
    """Extracts the well property presented from a Geos log line.

    Args:
        geosLogLine (str): "wellControls1: Phase 0 surface
            volumetric rate: 30.023748128796043 sm3/s"
        wellName (str): well1
        phaseName (str): phase1

    Returns:
        list[str]: ["Well1_SurfaceVolumetricRatePhase1"]
    """
    wName: str = formatPropertyName( wellName )
    pName: str = formatPropertyName( phaseName )
    tags_association = {
        "BHP": wName + "__BHP",
        "total massRate": wName + "__TotalMassRate",
        "total surface volumetricRate": wName + "__TotalSurfaceVolumetricRate",
        "phase surface volumetricRate": wName + "__SurfaceVolumetricRate" + pName,
        "well is shut": wName + "__IsShut",
        "density of phase": wName + "__DensityOf" + pName,
        "total fluid density": wName + "__TotalFluidDensity",
    }
    tags_found: list[ str ] = extractWellTags( geosLogLine )
    propertiesWell: list[ str ] = []
    for tag in tags_found:
        correspondingName = tags_association[ tag ]
        propertiesWell.append( correspondingName )
    return propertiesWell


def extractPhaseId( geosLogLine: str ) -> int:
    """Extracts the phase number id from a Geos log line.

    Args:
        geosLogLine (str): #expected line : "wellControls1:
            Phase 0 surface volumetric rate: 30.023748128796043 sm3/s"

    Raises:
        ValueError: "Not enough elements to unpack in line <<" + geosLogLine + ">>."
        ValueError: "An error has occured while parsing <<" + geosLogLine + ">>"

    Returns:
        int: 0
    """
    try:
        lineElements: list[ str ] = geosLogLine.lower().split()
        phaseElementIndex: int = lineElements.index( "phase" )
        if len( lineElements ) > phaseElementIndex + 1:
            return int( lineElements[ phaseElementIndex + 1 ] )
        else:
            raise ValueError( "Not enough elements to unpack in region line <<" + geosLogLine + ">>" )
    except Exception as e:
        raise ValueError( "An error has occured while parsing region line <<" + geosLogLine + ">>" ) from e


def extractWellTags( geosLogLine: str ) -> list[ str ]:
    """Extracts the list of well property tags available from a Geos log line.

    Args:
        geosLogLine (str): line from geos log file.

    Returns:
        list[str]: list of tags.
    """
    if geosLogLine.startswith( "Control switch" ):
        return []
    lower_geosLogLine = geosLogLine.lower()
    tags_found_line: list[ str ] = []
    if "well is shut" in lower_geosLogLine:
        tags_found_line.append( "well is shut" )
    elif " bhp " in lower_geosLogLine:
        tags_found_line.append( "BHP" )
    elif "total rate" in lower_geosLogLine:
        tags_found_line.append( "total massRate" )
        if "total surface volumetric rate" in lower_geosLogLine:
            tags_found_line.append( "total surface volumetricRate" )
    elif "surface volumetric rate" in lower_geosLogLine:
        tags_found_line.append( "phase surface volumetricRate" )
    elif "density of phase" in lower_geosLogLine:
        tags_found_line.append( "density of phase" )
    elif "total fluid density" in lower_geosLogLine:
        tags_found_line.append( "total fluid density" )
    return tags_found_line


def extractValuesWell( geosLogLine: str, numberProperties: int ) -> list[ float ]:
    """Extract values from Geos log line and returns them as a list of floats.

    The idea here is first to extract all floats values from the line.
    Now all of them are useful so we need to keep some of them.
    Luckily, only the last one or two floats are useful. And to determine
    that, we use the number of well properties found in the line which ranges
    from one to two.

    Args:
        geosLogLine (str): "Rank 129: well.CO2010: The density of
            phase 0 at surface conditions is 1.86 kg/sm3."
        numberProperties (int): number of well properties found in the line.

    Returns:
        list[float]: value of the property. e.g. [1.86]
    """
    try:
        if numberProperties > 0:
            valuesFound: list[ float ] = extractFloatsFromString( geosLogLine )
            if len( valuesFound ) >= numberProperties:
                usefulValues: list[ float ] = valuesFound[ -numberProperties: ]
                return usefulValues
            else:
                raise ValueError( "Number of floats found in line is inferior to number of well properties" +
                                  " in line <<" + geosLogLine + ">>." )
        else:
            raise ValueError( "No well property found in the well property line <<" + geosLogLine + ">>." )
    except Exception as e:
        raise ValueError( "Well line not corresponding to expected layering <<" + geosLogLine + ">>." ) from e


def extractValueAndNameAquifer( geosLogLine: str ) -> tuple[ str, float ]:
    """Extract value and name of the aquifer contained in a Geos log line.

    Args:
        geosLogLine (str): "FlowSolverBase compositionalMultiphaseFlow
            (SimuDeck_aquifer_pression_meme.xml, l.28): at time 100s, the
            <Aquifer> boundary condition 'aquifer1' produces a flux of
            -0.6181975187076816 kg (or moles if useMass=0)."

    Returns:
        tuple[str, float]: a tuple with the name and the float value.
        e.g. ("aquifer1", -0.6181975187076816)
    """
    try:
        lineElements: list[ str ] = geosLogLine.split()
        indexAquifName: int = lineElements.index( "produces" ) - 1
        indexValue: int = lineElements.index( "flux" ) + 2
        if 0 < indexAquifName < indexValue and indexValue < len( lineElements ):
            aquifName: str = lineElements[ indexAquifName ].replace( "'", "" )
            value: float = float( lineElements[ indexValue ] )
            return ( aquifName, value )
        else:
            raise ValueError( "Aquifer name or aquifer property value is not given in the line <<" + geosLogLine +
                              ">>." )
    except Exception as e:
        raise ValueError( "Aquifer line not corresponding to expected layering <<" + geosLogLine + ">>." ) from e


def correctZeroValuesInListOfValues( values: list[ float ] ) -> list[ float ]:
    """Replace orhphelin 0 values of input list.

    If 0 values are found in a list of values, either replace them with the
    value found before in the list or keep it 0. We suppose that 2 zeros in a
    row correspond to a continuity of the values, hence keeping it 0.

    Args:
        values (list[float]): list of ints or floats

    Returns:
        list[float]: list of ints or floats
    """
    valuesCorrected: list[ float ] = deepcopy( values )
    for i in range( 1, len( values ) - 1 ):
        valueChecked: float = values[ i ]
        if valueChecked == 0:
            valueBefore: float = values[ i - 1 ]
            valueAfter: float = values[ i + 1 ]
            if valueBefore != 0 or valueAfter != 0:
                valuesCorrected[ i ] = valueBefore
    return valuesCorrected


def extractTimeAndDt( geosLogLine: str ) -> tuple[ float, float ]:
    """From a Geos log line, extracts the float values of Time and dt.

    Args:
        geosLogLine (str): #expected lines :
            "Time: {} years, {} days, {} hrs, {} min, {} s, dt: {} s, Cycle: {}"
            "Time: {:.2f} years, dt: {} s, Cycle: {}"
            "Time: {:.2f} days, dt: {} s, Cycle: {}"
            "Time: {:.2f} hrs, dt: {} s, Cycle: {}"
            "Time: {:.2f} min, dt: {} s, Cycle: {}"
            "Time: {:4.2e} s, dt: {} s, Cycle: {}"
            "Time: {]s, dt:{}s, Cycle: {}"

    Raises:
        KeyError: "Cannot add time values for tag=<<timeFactor>>"

    Returns:
        tuple[float]: (time, dt)
    """
    timeCounter: dict[ str, float ] = { "years": 0, "days": 0, "hrs": 0, "min": 0, "s": 0 }
    timeTag: str = "Time:"
    try:
        indexDT: int = geosLogLine.index( "dt:" )
        cycleIndex: int = geosLogLine.index( "Cycle:" )
    except ValueError:
        print( "The log line does not have valid format :\n<<" + geosLogLine.rstrip() +
               ">>\nDefault value of 0.0 returned." )
        return ( 0.0, 0.0 )
    timePart: str = geosLogLine[ len( timeTag ):indexDT ]
    # timePart = " {} years, {} days, {} hrs, {} min, {} s, "
    timePart = timePart.replace( " ", "" )[ :-1 ]
    # timePart = "{}years,{}days,{}hrs,{}min,{}s"
    timeElts: list[ str ] = timePart.split( "," )
    # timeElts = ["{}years", "{}days", "{}hrs", "{}min", "{}s"]
    for elt in timeElts:
        lastDigitIndex: int = 0
        for i, caracter in enumerate( elt ):
            if caracter.isdigit():
                lastDigitIndex = i
        timeValue: float = float( elt[ :lastDigitIndex + 1 ] )
        timeFactor: str = elt[ lastDigitIndex + 1: ]
        try:
            timeCounter[ timeFactor ] += float( timeValue )
        except KeyError:
            print( f"Cannot add time values for tag=<<{timeFactor}>>" )
    totalTime: float = timeInSecond( timeCounter )

    dtPart: str = geosLogLine[ indexDT:cycleIndex ]
    # dtPart = "dt: {} s, "
    dtPart = dtPart.replace( " ", "" )[ 3:-2 ]
    # dtPart = "{}"
    dt: float = float( dtPart )
    return ( totalTime, dt )


def timeInSecond( timeCounter: dict[ str, float ] ) -> float:
    """Calculates the time in s from a dict of different time quantities.

    Args:
        timeCounter (dict[str, float]): timeCounter:
            {"years": x0, "days": x0, "hrs": x0, "min": x0, "s": x0}

    Returns:
        float: Sum in seconds of all time quantities.
    """
    yearsToSeconds: float = timeCounter[ "years" ] * 365.25 * 86400
    daysToSeconds: float = timeCounter[ "days" ] * 86400
    hrsToSeconds: float = timeCounter[ "hrs" ] * 3600
    minsToSeconds: float = timeCounter[ "min" ] * 60
    s: float = timeCounter[ "s" ]
    return yearsToSeconds + daysToSeconds + hrsToSeconds + minsToSeconds + s


def extractNewtonIter( geosLogLine: str ) -> int:
    """From a Geos log line, extracts the int value of NewtonIter.

    Args:
        geosLogLine (str): #expected line :
            "    Attempt:  0, ConfigurationIter:  0, NewtonIter:  0"

    Raises:
        ValueError: "Not enough elements to unpack in time line <<" + geosLogLine + ">>."

        ValueError: "An error has occured while parsing <<" + geosLogLine + ">>"

    Returns:
        int: NewtonIter
    """
    try:
        lineClean: str = replaceSpecialCharactersWithWhitespace( geosLogLine )
        lineElements: list[ str ] = lineClean.split()
        newtonIterIndex: int = lineElements.index( "NewtonIter" )
        if len( lineElements ) > newtonIterIndex + 1:
            newtonIter: str = lineElements[ newtonIterIndex + 1 ]
            return int( newtonIter )
        else:
            raise ValueError( "Not enough elements to unpack in line <<" + geosLogLine + ">>." )
    except Exception as e:
        raise ValueError( "An error has occured while parsing <<" + geosLogLine + ">>" ) from e


def extractLinearIter( geosLogLine: str ) -> int:
    """From a Geos log line, extracts the int value of linear iterations.

    Args:
        geosLogLine (str): #expected line :
            "    Linear Solver | Success | Iterations: 23 | Final Rel Res:
            5.96636e-05 | Make Restrictor Time: 0 | Compute Auu Time: 0 |
            SC Filter Time: 0 | Setup Time: 1.5156 s | Solve Time: 0.041093 s"

    Raises:
        ValueError: "Not enough elements to unpack in time line <<" + geosLogLine + ">>."
        ValueError: "An error has occured while parsing <<" + geosLogLine + ">>"

    Returns:
        int: 23
    """
    try:
        lineClean: str = replaceSpecialCharactersWithWhitespace( geosLogLine )
        lineElements: list[ str ] = lineClean.split()
        iterIndex: int = lineElements.index( "Iterations" )
        if len( lineElements ) > iterIndex + 1:
            linearIter: str = lineElements[ iterIndex + 1 ]
            return int( linearIter )
        else:
            raise ValueError( "Not enough elements to unpack in line <<" + geosLogLine + ">>." )
    except Exception as e:
        raise ValueError( "An error has occured while parsing <<" + geosLogLine + ">>" ) from e


"""
String treatments functions
"""


def replaceSpecialCharactersWithWhitespace( sentence: str ) -> str:
    """Replace every special characters in a string with whitespaces.

    Args:
        sentence (str): Random string "hi '(_there(''&*$^,:;'"

    Returns:
        str: "hi    there           "
    """
    cleanSentence: str = re.sub( "[^a-zA-Z0-9\n.+]", " ", sentence )
    return cleanSentence


def formatPropertyName( propertyName: str ) -> str:
    """Clean the string by replacing special characters and removing spaces.

    Args:
        propertyName (str): name;of:the property

    Returns:
        str: NameOfTheProperty
    """
    propertyClean: str = replaceSpecialCharactersWithWhitespace( propertyName )
    propertyElements: list[ str ] = propertyClean.split()
    capitalizedPropertyElements: list[ str ] = [ elt[ 0 ].upper() + elt[ 1: ] for elt in propertyElements ]
    formattedName: str = ""
    for element in capitalizedPropertyElements:
        formattedName += element
    return formattedName


def extractFloatsFromString( line: str ) -> list[ float ]:
    """Extracts a list of float numbers from a string.

    Args:
        line (str): A random string.

    Returns:
        list[float]: [float1, ..., floatN]
    """
    lineModified: str = deepcopy( line )
    replacements: list[ str ] = [ "[", "]", "{", "}" ]
    for replacement in replacements:
        lineModified = lineModified.replace( replacement, " " )
    elements: list[ str ] = lineModified.split()
    floats: list[ float ] = []
    for elt in elements:
        if isFloat( elt ):
            floats.append( float( elt ) )
    return floats


# from https://stackoverflow.com/a/20929881
def isFloat( element: Any ) -> bool:  # noqa: ANN401 # disable Any error
    """Check whether an element is float or not.

    Args:
        element (Any): input number to test.

    Returns:
        bool: True if the number is a float.
    """
    if element is None:
        return False
    try:
        float( element )
        return True
    except ValueError:
        return False


def extractListIntsFromString( string: str ) -> list[ int ]:
    """Builds a list of int numbers from a string.

    Args:
        string (str): A random string.

    Returns:
        list[int]: [int1, ..., intN]
    """
    intsFound: list[ int ] = []
    cleanString: str = replaceSpecialCharactersWithWhitespace( string )
    lineElements: list[ str ] = cleanString.split()
    for elt in lineElements:
        with contextlib.suppress( ValueError ):
            intsFound.append( int( elt ) )
    return intsFound


def extractFirstIntFromString( string: str ) -> int:
    """Extracts the first int value from a string.

    Args:
        string (str): A random string.

    Returns:
        int or None if no int was found.
    """
    cleanString: str = replaceSpecialCharactersWithWhitespace( string )
    lineElements: list[ str ] = cleanString.split()
    for elt in lineElements:
        try:
            intFound: int = int( elt )
            return intFound
        except ValueError:
            pass
    raise ValueError( "Line does not contain int value." )


def countNumberLines( filepath: str ) -> int:
    """Reads a file to find the number of lines within it.

    Args:
        filepath (str): Path to the file.

    Returns:
        int: Number of lines in file.
    """
    with open( filepath ) as file:
        numberLines = len( file.readlines() )
    return numberLines


def elementsAreInLog( filepath: str, elements: list[ str ] ) -> bool:
    """Indicates if input file contains element from input list of string.

    To do so, this reads a file and checks at every line if an
    element was found within the line. If an element is found, it is not
    checked again. The function returns True only when there is no more
    element to check.

    Args:
        filepath (str): Path to the file.
        elements (list[str]): Every string that needs to be find
            inside the file.

    Returns:
        bool:
    """
    assert len( elements ) > 0
    with open( filepath ) as file:
        for line in file:
            if len( elements ) == 0:
                return True
            for element in elements:
                if element in line:
                    indexElement: int = elements.index( element )
                    elements.pop( indexElement )
                    break
    return False


def findNumberPhasesSimulation( filepath: str ) -> int:
    """Find the number of phases from Geos log file.

    Geos logs do not have explicit message telling you how many phases
    were used to perform the simulation, unlike regions, wells etc ...
    Therefore, we need at least to identify the exact number of phases that
    can be find in this Geos log file to extract correctly properties
    regarding phase related data.

    Args:
        filepath (str): Filepath to a Geos log file.

    Returns:
        int: The number of phases found in the Geos log.
    """
    numberLines: int = countNumberLines( filepath )
    # arbitrary number of minimum lines to consider the log as readable
    assert numberLines > 50
    with open( filepath ) as geosFile:
        line: str = geosFile.readline()
        id_line: int = 1
        while not line.startswith( "Time:" ) and id_line <= numberLines:
            line = geosFile.readline()
            id_line += 1
            if line.startswith( "Adding Solver of type" ) and ( "singlephase" in line.lower() ):
                return 1
        maxPhaseIdWell: int = -1
        while id_line <= numberLines:
            line = geosFile.readline()
            id_line += 1
            if "Phase mass" in line or "Phase dynamic" in line:
                valuesFound: list[ float ] = extractValuesFlow( line )
                return len( valuesFound )
            lowLine: str = line.lower()
            phaseTags: list[ str ] = [ " phase ", " surface " ]
            if ( all( tag in lowLine for tag in phaseTags ) and "phase surface" not in lowLine ):
                phaseIdWell: int = extractPhaseId( line )
                if maxPhaseIdWell < phaseIdWell:
                    maxPhaseIdWell = phaseIdWell
                else:
                    return maxPhaseIdWell + 1
    return 0


def transformUserChoiceToListPhases( userChoice: Union[ str, None ] ) -> list[ str ]:
    """Get a list of phase name from the input string.

    When using GeosLogReader, the user can choose the names of the phases
    to use. The wished format is to specify each name in the good, separated
    by whitespaces or either commas.

    Args:
        userChoice (str | None): Output from EnterPhaseNames string vector widget.

    Returns:
        list[str]: [phase0, phase1, ..., phaseN]
    """
    if userChoice is None:
        return []
    choice: str = deepcopy( userChoice )
    # Regular expression pattern to match any symbol that is not
    # alphanumeric, comma, or whitespace
    pattern = r"[^\w ,]"
    matches = re.findall( pattern, userChoice )
    if bool( matches ):
        print( "You cannot use symbols except for commas." + " Please separate your phase names with whitespace" +
               " or with commas." )
        return []
    choiceClean: str = choice.replace( ",", " " )
    phaseNames: list[ str ] = choiceClean.split()
    return phaseNames


def phaseNamesBuilder( numberPhases: int, phasesFromUser: list[ str ] ) -> list[ str ]:
    """Build phase names.

    When creating phase names, the user can or cannot have defined his
    own phase names when reading the log. Therefore, whether phase names
    were provided or not, if we have N phases found in the log, a list of
    N phase names will be created, starting from phase0 up to phaseN.

    Args:
        numberPhases (int): Number of phases found in the log file.
        phasesFromUser (list[str]): names chosen by the user, can be more
            or less than numberPhases.

    Returns:
        list[str]: [nameFromUser0, nameFromUser1, ..., phaseN-1, phaseN]
    """
    phaseNames: list[ str ] = []
    size: int = len( phasesFromUser )
    for i in range( numberPhases ):
        if i + 1 > size:
            phaseNames.append( "phase" + str( i ) )
        else:
            phaseNames.append( phasesFromUser[ i ] )
    return phaseNames
