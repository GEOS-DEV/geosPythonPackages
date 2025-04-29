# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import numpy as np
import numpy.typing as npt
from pathlib import Path
from typing_extensions import Self

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    smdomain, smproperty, smproxy, smhint
)
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkPointSet,
    vtkUnstructuredGrid,
)

__doc__ = """
Example of a Paraview plugin that runs through time steps.

"""


@smproxy.filter( name="PVTimeStepAggregatorFilter", label="Time Step Aggregator Filter" )
@smhint.xml("""<ShowInMenu category="Filter Examples"/>""")
@smproperty.input( name="Input", port_index=0, label="Input" )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=True,
)
class PVTimeStepAggregatorFilter( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid" )
        print("__init__")

        #: all time steps from input
        self._timeSteps: npt.NDArray[ np.float64 ] = np.array( [] )
        #: displayed time step in the IHM
        self._currentTime: float = 0.0
        #: time step index of displayed time step
        self._currentTimeStepIndex: int = 0
        #: request data processing step - incremented each time RequestUpdateExtent is called
        #: start at -1 to perform initialization when filter is selected (but not applied yet)
        self._requestDataStep: int = -1

        #: saved object at each time step
        self._savedInputs: list[vtkUnstructuredGrid] = []

    def RequestUpdateExtent(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestUpdateExtent.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()
        inInfo = inInfoVec[ 0 ]
        # get displayed time step info at filter intialization only
        if self._requestDataStep == -1:
            self._timeSteps = inInfo.GetInformationObject( 0 ).Get( executive.TIME_STEPS()  # type: ignore
                                                                    )
            self._currentTime = inInfo.GetInformationObject( 0 ).Get( executive.UPDATE_TIME_STEP()  # type: ignore
                                                                      )
            self._currentTimeStepIndex = self.getTimeStepIndex( self._currentTime, self._timeSteps )

            self._savedInputs.clear()

        # update requestDataStep
        self._requestDataStep += 1
        # update time according to requestDataStep iterator
        inInfo.GetInformationObject( 0 ).Set(
            executive.UPDATE_TIME_STEP(),
            self._timeSteps[ self._requestDataStep ]  # type: ignore
        )
        outInfoVec.GetInformationObject( 0 ).Set(
            executive.UPDATE_TIME_STEP(),
            self._timeSteps[ self._requestDataStep ]  # type: ignore
        )
        # update all objects according to new time info
        self.Modified()
        return 1

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
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
        inData1 = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData1 is not None
        if outData is None or ( not outData.IsA( inData1.GetClassName() ) ):
            outData = inData1.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
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
        input: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
        outData: vtkPointSet = self.GetOutputData( outInfoVec, 0 )

        assert input is not None, "input 0 server mesh is null."
        assert outData is not None, "Output pipeline is null."

        # time controller
        executive = self.GetExecutive()
        if self._requestDataStep <= self._currentTimeStepIndex:

            # do something repeated at each time step...
            dataAtT: vtkUnstructuredGrid = vtkUnstructuredGrid()
            dataAtT.ShallowCopy(input)
            self._savedInputs.append(dataAtT)
            print(f"Input data saved at time step {self._requestDataStep}")
            # keep running through time steps
            request.Set( executive.CONTINUE_EXECUTING(), 1 )  # type: ignore
        if self._requestDataStep >= self._currentTimeStepIndex:
                # displayed time step, stop running
                request.Remove( executive.CONTINUE_EXECUTING() )  # type: ignore

                # reinitialize requestDataStep if filter is re-applied later
                self._requestDataStep = -1

                # do something to finalize process...
                outData.ShallowCopy(input)
                print("Finalization process")

        outData.Modified()
        return 1

    def getTimeStepIndex( self: Self, time: float, timeSteps: npt.NDArray[ np.float64 ] ) -> int:
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
