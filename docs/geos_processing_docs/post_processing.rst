Post-processing filters
^^^^^^^^^^^^^^^^^^^^^^^^^^

This module contains GEOS post-processing tools.

Geomechanics post-processing tools
=====================================

GEOS computes many outputs including flow and geomechanic properties if coupled flow geomechanics simulations were run. Users however need additional metrics to asses geomechanical stability as part of operational studies. Two filters have been developped to compute these additional metrics: `Geos Geomechanics Calculator`` and `Geos Surfacic Geomechanics`. In addition, a third filter allows to plot Mohr's circles on selected cells and time steps.

.. Note::

    Several processing filters require the definition of physical parameters. The following list is non-exhaustive.

    Default values:
    - rock cohesion: 0.0 Pa $( fractured case )
    - friction angle: 10°


geos.processing.post_processing.SurfaceGeomechanics
-------------------------------------------------------

.. automodule:: geos.processing.post_processing.SurfaceGeomechanics
    :members:
    :undoc-members:
    :show-inheritance:


geos.processing.post_processing.GeomechanicsCalculator module
--------------------------------------------------------------

.. automodule:: geos.processing.post_processing.GeomechanicsCalculator
   :members:
   :undoc-members:
   :show-inheritance:
