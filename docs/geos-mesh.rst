
GEOS Mesh Tools
====================


Mesh Doctor
---------------

``mesh-doctor`` is a ``python`` executable that can be used through the command line to perform various checks, validations, and tiny fixes to the ``vtk`` mesh that are meant to be used in ``geos``.
``mesh-doctor`` is organized as a collection of modules with their dedicated sets of options.
The current page will introduce those modules, but the details and all the arguments can be retrieved by using the ``--help`` option for each module.

Modules
^^^^^^^

To list all the modules available through ``mesh-doctor``, you can simply use the ``--help`` option, which will list all available modules as well as a quick summary.

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py --help
      usage: mesh_doctor.py [-h] [-v] [-q] -i VTK_MESH_FILE
                      {collocated_nodes,element_volumes,fix_elements_orderings,generate_cube,generate_fractures,generate_global_ids,non_conformal,self_intersecting_elements,supported_elements}
                      ...

      Inspects meshes for GEOSX.

      positional arguments:
      {collocated_nodes,element_volumes,fix_elements_orderings,generate_cube,generate_fractures,generate_global_ids,non_conformal,self_intersecting_elements,supported_elements}
            Modules
         collocated_nodes
            Checks if nodes are collocated.
         element_volumes
            Checks if the volumes of the elements are greater than "min".
         fix_elements_orderings
            Reorders the support nodes for the given cell types.
         generate_cube
            Generate a cube and its fields.
         generate_fractures
            Splits the mesh to generate the faults and fractures. [EXPERIMENTAL]
         generate_global_ids
            Adds globals ids for points and cells.
         non_conformal
            Detects non conformal elements. [EXPERIMENTAL]
         self_intersecting_elements
            Checks if the faces of the elements are self intersecting.
         supported_elements
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

      $ python src/geos/mesh/doctor/mesh_doctor.py collocated_nodes --help
      usage: mesh_doctor.py collocated_nodes [-h] --tolerance TOLERANCE

      options:
      -h, --help              show this help message and exit
      --tolerance TOLERANCE   [float]: The absolute distance between two nodes for them to be considered collocated.

``mesh-doctor`` loads its module dynamically.
If a module can't be loaded, ``mesh-doctor`` will proceed and try to load other modules.
If you see a message like

.. code-block:: bash

    [1970-04-14 03:07:15,625][WARNING] Could not load module "collocated_nodes": No module named 'vtkmodules'

then most likely ``mesh-doctor`` could not load the ``collocated_nodes`` module, because the ``vtk`` python package was not found.
Thereafter, the documentation for module ``collocated_nodes`` will not be displayed.
You can solve this issue by installing the dependencies of ``mesh-doctor`` defined in its ``requirements.txt`` file (``python -m pip install -r requirements.txt``).

Here is a list and brief description of all the modules available.

``collocated_nodes``
""""""""""""""""""""

Displays the neighboring nodes that are closer to each other than a prescribed threshold.
It is not uncommon to define multiple nodes for the exact same position, which will typically be an issue for ``geos`` and should be fixed.

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py collocated_nodes --help
      usage: mesh_doctor.py collocated_nodes [-h] --tolerance TOLERANCE

      options:
      -h, --help              show this help message and exit
      --tolerance TOLERANCE   [float]: The absolute distance between two nodes for them to be considered collocated.

``element_volumes``
"""""""""""""""""""

Computes the volumes of all the cells and displays the ones that are below a prescribed threshold.
Cells with negative volumes will typically be an issue for ``geos`` and should be fixed.

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py element_volumes --help
      usage: mesh_doctor.py element_volumes [-h] --min 0.0

      options:
      -h, --help              show this help message and exit
      --min 0.0               [float]: The minimum acceptable volume. Defaults to 0.0.

``fix_elements_orderings``
""""""""""""""""""""""""""

