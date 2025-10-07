Mesh Doctor
---------------

``mesh-doctor`` is a ``python`` executable that can be used through the command line to perform various checks, validations, and tiny fixes to the ``vtk`` mesh that are meant to be used in ``geos``.
``mesh-doctor`` is organized as a collection of modules with their dedicated sets of options.
The current page will introduce those modules, but the details and all the arguments can be retrieved by using the ``--help`` option for each module.

Prerequisites
^^^^^^^^^^^^^

To use mesh-doctor, you first need to have installed the ``geos-mesh`` package using the following command:

.. code-block:: bash

    python -m pip install --upgrade ./geos-mesh

Once done, you can call ``mesh-doctor`` or ``meshDoctor`` in your command line as presented in the rest of this documentation.

Modules
^^^^^^^

To list all the modules available through ``mesh-doctor``, you can simply use the ``--help`` option, which will list all available modules as well as a quick summary.

.. code-block::

      $ mesh-doctor --help
      usage: meshDoctor.py [-h] [-v] [-q] -i VTK_MESH_FILE
                      {collocatedNodes,elementVolumes,fixElementsOrderings,generateCube,generateFractures,generateGlobalIds,nonConformal,selfIntersectingElements,supportedElements}
                      ...
      Inspects meshes for GEOSX.
      positional arguments:
      {collocatedNodes,elementVolumes,fixElementsOrderings,generateCube,generateFractures,generateGlobalIds,nonConformal,selfIntersectingElements,supportedElements}
            Modules
         collocatedNodes
            Checks if nodes are collocated.
         elementVolumes
            Checks if the volumes of the elements are greater than "min".
         fixElementsOrderings
            Reorders the support nodes for the given cell types.
         generateCube
            Generate a cube and its fields.
         generateFractures
            Splits the mesh to generate the faults and fractures. [EXPERIMENTAL]
         generateGlobalIds
            Adds globals ids for points and cells.
         nonConformal
            Detects non conformal elements. [EXPERIMENTAL]
         selfIntersectingElements
            Checks if the faces of the elements are self intersecting.
         supportedElements
            Check that all the elements of the mesh are supported by GEOSX.
      options:
      -h, --help
            show this help message and exit
      -v    Use -v 'INFO', -vv for 'DEBUG'. Defaults to 'WARNING'.
      -q    Use -q to reduce the verbosity of the output.
      -i VTK_MESH_FILE, --vtk-input-file VTK_MESH_FILE
      Note that checks are dynamically loaded.
      An option may be missing because of an unloaded module.
      Increase verbosity (-v, -vv) to get full information.

Then, if you are interested in a specific module, you can ask for its documentation using the ``mesh-doctor module_name --help`` pattern.
For example

.. code-block::

      $ mesh-doctor collocatedNodes --help
      usage: meshDoctor.py collocatedNodes [-h] --tolerance TOLERANCE
      options:
      -h, --help              show this help message and exit
      --tolerance TOLERANCE   [float]: The absolute distance between two nodes for them to be considered collocated.

``mesh-doctor`` loads its module dynamically.
If a module can't be loaded, ``mesh-doctor`` will proceed and try to load other modules.
If you see a message like

.. code-block:: bash

    [1970-04-14 03:07:15,625][WARNING] Could not load module "collocatedNodes": No module named 'vtkmodules'

then most likely ``mesh-doctor`` could not load the ``collocatedNodes`` module, because the ``vtk`` python package was not found.
Thereafter, the documentation for module ``collocatedNodes`` will not be displayed.
You can solve this issue by installing the dependencies of ``mesh-doctor`` defined in its ``requirements.txt`` file (``python -m pip install -r requirements.txt``).

Here is a list and brief description of all the modules available.

``allChecks`` and ``mainChecks``
""""""""""""""""""""""""""""""""

``mesh-doctor`` modules are called ``actions`` and they can be split into 2 different categories:
``check actions`` that will give you a feedback on a .vtu mesh that you would like to use in GEOS.
``operate actions`` that will either create a new mesh or modify an existing mesh.

``allChecks`` aims at applying every single ``check`` action in one single command. The available list is of check is:
``collocatedNodes``, ``elementVolumes``, ``nonConformal``, ``selfIntersectingElements``, ``supportedElements``.

``mainChecks`` does only the fastest checks ``collocatedNodes``, ``elementVolumes`` and ``selfIntersectingElements``
that can quickly highlight some issues to deal with before investigating the other checks.

Both ``allChecks`` and ``mainChecks`` have the same keywords and can be operated in the same way. The example below shows
the case of ``allChecks``, but it can be swapped for ``mainChecks``.

.. code-block::

      $ mesh-doctor allChecks --help                                                                                
      usage: mesh-doctor allChecks [-h] [--checksToPerform checksToPerform] [--set_parameters SET_PARAMETERS]

      options:
      -h, --help            show this help message and exit
      --checksToPerform checksToPerform
                              Comma-separated list of mesh-doctor checks to perform.
                              If no input was given, all of the following checks will be executed by default: ['collocatedNodes', 'elementVolumes', 'selfIntersectingElements'].
                              The available choices for checks are ['collocatedNodes', 'elementVolumes', 'nonConformal', 'selfIntersectingElements', 'supportedElements'].
                              If you want to choose only certain of them, you can name them individually.
                              Example: --checksToPerform collocatedNodes,elementVolumes (default: )
      --setParameters setParameters
                              Comma-separated list of parameters to set for the checks (e.g., 'param_name:value'). These parameters override the defaults.
                              Default parameters are: For collocatedNodes: tolerance:0.0. For elementVolumes: minVolume:0.0.
                              For nonConformal: angleTolerance:10.0, pointTolerance:0.0, faceTolerance:0.0.
                              For selfIntersectingElements: minDistance:2.220446049250313e-16. For supportedElements: chunkSize:1, nproc:8.
                              Example: --setParameters parameter_name:10.5,other_param:25 (default: )

``collocatedNodes``
""""""""""""""""""""

Displays the neighboring nodes that are closer to each other than a prescribed threshold.
It is not uncommon to define multiple nodes for the exact same position, which will typically be an issue for ``geos`` and should be fixed.

.. code-block::

      $ mesh-doctor collocatedNodes --help
      usage: meshDoctor.py collocatedNodes [-h] --tolerance TOLERANCE
      options:
      -h, --help              show this help message and exit
      --tolerance TOLERANCE   [float]: The absolute distance between two nodes for them to be considered collocated.

``elementVolumes``
""""""""""""""""""

Computes the volumes of all the cells and displays the ones that are below a prescribed threshold.
Cells with negative volumes will typically be an issue for ``geos`` and should be fixed.

.. code-block::

      $ mesh-doctor elementVolumes --help
      usage: meshDoctor.py elementVolumes [-h] --minVolume 0.0
      options:
      -h, --help              show this help message and exit
      --minVolume 0.0         [float]: The minimum acceptable volume. Defaults to 0.0.

``fixElementsOrderings``
""""""""""""""""""""""""

It sometimes happens that an exported mesh does not abide by the ``vtk`` orderings.
The ``fixElementsOrderings`` module can rearrange the nodes of given types of elements.
This can be convenient if you cannot regenerate the mesh.

.. code-block::

      $ mesh-doctor fixElementsOrderings --help
      usage: meshDoctor.py fixElementsOrderings [-h] [--Hexahedron 1,6,5,4,7,0,2,3] [--Prism5 8,2,0,7,6,9,5,1,4,3]
                                                   [--Prism6 11,2,8,10,5,0,9,7,6,1,4,3] [--Pyramid 3,4,0,2,1]
                                                   [--Tetrahedron 2,0,3,1] [--Voxel 1,6,5,4,7,0,2,3]
                                                   [--Wedge 3,5,4,0,2,1] --output OUTPUT [--data-mode binary, ascii]
      options:
      -h, --help              show this help message and exit
      --Hexahedron 1,6,5,4,7,0,2,3
                              [list of integers]: node permutation for "Hexahedron".
      --Prism5 8,2,0,7,6,9,5,1,4,3
                              [list of integers]: node permutation for "Prism5".
      --Prism6 11,2,8,10,5,0,9,7,6,1,4,3
                              [list of integers]: node permutation for "Prism6".
      --Pyramid 3,4,0,2,1     [list of integers]: node permutation for "Pyramid".
      --Tetrahedron 2,0,3,1   [list of integers]: node permutation for "Tetrahedron".
      --Voxel 1,6,5,4,7,0,2,3 [list of integers]: node permutation for "Voxel".
      --Wedge 3,5,4,0,2,1     [list of integers]: node permutation for "Wedge".
      --output OUTPUT         [string]: The vtk output file destination.
      --data-mode binary, ascii
                              [string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.

``generateCube``
""""""""""""""""

This module conveniently generates cubic meshes in ``vtk``.
It can also generate fields with simple values.
This tool can also be useful to generate a trial mesh that will later be refined or customized.

.. code-block::

      $ mesh-doctor generateCube --help
      usage: meshDoctor.py generateCube [-h] [--x 0:1.5:3] [--y 0:5:10] [--z 0:1] [--nx 2:2] [--ny 1:1] [--nz 4]
                                          [--fields name:support:dim [name:support:dim ...]] [--cells] [--no-cells]      
                                          [--points] [--no-points] --output OUTPUT [--data-mode binary, ascii]
      options:
      -h, --help              show this help message and exit
      --x 0:1.5:3             [list of floats]: X coordinates of the points.
      --y 0:5:10              [list of floats]: Y coordinates of the points.
      --z 0:1                 [list of floats]: Z coordinates of the points.
      --nx 2:2                [list of integers]: Number of elements in the X direction.
      --ny 1:1                [list of integers]: Number of elements in the Y direction.
      --nz 4                  [list of integers]: Number of elements in the Z direction.
      --fields name:support:dim 
                              [name:support:dim ...]: Create fields on CELLS or POINTS, with given dimension (typically 1 or 3).
      --cells                 [bool]: Generate global ids for cells. Defaults to true.
      --no-cells              [bool]: Don't generate global ids for cells.
      --points                [bool]: Generate global ids for points. Defaults to true.
      --no-points             [bool]: Don't generate global ids for points.
      --output OUTPUT         [string]: The vtk output file destination.
      --data-mode binary, ascii
                              [string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.

``generateFractures``
"""""""""""""""""""""

For a conformal fracture to be defined in a mesh, ``geos`` requires the mesh to be split at the faces where the fracture gets across the mesh.
The ``generateFractures`` module will split the mesh and generate the multi-block ``vtk`` files.

.. code-block::

      $ mesh-doctor generateFractures --help
      usage: meshDoctor.py generateFractures [-h] --policy field, internal_surfaces [--name NAME] [--values VALUES] --output OUTPUT
                                               [--data-mode binary, ascii] [--fracturesOutputDir FRACTURES_OUTPUT_DIR]
      options:
      -h, --help              show this help message and exit
      --policy field, internal_surfaces
                              [string]: The criterion to define the surfaces that will be changed into fracture zones. Possible values are "field, internal_surfaces"
      --name NAME             [string]: If the "field" policy is selected, defines which field will be considered to define the fractures.
                              If the "internal_surfaces" policy is selected, defines the name of the attribute will be considered to identify the fractures.
      --values VALUES         [list of comma separated integers]: If the "field" policy is selected, which changes of the field will be considered as a fracture.
                              If the "internal_surfaces" policy is selected, list of the fracture attributes.
                              You can create multiple fractures by separating the values with ':' like shown in this example.
                              --values 10,12:13,14,16,18:22 will create 3 fractures identified respectively with the values (10,12), (13,14,16,18) and (22).
                              If no ':' is found, all values specified will be assumed to create only 1 single fracture.
      --output OUTPUT         [string]: The vtk output file destination.
      --data-mode binary, ascii
                              [string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.
      --fracturesOutputDir FRACTURES_OUTPUT_DIR
                              [string]: The output directory for the fractures meshes that will be generated from the mesh.
      --fracturesDataMode FRACTURES_DATA_MODE
                              [string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.

``generateGlobalIds``
"""""""""""""""""""""

When running ``geos`` in parallel, `global ids` can be used to refer to data across multiple ranks.
The ``generateGlobalIds`` can generate `global ids` for the imported ``vtk`` mesh.

.. code-block::

      $ mesh-doctor generateGlobalIds --help
      usage: meshDoctor.py generateGlobalIds [-h] [--cells] [--no-cells] [--points] [--no-points] --output OUTPUT
                                                [--data-mode binary, ascii]
      options:
      -h, --help              show this help message and exit
      --cells                 [bool]: Generate global ids for cells. Defaults to true.
      --no-cells              [bool]: Don't generate global ids for cells.
      --points                [bool]: Generate global ids for points. Defaults to true.
      --no-points             [bool]: Don't generate global ids for points.
      --output OUTPUT         [string]: The vtk output file destination.
      --data-mode binary, ascii
                              [string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.

``nonConformal``
""""""""""""""""

This module will detect elements which are close enough (there's a user defined threshold) but which are not in front of each other (another threshold can be defined).
`Close enough` can be defined in terms or proximity of the nodes and faces of the elements.
The angle between two faces can also be precribed.
This module can be a bit time consuming.

.. code-block::

      $ mesh-doctor nonConformal --help
      usage: meshDoctor.py nonConformal [-h] [--angleTolerance 10.0] [--pointTolerance POINT_TOLERANCE]
                                          [--faceTolerance FACE_TOLERANCE]
      options:
      -h, --help              show this help message and exit
      --angleTolerance 10.0  [float]: angle tolerance in degrees. Defaults to 10.0
      --pointTolerance POINT_TOLERANCE
                              [float]: tolerance for two points to be considered collocated.
      --faceTolerance FACE_TOLERANCE
                              [float]: tolerance for two faces to be considered "touching".

``selfIntersectingElements``
""""""""""""""""""""""""""""

Some meshes can have cells that auto-intersect.
This module will display the elements that have faces intersecting.

.. code-block::

      $ mesh-doctor selfIntersectingElements --help
      usage: meshDoctor.py selfIntersectingElements [-h] [--minDistance 2.220446049250313e-16]
      options:
      -h, --help              show this help message and exit
      --minDistance 2.220446049250313e-16
                              [float]: The tolerance in the computation. Defaults to your machine precision 2.220446049250313e-16.

``supportedElements``
"""""""""""""""""""""

``geos`` supports a specific set of elements.
Let's cite the standard elements like `tetrahedra`, `wedges`, `pyramids` or `hexahedra`.
But also prismes up to 11 faces.
``geos`` also supports the generic ``VTK_POLYHEDRON``/``42`` elements, which are converted on the fly into one of the elements just described.

The ``supportedElements`` check will validate that no unsupported element is included in the input mesh.
It will also verify that the ``VTK_POLYHEDRON`` cells can effectively get converted into a supported type of element.

.. code-block::

      $ mesh-doctor supportedElements --help
      usage: meshDoctor.py supportedElements [-h] [--chunkSize 1] [--nproc 8]
      options:
      -h, --help              show this help message and exit
      --chunkSize 1           [int]: Defaults chunk size for parallel processing to 1
      --nproc 8               [int]: Number of threads used for parallel processing. Defaults to your CPU count 8.