#################################################################################
 Driving a reservoir simulation with Pygeos
#################################################################################


**Context**

In this example, we will use pygeos to control a CompositionalMultiphaseFVM solver throughout a GEOS simulation.
The goal is to reproduce the same results as if the simulation was launched directly through the XML file.

For the rest of this example, every part highlighting Python snippets will represent what is used to control pygeos and
how it is linked to the XML file.

The example python script for this documentation is the following:

.. code-block:: console

   pygeos-tools/src/solvers_examples/reservoir_modeling.py


------------------------------------------------------------------
 XML file and initialization of Solver object
------------------------------------------------------------------


The xml input file for the test case is located at:

.. code-block:: console

   /path/to/your/GEOS/src/inputFiles/compositionalMultiphaseFlow/2ph_cap_1d_ihu.xml


After setting up the MPI communication and parsing all the args, we can set the XML object that has parsed our XML file.

.. code-block:: python

   xmlfile = args.xml
   xml = XML( xmlfile )


**Solver**

The simulation is performed using the GEOS general-purpose multiphase flow solver.
The solver can be found in the ``Solvers`` block.

.. code-block:: xml

   <Solvers gravityVector="{0.38268, 0., -0.92388}">

     <CompositionalMultiphaseFVM
       name="compflow"
       logLevel="1"
       discretization="fluidTPFA"
       targetRegions="{ Region1 }"
       temperature="297.15">

       <NonlinearSolverParameters
         newtonTol="5e-4"
         lineSearchAction="None"
         newtonMaxIter="15"/>

       <LinearSolverParameters
         directParallel="0"/>

     </CompositionalMultiphaseFVM>

   </Solvers>


The important thing to note here is the solver type ``CompositionalMultiphaseFVM``.
Because we are dealing with a flow solver, which is not coupled, we can use the ``ReservoirSolver`` class to pilot the simulation.

.. code-block:: python

   solver = ReservoirSolver( "CompositionalMultiphaseFVM" )
   solver.initialize( rank=rank, xml=xml )
   solver.applyInitialConditions()


**Events**

To trigger the timestepping of the solver and the different outputs to perform, the "Events" block is the following:

.. code-block:: xml

   <Events
     maxTime="1.0368e8">

     <PeriodicEvent
       name="outputs"
       timeFrequency="1.728e6"
       target="/Outputs/vtkOutput"/>

     <PeriodicEvent
       name="solverApplications1"
       forceDt="1.728e6"
       target="/Solvers/compflow"/>

     <PeriodicEvent
       name="restarts"
       timeFrequency="3e7"
       targetExactTimestep="0"
       target="/Outputs/restartOutput"/>

   </Events>


The first attribute to use is ``maxTime`` which will be the limit for the simulation.
The ``solverApplications1`` event targets the ``CompositionalMultiphaseFVM`` solver that we are using.
This block contains a ``forceDt`` attribute that will be used later to choose as the timestep of the simulation.

.. code-block:: python

   solver.setDtFromTimeVariable( "forceDt" )                    # solver.dt = 1.728e6
   solver.setMaxTime( solver.getTimeVariables()[ "maxTime" ] )  # solver.maxTime = 1.0368e8


The "outputs" event triggers the output of the vtk files. The attribute "timeFrequency" has the same value as "forceDt"
so we can use the same timestep for the solver and the outputs.
To start, we will set the time to 0.0 and trigger one output of the vtk files.

.. code-block:: python

   time = 0.0
   solver.outputVtk( time )


------------------------------------------------------------------
 Iterations process and simulation end
------------------------------------------------------------------

The iterative process organizes the execution of the solver at each timestep while not exceeding the maxTime of the simulation.
Once done, the simulation is ended by calling the ``cleanup`` method.

.. code-block:: python

   while time < solver.maxTime:
       solver.execute( time )
       solver.outputVtk( time )
       time += solver.dt
   solver.cleanup( time )


More complex timestepping strategies can be implemented by modifying the timestep duration and the outputs.


------------------------------------------------------------------
 How to run that script
------------------------------------------------------------------

Using the same python used to build your GEOS installation with, run this command:

.. code-block:: console

   python pygeos-tools/src/solvers_examples/reservoir_modeling.py
          --xml /path/to/your/GEOS/src/inputFiles/compositionalMultiphaseFlow/2ph_cap_1d_ihu.xml


------------------------------------------------------------------
 To go further
------------------------------------------------------------------


**Feedback on this example**

For any feedback on this example, please submit a `GitHub issue on the project's GitHub page <https://github.com/GEOS-DEV/geosPythonPackages/issues>`_.
