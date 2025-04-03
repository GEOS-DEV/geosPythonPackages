import argparse
from geos.pygeos_tools.input import XML
from geos.pygeos_tools.acquisition_library.Acquisition import Acquisition
from geos.pygeos_tools.solvers import ElasticSolver
from geos.pygeos_tools.output import SeismicTraceOutput
import mpi4py
mpi4py.rc.initialize = False
from mpi4py import MPI


__doc__ = """
This is an example of how to set and run your GEOS simulation when using the ElasticSolver.
The suggested example with this script could be to use a XML file with the "ElasticSEM" solver.
"""


def parse_args():
    """Get arguments

    Returns:
        argument '--xml': Input xml file for GEOSX
    """
    parser = argparse.ArgumentParser( description="Modeling acquisition example" )
    parser.add_argument( '--xml', type=str, required=True, help="Input xml file for GEOSX" )

    args, _ = parser.parse_known_args()
    return args


def main():

    if MPI.Is_initialized():
        print("MPI initialized")
    else:
        print("MPI not initialized. Initializing...")
        MPI.Init()

    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    args = parse_args()
    print( args )
    xmlfile = args.xml
    xml = XML( xmlfile )

    # Read acquisition
    if rank == 0:
        acqui = Acquisition( xml )
    else:
        acqui = None
    acqui = comm.bcast( acqui, root=0 )

    solver = ElasticSolver()

    for shot in acqui.shots:
        xmlshot = shot.xml
        rank = comm.Get_rank()

        solver.initialize( rank, xmlshot )
        solver.applyInitialConditions()

        solver.setSourceAndReceivers( shot.getSourceCoords(), shot.getReceiverCoords() )
        solver.setVtkOutputsName( directory=f"Shot{shot.id}" )
        solver.setDtFromTimeVariable( "forceDt" )  # because is defined in the XML
        solver.setMaxTime( solver.getTimeVariables()[ "maxTime" ] )

        t: float = 0.0
        cycle: int = 0

        while t < solver.maxTime:
            if rank == 0 and cycle % 100 == 0:
                print( f"time = {t:.3f}s, dt = {solver.dt:.4f}, iter = {cycle+1}" )
            solver.execute( t )
            if cycle % 100 == 0:
                solver.outputVtk( t )
            t += solver.dt
            cycle += 1

        shot.flag = "Done"
        if rank == 0:
            print( f"Shot {shot.id} done" )
            print( "Gathering and exporting seismos" )

        seismos = solver.getAllDisplacementAtReceivers()

        directory = './seismoTraces/'
        rootname = f"seismo_{shot.id}_U"

        for i, dir in enumerate( ( 'X', 'Y', 'Z' ) ):
            seismoOut = SeismicTraceOutput( seismos[ i ], format="SEP" )
            seismoOut.export( directory=directory, rootname=rootname + dir, dt=solver.dtSeismo, verbose=True )

        solver.resetWaveField()


if __name__ == "__main__":
    main()
