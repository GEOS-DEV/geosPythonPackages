from vtkmodules.numpy_interface import dataset_adapter as dsa
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkCommonCore import vtkPoints
import numpy as np
import logging

def transform_mesh( input : vtkUnstructuredGrid, logger : logging.Logger | None = None ) -> vtkUnstructuredGrid:
    """Apply a transformation to a mesh

    Args:
        input (vtk.vtkUnstructuredGrid): input mesh
        logger (logging.logger | None, optional): logger instance. Defaults to None.

    Returns:
        vtk.vtkUnstructuredGrid: transformed mesh
    """
    # Initialize the logger if it is empty
    if not logger:
        logging.basicConfig( level=logging.WARNING )
        logger = logging.getLogger( __name__ )

    translation, rotation, pts = recenter_and_rotate( dsa.numpy_support.vtk_to_numpy(input.GetPoints().GetData()), logger )

    logger.info(f"Translation {translation}")
    logger.info(f"Rotation {rotation}")

    output = vtkUnstructuredGrid()
    (vpts:= vtkPoints()).SetData( dsa.numpy_support.numpy_to_vtk(pts) )
    output.SetPoints(vpts)
    output.SetCells(input.GetCellTypesArray(), input.GetCellLocationsArray(), input.GetCells())

    return output

def local_frame(pts):
    # find 3 orthogonal vectors
    # we assume points are on a box
    # first vector is along x axis
    ori, _, _ = origin_bounding_box(pts)
    assert ((ori == np.asarray([0, 0, 0])).all())
    u = pts[1]
    v = u
    for pt in pts[2:]:# As we assume points are on a box there should be one orthogonal to u
        if (np.abs(np.dot(u, pt)) < 0.0001):
            v = pt
            break

    return (u, v, np.cross(u, v))
    
    # utils
def origin_bounding_box( pts : np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Find the bounding box of a set of points
    Args:
        pts (np.ndarray): points to find the bounding box of
    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray]: origin, min, max of the bounding box
    """

    pt0 = pts[np.argmin(pts, axis=0), :]
    pt1 = pts[np.argmax(pts, axis=0), :]

    return (pts[0], pt0, pt1)

def recenter_and_rotate(pts : np.ndarray, logger : logging.Logger) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Recenter and rotate points to align with principal axes
    
    Args:
        pts (np.ndarray): points to recenter and rotate
        logger (logging.logger, optional): logger instance.
    """

    # find bounding box
    org, vmin, vmax = origin_bounding_box(pts)
    logger.info(f"Bounding box is {org}, {vmin}, {vmax}")

    # Transformation
    translation = org
    pts -= translation

    u, v, w = local_frame(pts)
    logger.info(f"Local frame u {u}, v {v}, w {w}")

    # find rotation R = U sig V
    rotation = np.asarray([u / np.linalg.norm(u), v / np.linalg.norm(v), w / np.linalg.norm(w)],dtype=np.float64).transpose()
    logger.info(f"R {rotation}")
    logger.info(f"theta {np.acos(.5 * (np.trace(rotation) - 1)) * 180 / np.pi}")

    pts = (rotation.transpose() @ pts.transpose()).transpose()
    pts[np.abs(pts)<1e-15] = 0. # clipping points too close to zero
    logger.info(f"Un-rotated pts : {pts}")

    return translation, rotation, pts


# #TO DO : remove
# if __name__ == "__main__":
    
#     reader = vtk.vtkXMLUnstructuredGridReader()
#     reader.SetFileName("/home/jfranc/codes/python/geosPythonPackages/geos-mesh/src/geos/mesh/processing/input.vtu")
#     reader.Update()

#     # Transformation
#     output = transform_mesh(reader.GetOutput())

#     output.SetCells(VTK_HEXAHEDRON, reader.GetOutput().GetCells())
#     writer = vtk.vtkXMLUnstructuredGridWriter()
#     writer.SetFileName("./output.vtu")
#     writer.SetInputData(output)
#     writer.Update()
#     writer.Write()
