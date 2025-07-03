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
import importlib.util
import warnings
from math import isclose
from typing import Callable, Optional, Tuple


def computeResidual( predicted: np.ndarray, observed: np.ndarray ) -> np.ndarray:
    """
    Compute the residual vector between predicted and observed data.

    Parameters
    ----------
    predicted : np.ndarray
        Predicted data vector.
    observed : np.ndarray
        Observed data vector.

    Returns
    -------
    np.ndarray
        Residual vector (predicted - observed).
    """
    return predicted - observed


def computeL2Loss( predicted: np.ndarray, observed: np.ndarray, scale: float = 1.0 ) -> float:
    """
    Compute the L2 loss (squared L2 norm) between predicted and observed data.

    Parameters
    ----------
    predicted : np.ndarray
        Predicted data vector.
    observed : np.ndarray
        Observed data vector.
    scale : float, optional
        Scaling factor applied to the loss (default is 1.0).

    Returns
    -------
    float
        Scaled L2 loss value.
    """
    residual = computeResidual( predicted, observed )
    loss = 0.5 * np.linalg.norm( residual )**2

    return scale * loss


def gradientTest( f: Callable[ [ np.ndarray ], float ],
                  g: Callable[ [ np.ndarray ], np.ndarray ],
                  m0: np.ndarray,
                  dm: np.ndarray,
                  flag_verbose: bool = True,
                  nk: int = 25,
                  dk: float = 1.8,
                  history_filename: Optional[ str ] = None ) -> Tuple[ bool, np.ndarray, np.ndarray ]:
    r"""
    Tests that the gradient g of an objective function f satisfies the Taylor expansion:
        f(m0 + h·Δm) ≈ f(m0) + h·g(m0)ᵀ·Δm + O(h²)        
        
    Parameters
    ----------
    f : function
        Objective function of the form m->f(m).
    g : function
        Gradient function of the form m->g(m).
    m0 : :obj:`np.ndarray`
        Reference model.
    dm : :obj:`np.ndarray`
        Model perturbation.
    flag_verbose : :obj:`logical`, optional
        Print convergence report.
    nk : :obj:`int`, optional
        Number of steps (values of h).
    dk : :obj:`float`, optional
        Ratio between two consecutive steps.

    Returns
    -------
    passed : :obj:`logical`
        True if the gradient test passed, False otherwise.
    slope : :obj:`np.ndarray`
        Slope of the error curve at every step (should be 2. if the jacobian is correct).
    history: :obj:`np.ndarray`
        Full convergence history (steps and errors), useful for further display.

    """
    f0 = f( m0 )
    g0_dm = np.dot( g( m0 ), dm )

    e0 = np.zeros( nk )
    e1 = np.zeros( nk )
    h = np.zeros( nk )

    for k in range( nk ):
        if flag_verbose:
            print( f"Gradient test: Refinement {k} / {nk}", flush=True )

        h[ k ] = pow( dk, -( k + 1 ) )
        f1 = f( m0 + h[ k ] * dm )

        e0[ k ] = abs( f1 - f0 ) / abs( f0 )
        e1[ k ] = abs( f1 - f0 - h[ k ] * g0_dm ) / abs( f0 )

    if flag_verbose:
        print( "         h         h2         e0         e1", flush=True )
        for k in range( nk ):
            print( f'{h[k]:.4e} {h[k]*h[k]:.4e} {e0[k]:.4e} {e1[k]:.4e}', flush=True )

    # Keep meaningful part of the curve, and estimate its slope...
    # Should be 2 since quadratic behaviour is expected.
    ind = np.where( ( 1e-15 < e1 ) & ( e1 < 1e-2 ) )[ 0 ]
    if ind.size > 1:
        slope = np.diff( np.log( e1[ ind ] ) ) / np.diff( np.log( h[ ind ] ) )
        mean_slope = np.mean( slope )
        passed = ( isclose( mean_slope, 2.0, abs_tol=0.1 ) or np.count_nonzero( slope > 1.9 ) > 2
                   or np.all( e1 < 1e-15 ) )
    else:
        slope = np.array( [] )
        passed = False

    history = np.vstack( ( h, h * h, e0, e1 ) )

    if history_filename is not None:
        np.savetxt( history_filename, history )

    return passed, slope, history


def plotGradientTest( h: np.ndarray,
                      e1: np.ndarray,
                      save_path: Optional[ str ] = None,
                      style: Optional[ dict ] = None ) -> Optional[ "matplotlib.figure.Figure" ]:
    """
    Plot the gradient test error curve and reference trends.

    This function visualizes the convergence behavior of a gradient test by plotting
    the first-order Taylor error (e1) against the step size (h) on a log-log scale.
    It also overlays reference lines for linear and quadratic convergence trends.

    Parameters
    ----------
    h : np.ndarray
        Array of step sizes used in the gradient test.
    e1 : np.ndarray
        Array of first-order Taylor error values.
    save_path : str, optional
        If provided, the plot will be saved to this file path (e.g., "plot.png").
    style : dict, optional
        Dictionary of matplotlib style arguments (e.g., color, marker, linestyle) to customize the error curve.

    Returns
    -------
    matplotlib.figure.Figure or None
        The matplotlib Figure object if plotting is successful, otherwise None if matplotlib is not available or data is invalid.
    """

    if importlib.util.find_spec( "matplotlib" ) is None:
        warnings.warn( "matplotlib is not installed." )
        return None

    import matplotlib
    matplotlib.use( "Agg" )  # Safe for headless environments
    import matplotlib.pyplot as plt

    # Filter out invalid values
    h = np.asarray( h )
    e1 = np.asarray( e1 )
    valid = np.isfinite( h ) & np.isfinite( e1 ) & ( h > 0 ) & ( e1 > 0 )

    if not np.any( valid ):
        warnings.warn( "No valid data points for plotting." )
        return None

    h_valid = h[ valid ]
    e1_valid = e1[ valid ]

    try:
        fig, ax = plt.subplots()
    except Exception as e:
        print( f"Subplot creation failed: {e}" )
        fig = plt.figure()
        ax = fig.add_subplot( 1, 1, 1 )

    style = style or {}
    try:
        ax.loglog( h_valid, e1_valid, label="Error", **style )
        ax.loglog( h_valid, h_valid, label="Linear trend", linestyle='--' )
        ax.loglog( h_valid, np.power( h_valid, 2 ), label="Quadratic trend", linestyle=':' )
    except Exception as e:
        print( f"Plotting failed: {e}" )
        return None

    ax.grid( True )
    ax.legend()
    ax.set_title( "Gradient test" )
    ax.set_xlabel( "h" )
    ax.set_ylabel( "Error" )

    if save_path:
        try:
            fig.savefig( save_path, bbox_inches='tight' )
            print( f"Plot saved to {save_path}" )
        except Exception as e:
            print( f"Saving plot failed: {e}" )
            return None

    return fig


def plotGradientTestFromFile( filename: str,
                              column_h: int = 0,
                              column_error: int = 3,
                              **kwargs ) -> Optional[ "matplotlib.figure.Figure" ]:
    """
    Load gradient test history from a file and plot the error curve.

    This function reads a saved gradient test history file (typically generated by `gradientTest`)
    and plots the first-order Taylor error against the step size using `plotGradientTest`.

    Parameters
    ----------
    filename : str
        Path to the file containing the gradient test history (as a 2D array).
    column_h : int, optional
        Index of the column containing step sizes (default is 0).
    column_error : int, optional
        Index of the column containing first-order Taylor errors (default is 3).
    **kwargs : dict
        Additional keyword arguments passed to `plotGradientTest`, such as `style` or `save_path`.

    Returns
    -------
    matplotlib.figure.Figure or None
        The matplotlib Figure object if plotting is successful, otherwise None if matplotlib is not available.
    """
    history = np.loadtxt( filename )
    h = history[ column_h, : ]
    e1 = history[ column_error, : ]
    return plotGradientTest( h, e1, **kwargs )
