Mesh Doctor
-----------

| ``mesh-doctor`` is a ``python`` executable that can be used through the command line to perform various checks, validations, and tiny fixes to the ``vtkUnstructuredGrid`` mesh that are meant to be used in ``geos``.
  ``mesh-doctor`` is organized as a collection of modules with their dedicated sets of options.
| The current page will introduce those modules, but the details and all the arguments can be retrieved by using the ``--help`` option for each module.

Prerequisites
^^^^^^^^^^^^^

To use mesh-doctor, you need to have installed the mandatory packages using the following commands (in this order):

.. code-block:: bash

    python -m pip install --upgrade ./geos-utils
    python -m pip install --upgrade ./geos-mesh
    python -m pip install --upgrade ./mesh-doctor

Once done, you can call ``mesh-doctor`` in your command line as presented in the rest of this documentation.

Modules
^^^^^^^

To list all the modules available through ``mesh-doctor``, you can simply use the ``--help`` option, which will list all available modules as well as a quick summary.

.. command-output:: mesh-doctor --help
   :shell:

Then, if you are interested in a specific module, you can ask for its documentation using the ``mesh-doctor -i random.vtu module_name --help`` pattern.
For example

.. command-output:: mesh-doctor -i random.vtu collocatedNodes --help
   :shell:

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

.. command-output:: mesh-doctor -i random.vtu allChecks --help
   :shell:

``collocatedNodes``
"""""""""""""""""""

Displays the neighboring nodes that are closer to each other than a prescribed threshold.
It is not uncommon to define multiple nodes for the exact same position, which will typically be an issue for ``geos`` and should be fixed.

.. command-output:: mesh-doctor -i random.vtu collocatedNodes --help
   :shell:

``elementVolumes``
""""""""""""""""""

Computes the volumes of all the cells and displays the ones that are below a prescribed threshold.
Cells with negative volumes will typically be an issue for ``geos`` and should be fixed.

.. command-output:: mesh-doctor -i random.vtu elementVolumes --help
   :shell:

``fixElementsOrderings``
""""""""""""""""""""""""

It sometimes happens that an exported mesh does not abide by the ``vtk`` orderings.
The ``fixElementsOrderings`` module can rearrange the nodes of given types of elements.
This can be convenient if you cannot regenerate the mesh.

.. command-output:: mesh-doctor -i random.vtu fixElementsOrderings --help
   :shell:

``generateCube``
""""""""""""""""

This module conveniently generates cubic meshes in ``vtk``.
It can also generate fields with simple values.
This tool can also be useful to generate a trial mesh that will later be refined or customized.

.. command-output:: mesh-doctor -i random.vtu generateCube --help
   :shell:

``generateFractures``
"""""""""""""""""""""

For a conformal fracture to be defined in a mesh, ``geos`` requires the mesh to be split at the faces where the fracture gets across the mesh.
The ``generateFractures`` module will split the mesh and generate the multi-block ``vtk`` files.

.. command-output:: mesh-doctor -i random.vtu generateFractures --help
   :shell:

``generateGlobalIds``
"""""""""""""""""""""

When running ``geos`` in parallel, `global ids` can be used to refer to data across multiple ranks.
The ``generateGlobalIds`` can generate `global ids` for the imported ``vtk`` mesh.

.. command-output:: mesh-doctor -i random.vtu generateGlobalIds --help
   :shell:

``nonConformal``
""""""""""""""""

This module will detect elements which are close enough (there's a user defined threshold) but which are not in front of each other (another threshold can be defined).
`Close enough` can be defined in terms or proximity of the nodes and faces of the elements.
The angle between two faces can also be precribed.
This module can be a bit time consuming.

.. command-output:: mesh-doctor -i random.vtu nonConformal --help
   :shell:

``selfIntersectingElements``
""""""""""""""""""""""""""""

Some meshes can have cells that auto-intersect.
This module will display the elements that have faces intersecting.

.. command-output:: mesh-doctor -i random.vtu selfIntersectingElements --help
   :shell:

``supportedElements``
"""""""""""""""""""""

``geos`` supports a specific set of elements.
Let's cite the standard elements like `tetrahedra`, `wedges`, `pyramids` or `hexahedra`.
But also prismes up to 11 faces.
``geos`` also supports the generic ``VTK_POLYHEDRON``/``42`` elements, which are converted on the fly into one of the elements just described.

The ``supportedElements`` check will validate that no unsupported element is included in the input mesh.
It will also verify that the ``VTK_POLYHEDRON`` cells can effectively get converted into a supported type of element.

.. command-output:: mesh-doctor -i random.vtu supportedElements --help
   :shell:


Why only use vtkUnstructuredGrid?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

| The mesh doctor is designed specifically for unstructured meshes used in GEOS.
| All input files are expected to be ``.vtu`` (VTK Unstructured Grid) format.
| What about other formats?

VTK Hierarchy
"""""""""""""

Supposedly, other grid types that are part of the following VTK hierarchy could be used::

      vtkDataObject
      └── vtkDataSet
      └── vtkCartesianGrid
            └── vtkRectilinearGrid
            └── vtkImageData
                  └── vtkStructuredPoints
                  └── vtkUniformGrid
      └── vtkPointSet
            └── vtkExplicitStructuredGrid
            └── vtkPolyData
            └── vtkStructuredGrid
            └── vtkUnstructuredGrid

And when looking at specific methods used in mesh-doctor, it could suggest that other formats could be used:

* Points access: ``mesh.GetPoints()`` - Available in all vtkPointSet subclasses ✓
* Cell iteration: ``mesh.GetNumberOfCells()``, ``mesh.GetCell()`` - Available in all vtkDataSet subclasses ✓
* Cell types: ``mesh.GetCellType()`` - Available in all vtkDataSet subclasses ✓
* Cell/Point data: ``mesh.GetCellData()``, ``mesh.GetPointData()`` - Available in all vtkDataSet subclasses ✓

VTK Filter Compatibility
""""""""""""""""""""""""

| ``vtkCellSizeFilter``, ``vtkMeshQuality``, and other VTK filters used in the actions expect ``vtkDataSet`` or its subclasses
  ``vtkUnstructuredGrid`` is compatible with all VTK filters used.
| ``vtkPolyData`` has a different data structure, not suitable for 3D volumetric meshes.

Specific Operations Require vtkUnstructuredGrid
"""""""""""""""""""""""""""""""""""""""""""""""

* ``GetCellNeighbors()`` - Only available in vtkUnstructuredGrid
* ``GetFaceStream()`` - Only available in vtkUnstructuredGrid (for polyhedron support)
* ``GetDistinctCellTypesArray()`` - Only available in vtkUnstructuredGrid