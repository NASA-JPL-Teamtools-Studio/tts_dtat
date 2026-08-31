"""tts_dtat.downsample — LTTB-based downsampling for DTAT data.

Public API
----------
downsample_series(x, y, n_points)  -> (x_ds, y_ds)
    Raw LTTB primitive on numeric arrays.

downsample(df, n_points, ...)       -> pd.DataFrame
    Per-trace DTAT wrapper; operates on a long-form DataFrame.

PlotOrchestrator(data, y_vars, ...) -> orchestrator
    Holds data + config; exposes .plot() and .config().

Closes: #10 (T1), #11 (T2), #13 (T4)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


def _lttb(data: "np.ndarray", n_out: int) -> "np.ndarray":
    """Pure-NumPy Largest-Triangle-Three-Buckets (LTTB) implementation.

    Args:
        data: Shape ``(N, 2)`` array where column 0 is x and column 1 is y.
        n_out: Number of output points.  Must satisfy ``2 <= n_out < N``.

    Returns:
        Shape ``(n_out, 2)`` array — a subset of the original points.
    """
    n = len(data)
    sampled = np.empty((n_out, 2))
    sampled[0] = data[0]
    sampled[-1] = data[-1]

    every = (n - 2) / (n_out - 2)
    a = 0

    for i in range(n_out - 2):
        avg_start = int((i + 1) * every) + 1
        avg_end   = min(int((i + 2) * every) + 1, n)
        avg_x = data[avg_start:avg_end, 0].mean()
        avg_y = data[avg_start:avg_end, 1].mean()

        bkt_start = int(i * every) + 1
        bkt_end   = min(int((i + 1) * every) + 1, n)

        bx = data[bkt_start:bkt_end, 0]
        by = data[bkt_start:bkt_end, 1]
        areas = np.abs(
            data[a, 0] * (by - avg_y)
            + bx       * (avg_y - data[a, 1])
            + avg_x    * (data[a, 1] - by)
        )
        a = int(np.argmax(areas)) + bkt_start
        sampled[i + 1] = data[a]

    return sampled



# ---------------------------------------------------------------------------
# T1 — downsample_series
# ---------------------------------------------------------------------------

def downsample_series(
    x: np.ndarray,
    y: np.ndarray,
    n_points: int,
) -> Tuple[np.ndarray, np.ndarray]:
    """Downsample a single (x, y) trace to at most *n_points* using LTTB.

    Args:
        x: 1-D array of x values (numeric or already cast to float).
        y: 1-D array of y values; same length as *x*.
        n_points: Maximum number of output points.

    Returns:
        Tuple ``(x_downsampled, y_downsampled)`` as ``np.ndarray`` pairs.
        If ``len(x) <= n_points`` the arrays are returned unchanged.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) <= n_points:
        return x, y
    data = np.column_stack([x, y])
    result = _lttb(data, n_points)
    return result[:, 0], result[:, 1]


# ---------------------------------------------------------------------------
# T2 — downsample (per-trace DTAT wrapper)
# ---------------------------------------------------------------------------

def downsample(
    df: pd.DataFrame,
    n_points: int,
    x_col: str = "scet",
    y_col: str = "value",
    name_col: str = "name",
) -> pd.DataFrame:
    """Downsample a DTAT long-form DataFrame per trace using LTTB.

    Each unique value in *name_col* is downsampled independently so that
    a trace with 200 rows is never decimated because a sibling has 200 k rows.
    All columns not used in downsampling are preserved.

    Args:
        df: Long-form DataFrame with at minimum columns for *x_col*, *y_col*,
            and *name_col*.
        n_points: Maximum number of output rows **per trace**.
        x_col: Name of the time/x column (default ``"scet"``).
        y_col: Name of the value column (default ``"value"``).
        name_col: Column whose unique values identify separate traces
                  (default ``"name"``).

    Returns:
        Downsampled DataFrame with the same schema as *df*.
        Empty input returns empty output with the same columns.
    """
    if df.empty:
        return df.copy()

    pieces = []

    for _name, group in df.groupby(name_col, sort=False):
        if len(group) <= n_points:
            pieces.append(group)
            continue

        x_int = (
            pd.to_datetime(group[x_col], errors="coerce")
            .astype(np.int64)
            .astype(float)
        )
        y_vals = pd.to_numeric(group[y_col], errors="coerce").values

        x_ds, _ = downsample_series(x_int.values, y_vals, n_points)

        # Map downsampled x values back to the original row positions.
        # First-occurrence wins for duplicate timestamps.
        x_to_pos: Dict[float, int] = {}
        for pos, xv in enumerate(x_int.values):
            if xv not in x_to_pos:
                x_to_pos[xv] = pos

        positions = [x_to_pos[xv] for xv in x_ds if xv in x_to_pos]
        pieces.append(group.iloc[positions])

    if not pieces:
        return df.iloc[0:0].copy()

    return pd.concat(pieces, ignore_index=True)


# ---------------------------------------------------------------------------
# T4 — PlotOrchestrator
# ---------------------------------------------------------------------------

class PlotOrchestrator:
    """Holds a DTAT DataFrame + plot config; renders via LTTB-downsampled figures.

    Args:
        data: Long-form DTAT DataFrame (must have ``name``, ``value``, and a
              time column matching *x_var*).
        y_vars: List-of-lists specifying subplot layout, e.g.
                ``[["SPu", "SPv"], ["VBBz"]]`` — two subplots.
        n_points: Maximum points per trace passed to :func:`downsample`.
                  Default ``500``.
        x_var: Name of the x / time column. Default ``"scet"``.
        **kwargs: Additional keyword arguments forwarded to
                  :func:`tts_dtat.plot.make_stacked_graph`.

    Example::

        orch = PlotOrchestrator(df, [["SPu"], ["VBBz"]], n_points=300)
        fig = orch.plot()

        # Mutate config and re-render without re-specifying everything:
        fig2 = orch.config(n_points=100, figure_title="Zoomed").plot()
    """

    def __init__(
        self,
        data: pd.DataFrame,
        y_vars: Sequence[Sequence[str]],
        n_points: int = 500,
        x_var: str = "scet",
        **kwargs: Any,
    ) -> None:
        self._data = data
        self._y_vars = list(y_vars)
        self._n_points = n_points
        self._x_var = x_var
        self._kwargs: Dict[str, Any] = kwargs

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def config(self, **kwargs: Any) -> "PlotOrchestrator":
        """Mutate stored configuration and return *self* for chaining.

        Recognised special keys: ``data``, ``y_vars``, ``n_points``, ``x_var``.
        All other keys are forwarded to ``make_stacked_graph``.
        """
        for k, v in kwargs.items():
            if k == "data":
                self._data = v
            elif k == "y_vars":
                self._y_vars = list(v)
            elif k == "n_points":
                self._n_points = int(v)
            elif k == "x_var":
                self._x_var = v
            else:
                self._kwargs[k] = v
        return self

    def plot(self):
        """Downsample and render, returning a ``go.Figure``.

        Returns:
            ``plotly.graph_objects.Figure`` ready for display.
        """
        from tts_dtat.plot import make_stacked_graph  # avoid circular at module level

        ds = downsample(self._data, self._n_points, x_col=self._x_var)
        fig, _colors, _markers, _traces = make_stacked_graph(
            ds, self._y_vars, x_var=self._x_var, **self._kwargs
        )
        return fig

    def interactive(self):
        """Return a zoom-reactive ``go.FigureWidget`` (implemented in T5)."""
        raise NotImplementedError(
            "PlotOrchestrator.interactive() is implemented in T5 (#14)."
        )

    def __repr__(self) -> str:
        return (
            f"PlotOrchestrator("
            f"n_rows={len(self._data)}, "
            f"n_traces={sum(len(s) for s in self._y_vars)}, "
            f"n_points={self._n_points})"
        )
