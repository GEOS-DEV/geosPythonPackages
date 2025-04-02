import numpy.typing as npt
from typing_extensions import Self
from geos.pygeos_tools.output.SEPTraceOutput import SEPTraceOutput
from geos.pygeos_tools.output.SEGYTraceOutput import SEGYTraceOutput


class SeismicTraceOutput:
    """
    Generic class for seismic traces output

    Attributes
    -----------
        data : array-like
            seismic traces to export
        format : str
            Output format \
            "SEP" or "SEGY"
    """

    def __init__( self: Self, seismo: npt.NDArray, format: str, **kwargs ):
        """
        Parameters
        -----------
            seismo : array-like
                Seismic traces to export
            format : str
                Output format \
                "SEP" or "SEGY"
        """
        self.data: npt.NDArray = seismo
        self.format: str = format

    def export( self: Self, **kwargs ) -> None:
        """
        Save the seismic traces in the requested format
        """
        if self.format.lower() == "sep":
            seismoOut = SEPTraceOutput( self.data, **kwargs )
            seismoOut.export( **kwargs )

        elif self.format.lower() == "segy":
            seismoOut = SEGYTraceOutput( self.data, **kwargs )
            seismoOut.export( **kwargs )

        else:
            raise TypeError( "Unknown output format" )