It sometimes happens that an exported mesh does not abide by the ``vtk`` orderings.
The ``fix_elements_orderings`` module can rearrange the nodes of given types of elements.
This can be convenient if you cannot regenerate the mesh.

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py fix_elements_orderings --help
      usage: mesh_doctor.py fix_elements_orderings [-h] [--Tetrahedron 2,0,3,1] [--Pyramid 3,4,0,2,1] [--Wedge 3,5,4,0,2,1]
                                                   [--Hexahedron 1,6,5,4,7,0,2,3] [--Prism5 8,2,0,7,6,9,5,1,4,3] [--Prism6 11,2,8,10,5,0,9,7,6,1,4,3]
                                                   --volume_to_reorder all,positive,negative --output OUTPUT [--data-mode binary, ascii]

      options:
      -h, --help                  show this help message and exit
      --Tetrahedron 2,0,3,1       [list of integers]: node permutation for "Tetrahedron".
      --Pyramid 3,4,0,2,1         [list of integers]: node permutation for "Pyramid".
      --Wedge 3,5,4,0,2,1         [list of integers]: node permutation for "Wedge".
      --Hexahedron 1,6,5,4,7,0,2,3
                                  [list of integers]: node permutation for "Hexahedron".
      --Prism5 8,2,0,7,6,9,5,1,4,3
                                  [list of integers]: node permutation for "Prism5".
      --Prism6 11,2,8,10,5,0,9,7,6,1,4,3
                                  [list of integers]: node permutation for "Prism6".
      --volume_to_reorder all,positive,negative
                                  [str]: Select which element volume is invalid and needs reordering. 'all' will allow reordering of nodes for every element, regarding of their volume.
                                  'positive' or 'negative' will only reorder the element with the corresponding volume.
      --output OUTPUT             [string]: The vtk output file destination.
      --data-mode binary, ascii   [string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.

For example, assume that you have a mesh that contains 3 different cell types like Hexahedrons, Pyramids and Tetrahedrons.
After checking ``element_volumes``, you found that all your Hexahedrons and half of your Tetrahedrons have a negative volume.
To correct that, assuming you know the correct node ordering to correct these volumes, you can use this command:

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py -i /path/to/your/mesh/file fix_elements_orderings --Hexahedron 1,6,5,4,7,0,2,3
      --Tetrahedron 2,0,3,1 --volume_to_reorder negative --output /new/path/for/your/new/mesh/reordered/file --data-mode binary

``generate_cube``
"""""""""""""""""

This module conveniently generates cubic meshes in ``vtk``.
It can also generate fields with simple values.
This tool can also be useful to generate a trial mesh that will later be refined or customized.

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py generate_cube --help
      usage: mesh_doctor.py generate_cube [-h] [--x 0:1.5:3] [--y 0:5:10] [--z 0:1] [--nx 2:2] [--ny 1:1] [--nz 4]
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

``generate_fractures``
""""""""""""""""""""""

For a conformal fracture to be defined in a mesh, ``geos`` requires the mesh to be split at the faces where the fracture gets across the mesh.
The ``generate_fractures`` module will split the mesh and generate the multi-block ``vtk`` files.

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py generate_fractures --help
      usage: mesh_doctor.py generate_fractures [-h] --policy field, internal_surfaces [--name NAME] [--values VALUES]
                                             --output OUTPUT [--data-mode binary, ascii] --fracture-output
                                             FRACTURE_OUTPUT [--fracture-data-mode binary, ascii]

      options:
      -h, --help              show this help message and exit
      --policy field, internal_surfaces
                              [string]: The criterion to define the surfaces that will be changed into fracture zones.
                              Possible values are "field, internal_surfaces"
      --name NAME             [string]: If the "field" policy is selected, defines which field will be considered to
                              define the fractures. If the "internal_surfaces" policy is selected, defines the name of
                              the attribute will be considered to identify the fractures.
      --values VALUES         [list of comma separated integers]: If the "field" policy is selected, which changes of    
                              the field will be considered as a fracture. If the "internal_surfaces" policy is
                              selected, list of the fracture attributes.
      --output OUTPUT         [string]: The vtk output file destination.
      --data-mode binary, ascii
                              [string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.
      --fracture-output FRACTURE_OUTPUT
                              [string]: The vtk output file destination.
      --fracture-data-mode binary, ascii
                              [string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.

``generate_global_ids``
"""""""""""""""""""""""

When running ``geos`` in parallel, `global ids` can be used to refer to data across multiple ranks.
The ``generate_global_ids`` can generate `global ids` for the imported ``vtk`` mesh.

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py generate_global_ids --help
      usage: mesh_doctor.py generate_global_ids [-h] [--cells] [--no-cells] [--points] [--no-points] --output OUTPUT
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

``non_conformal``
"""""""""""""""""

This module will detect elements which are close enough (there's a user defined threshold) but which are not in front of each other (another threshold can be defined).
`Close enough` can be defined in terms or proximity of the nodes and faces of the elements.
The angle between two faces can also be precribed.
This module can be a bit time consuming.

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py non_conformal --help
      usage: mesh_doctor.py non_conformal [-h] [--angle_tolerance 10.0] [--point_tolerance POINT_TOLERANCE]
                                          [--face_tolerance FACE_TOLERANCE]

      options:
      -h, --help              show this help message and exit
      --angle_tolerance 10.0  [float]: angle tolerance in degrees. Defaults to 10.0
      --point_tolerance POINT_TOLERANCE
                              [float]: tolerance for two points to be considered collocated.
      --face_tolerance FACE_TOLERANCE
                              [float]: tolerance for two faces to be considered "touching".

``self_intersecting_elements``
""""""""""""""""""""""""""""""

Some meshes can have cells that auto-intersect.
This module will display the elements that have faces intersecting.

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py self_intersecting_elements --help
      usage: mesh_doctor.py self_intersecting_elements [-h] [--min 2.220446049250313e-16]

      options:
      -h, --help              show this help message and exit
      --min 2.220446049250313e-16
                              [float]: The tolerance in the computation. Defaults to your machine precision 2.220446049250313e-16.

``supported_elements``
""""""""""""""""""""""

``geos`` supports a specific set of elements.
Let's cite the standard elements like `tetrahedra`, `wedges`, `pyramids` or `hexahedra`.
But also prismes up to 11 faces.
``geos`` also supports the generic ``VTK_POLYHEDRON``/``42`` elements, which are converted on the fly into one of the elements just described.

The ``supported_elements`` check will validate that no unsupported element is included in the input mesh.
It will also verify that the ``VTK_POLYHEDRON`` cells can effectively get converted into a supported type of element.

.. code-block::

      $ python src/geos/mesh/doctor/mesh_doctor.py supported_elements --help
      usage: mesh_doctor.py supported_elements [-h] [--chunck_size 1] [--nproc 8]

      options:
      -h, --help              show this help message and exit
      --chunck_size 1         [int]: Defaults chunk size for parallel processing to 1
      --nproc 8               [int]: Number of threads used for parallel processing. Defaults to your CPU count 8.



Mesh Conversion
--------------------------

The `geos-mesh` python package includes tools for converting meshes from common formats (abaqus, etc.) to those that can be read by GEOS (gmsh, vtk).
See :ref:`PythonToolsSetup` for details on setup instructions, and `External Mesh Guidelines <https://geosx-geosx.readthedocs-hosted.com/en/latest/coreComponents/mesh/docs/Mesh.html#using-an-external-mesh>`_ for a detailed description of how to use external meshes in GEOS.
The available console scripts for this package and its API are described below.


convert_abaqus
^^^^^^^^^^^^^^

Compile an xml file with advanced features into a single file that can be read by GEOS.

.. argparse::
   :module: geos.mesh.conversion.main
   :func: build_abaqus_converter_input_parser
   :prog: convert_abaqus


.. note::
    For vtk format meshes, the user also needs to determine the region ID numbers and names of nodesets to import into GEOS.
    The following shows how these could look in an input XML file for a mesh with three regions (*REGIONA*, *REGIONB*, and *REGIONC*) and six nodesets (*xneg*, *xpos*, *yneg*, *ypos*, *zneg*, and *zpos*):


.. code-block:: xml

    <Problem>
      <Mesh>
        <VTKMesh
          name="external_mesh"
          file="mesh.vtu"
          regionAttribute="REGIONA-REGIONB-REGIONC"
          nodesetNames="{ xneg, xpos, yneg, ypos, zneg, zpos }"/>
      </Mesh>

      <ElementRegions>
        <CellElementRegion
          name="ALL"
          cellBlocks="{ 0_tetrahedra, 1_tetrahedra, 2_tetrahedra }"
          materialList="{ water, porousRock }"
          meshBody="external_mesh"/>
      </ElementRegions>
    </Problem>


API
^^^

.. automodule:: geos.mesh.conversion.abaqus_converter
    :members: