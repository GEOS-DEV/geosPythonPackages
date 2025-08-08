""" Bar label function copied and adapted from bar_label function from matplotlib package to handle matplotlib versions < 3.3 used in some Paraview configurations.

    Source: matplotlib/lib/matplotlib/axes/_axes.py

"""
import numpy as np
import itertools
from packaging.version import Version
import matplotlib.transforms as mtransforms
import matplotlib as mpl

# yapf: disable
if Version( mpl.__version__ ) < Version( "3.3" ):
    def _bar_label( ax, container, datavalues, labels=None, *, fmt="%g", label_type="edge", padding=0, **kwargs):
        """Bar label function copied and adapted from bar_label function from matplotlib package to handle matplotlib versions < 3.3 used in some Paraview configurations.
        Source: matplotlib/lib/matplotlib/axes/_axes.py
        """
        for key in ['horizontalalignment', 'ha', 'verticalalignment', 'va']:
            if key in kwargs:
                raise ValueError(
                    f"Passing {key!r} to bar_label() is not supported.")

        a, b = ax.yaxis.get_view_interval()
        y_inverted = a > b
        c, d = ax.xaxis.get_view_interval()
        x_inverted = c > d

        # want to know whether to put label on positive or negative direction
        # cannot use np.sign here because it will return 0 if x == 0
        def sign(x):
            return 1 if x >= 0 else -1

        bars = container.patches
        errorbar = container.errorbar
        orientation = "vertical"

        if errorbar:
            # check "ErrorbarContainer" for the definition of these elements
            lines = errorbar.lines  # attribute of "ErrorbarContainer" (tuple)
            barlinecols = lines[2]  # 0: data_line, 1: caplines, 2: barlinecols
            barlinecol = barlinecols[0]  # the "LineCollection" of error bars
            errs = barlinecol.get_segments()
        else:
            errs = []

        if labels is None:
            labels = []

        if np.iterable(padding):
            # if padding iterable, check length
            padding = np.asarray(padding)
            if len(padding) != len(bars):
                raise ValueError(
                    f"padding must be of length {len(bars)} when passed as a sequence")
        else:
            # single value, apply to all labels
            padding = [padding] * len(bars)

        for bar, err, dat, lbl, pad in itertools.zip_longest(
                bars, errs, datavalues, labels, padding
        ):
            (x0, y0), (x1, y1) = bar.get_bbox().get_points()
            xc, yc = (x0 + x1) / 2, (y0 + y1) / 2

            if orientation == "vertical":
                extrema = max(y0, y1) if dat >= 0 else min(y0, y1)
                length = abs(y0 - y1)
            else:  # horizontal
                extrema = max(x0, x1) if dat >= 0 else min(x0, x1)
                length = abs(x0 - x1)

            if err is None or np.size(err) == 0:
                endpt = extrema
            elif orientation == "vertical":
                endpt = err[:, 1].max() if dat >= 0 else err[:, 1].min()
            else:  # horizontal
                endpt = err[:, 0].max() if dat >= 0 else err[:, 0].min()

            if label_type == "center":
                value = sign(dat) * length
            else:  # edge
                value = extrema

            if label_type == "center":
                xy = (0.5, 0.5)
                kwargs["xycoords"] = (
                    lambda r, b=bar:
                        mtransforms.Bbox.intersection(
                            b.get_window_extent(r), b.get_clip_box()
                        ) or mtransforms.Bbox.null()
                )
            else:  # edge
                if orientation == "vertical":
                    xy = xc, endpt
                else:  # horizontal
                    xy = endpt, yc

            if orientation == "vertical":
                y_direction = -1 if y_inverted else 1
                xytext = 0, y_direction * sign(dat) * pad
            else:  # horizontal
                x_direction = -1 if x_inverted else 1
                xytext = x_direction * sign(dat) * pad, 0

            if label_type == "center":
                ha, va = "center", "center"
            else:  # edge
                if orientation == "vertical":
                    ha = 'center'
                    if y_inverted:
                        va = 'top' if dat > 0 else 'bottom'  # also handles NaN
                    else:
                        va = 'top' if dat < 0 else 'bottom'  # also handles NaN
                else:  # horizontal
                    if x_inverted:
                        ha = 'right' if dat > 0 else 'left'  # also handles NaN
                    else:
                        ha = 'right' if dat < 0 else 'left'  # also handles NaN
                    va = 'center'

            if lbl is None:
                lbl = fmt % (value)

            ax.annotate(lbl,
                                    xy, xytext, textcoords="offset points",
                                    ha=ha, va=va, **kwargs)
# yapf: enable
