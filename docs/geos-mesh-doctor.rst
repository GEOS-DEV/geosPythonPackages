
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

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py --help
   :cwd: ../geos-mesh

Then, if you are interested in a specific module, you can ask for its documentation using the ``mesh-doctor module_name --help`` pattern.
For example

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py collocated_nodes --help
   :cwd: ../geos-mesh

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

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py collocated_nodes --help
   :cwd: ../geos-mesh

``element_volumes``
"""""""""""""""""""

Computes the volumes of all the cells and displays the ones that are below a prescribed threshold.
Cells with negative volumes will typically be an issue for ``geos`` and should be fixed.

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py element_volumes --help
   :cwd: ../geos-mesh

``fix_elements_orderings``
""""""""""""""""""""""""""

It sometimes happens that an exported mesh does not abide by the ``vtk`` orderings.
The ``fix_elements_orderings`` module can rearrange the nodes of given types of elements.
This can be convenient if you cannot regenerate the mesh.

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py fix_elements_orderings --help
   :cwd: ../geos-mesh

``generate_cube``
"""""""""""""""""

This module conveniently generates cubic meshes in ``vtk``.
It can also generate fields with simple values.
This tool can also be useful to generate a trial mesh that will later be refined or customized.

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py generate_cube --help
   :cwd: ../geos-mesh

``generate_fractures``
""""""""""""""""""""""

For a conformal fracture to be defined in a mesh, ``geos`` requires the mesh to be split at the faces where the fracture gets across the mesh.
The ``generate_fractures`` module will split the mesh and generate the multi-block ``vtk`` files.

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py generate_fractures --help
   :cwd: ../geos-mesh

``generate_global_ids``
"""""""""""""""""""""""

When running ``geos`` in parallel, `global ids` can be used to refer to data across multiple ranks.
The ``generate_global_ids`` can generate `global ids` for the imported ``vtk`` mesh.

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py generate_global_ids --help
   :cwd: ../geos-mesh

``non_conformal``
"""""""""""""""""

This module will detect elements which are close enough (there's a user defined threshold) but which are not in front of each other (another threshold can be defined).
`Close enough` can be defined in terms or proximity of the nodes and faces of the elements.
The angle between two faces can also be precribed.
This module can be a bit time consuming.

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py non_conformal --help
   :cwd: ../geos-mesh

``self_intersecting_elements``
""""""""""""""""""""""""""""""

Some meshes can have cells that auto-intersect.
This module will display the elements that have faces intersecting.

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py self_intersecting_elements --help
   :cwd: ../geos-mesh

``supported_elements``
""""""""""""""""""""""

``geos`` supports a specific set of elements.
Let's cite the standard elements like `tetrahedra`, `wedges`, `pyramids` or `hexahedra`.
But also prismes up to 11 faces.
``geos`` also supports the generic ``VTK_POLYHEDRON``/``42`` elements, which are converted on the fly into one of the elements just described.

The ``supported_elements`` check will validate that no unsupported element is included in the input mesh.
It will also verify that the ``VTK_POLYHEDRON`` cells can effectively get converted into a supported type of element.

.. command-output:: python src/geos/mesh/doctor/mesh-doctor.py supported_elements --help
   :cwd: ../geos-mesh



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




