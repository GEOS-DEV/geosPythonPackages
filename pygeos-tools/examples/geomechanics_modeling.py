import argparse
from mpi4py import MPI
from geos.pygeos_tools.utilities.input import XML
from geos.pygeos_tools.utilities.solvers import GeomechanicsSolver


__doc__ = """
This is an example of how to set and run your GEOS simulation when using the GeomechanicsSolver.
The suggested example with this script could be the beam bending test case provided by GEOS:
'/path/to/your/geos/code/inputFiles/solidMechanics/beamBending_smoke.xml'.
"""


def parse_args():
    """Get arguments

    Returns:
        argument '--xml': Input xml file for GEOSX
    """
    parser = argparse.ArgumentParser( description="Geomechanics simulation example" )
    parser.add_argument( '--xml', type=str, required=True, help="Input xml file for GEOS" )

    args, _ = parser.parse_known_args()
    return args


def main():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    args = parse_args()
    xmlfile = args.xml
    xml = XML( xmlfile )

    solver = GeomechanicsSolver( "SolidMechanicsLagrangianSSLE" )
    solver.initialize( rank=rank, xml=xml )
    solver.applyInitialConditions()
    solver.setDtFromTimeVariable( "forceDt" )  # because is defined in the XML
    solver.setMaxTime( solver.getTimeVariables()[ "maxTime" ] )

    time: float = 0.0
    cycle: int = 0

    solver.outputVtk( time )
    while time < solver.maxTime:
        if rank == 0:
            if solver.dt is not None:
                print( f"time = {time:.3f}s, dt = {solver.dt:.4f}, iter = {cycle+1}" )
        solver.execute( time )
        solver.outputVtk( time )
        time += solver.dt
        cycle += 1
    solver.cleanup( time )


if __name__ == "__main__":
    main()
