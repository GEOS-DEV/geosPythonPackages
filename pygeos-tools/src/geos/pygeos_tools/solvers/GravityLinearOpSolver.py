# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------

import numpy as np
from numpy.typing import DTypeLike
from typing import Optional, Tuple
from scipy.sparse.linalg import LinearOperator

from geos.pygeos_tools.input.Xml import XML
from geos.pygeos_tools.solvers.InversionUtils import computeResidual, computeL2Loss
from geos.pygeos_tools.solvers.GravitySolver import GravitySolver


class GravityLinearOpSolver( LinearOperator ):
    """
    A SciPy-compatible linear operator that wraps GEOS-based forward and adjoint gravity modeling.

    This class provides a bridge between GEOS's GravitySolver and SciPy's optimization and inversion
    tools by exposing the forward and adjoint operations as a LinearOperator. It supports:
    
    - Forward modeling via `_matvec`
    - Adjoint modeling via `_rmatvec`
    - Loss and gradient computation for inversion workflows

    Parameters
    ----------
    rank : int, optional
        MPI rank of the current process (default is 0).
    scaleData : float, optional
        Scaling factor applied to the forward model output (default is 1.0).
    xml : object, optional
        Parsed XML configuration for GEOS.
    nm : int
        Number of model parameters (must be > 0).
    nd : int, optional
        Number of data points. If not provided, it will be inferred on first forward call.
    dtype : np.dtype, optional
        Data type for the operator (default is np.float64).
    """

    def __init__( self,
                  rank: int = 0,
                  scaleData: float = 1.0,
                  xml: Optional[ XML ] = None,
                  nm: int = 0,
                  nd: Optional[ int ] = None,
                  dtype: DTypeLike = np.float64 ) -> None:

        if nm <= 0:
            raise ValueError( f"Invalid dimensions: nm={nm}, must be a positive integer." )

        self.rank = rank
        self.scaleData = scaleData
        self.xml = xml
        self.nm = nm
        self.nd = nd
        self.dtype = dtype
        self._shape_initialized = False
        self.solver = GravitySolver( solverType="GravityFE" )

        if self.nd is not None:
            super().__init__( dtype=self.dtype, shape=( self.nd, self.nm ) )
            self._shape_initialized = True

    def _initialize_shape( self, nd: int ) -> None:
        if not self._shape_initialized:
            super().__init__( dtype=self.dtype, shape=( nd, self.nm ) )
            self._shape_initialized = True

    def _resetSolver( self ) -> None:
        self.solver.initialize( rank=self.rank, xml=self.xml )

    def _matvec( self, x: np.ndarray ) -> np.ndarray:
        self._resetSolver()
        y = self.solver.modeling( x, scale_data=self.scaleData )
        self._initialize_shape( nd=y.size )
        return y

    def _rmatvec( self, y: np.ndarray ) -> np.ndarray:
        self._resetSolver()
        self._initialize_shape( nd=y.size )
        return self.solver.adjoint( self.nm, y )

    def getData( self, model: np.ndarray ) -> np.ndarray:
        """
        Run forward modeling on the given model.

        Parameters
        ----------
        model : np.ndarray
            Model parameters.

        Returns
        -------
        np.ndarray
            Predicted data.
        """
        return self._matvec( model )

    def getLoss( self, model: np.ndarray, dObs: np.ndarray, scale: float = 1.0 ) -> float:
        """
        Compute the L2 loss between predicted and observed data.

        Parameters
        ----------
        model : np.ndarray
            Model parameters.
        dObs : np.ndarray
            Observed data.
        scale : float, optional
            Scaling factor for the loss (default is 1.0).

        Returns
        -------
        float
            Scaled L2 loss.
        """
        dPred = self._matvec( model )
        return computeL2Loss( dPred, dObs, scale )

    def getGradient( self, model: np.ndarray, dObs: np.ndarray, scale: float = 1.0 ) -> np.ndarray:
        """
        Compute the gradient of the loss with respect to the model.

        Parameters
        ----------
        model : np.ndarray
            Model parameters.
        dObs : np.ndarray
            Observed data.
        scale : float, optional
            Scaling factor for the gradient (default is 1.0).

        Returns
        -------
        np.ndarray
            Gradient vector.
        """
        dPred = self._matvec( model )
        residue = computeResidual( dPred, dObs )
        return self._rmatvec( residue ) * scale

    def getLossAndGradient( self,
                            model: np.ndarray,
                            dObs: np.ndarray,
                            scale: float = 1.0 ) -> Tuple[ float, np.ndarray ]:
        """
        Compute both the loss and its gradient.

        Parameters
        ----------
        model : np.ndarray
            Model parameters.
        dObs : np.ndarray
            Observed data.
        scale : float, optional
            Scaling factor (default is 1.0).

        Returns
        -------
        Tuple[float, np.ndarray]
            Tuple containing the loss and the gradient.
        """
        dPred = self._matvec( model )
        residue = computeResidual( dPred, dObs )
        loss = computeL2Loss( dPred, dObs, scale )
        gradient = self._rmatvec( residue ) * scale
        return loss, gradient

    def finalize( self ) -> None:
        """
        Finalize the GEOS solver if it was initialized.
        """
        if self.solver.alreadyInitialized:
            self.solver.finalize()

    def __enter__( self ) -> "GravityLinearOpSolver":
        return self

    def __exit__( self, excType, excValue, traceback ) -> None:
        self.finalize()
