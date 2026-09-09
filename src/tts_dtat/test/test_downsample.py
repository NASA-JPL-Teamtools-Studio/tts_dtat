"""Tests for tts_dtat.downsample — covers T1, T2, T3, T4."""

import numpy as np
import pandas as pd
import pytest
import plotly.graph_objects as go

from tts_dtat.downsample import downsample_series, downsample, PlotOrchestrator
from tts_dtat import plot


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def large_series():
    """1000-point synthetic sine wave."""
    x = np.linspace(0, 10, 1000)
    y = np.sin(x)
    return x, y


@pytest.fixture
def dtat_df():
    """Long-form DTAT DataFrame with two traces of different sizes."""
    n_big = 1000
    n_small = 50
    times_big = pd.date_range("2026-01-01", periods=n_big, freq="1s")
    times_small = pd.date_range("2026-01-01", periods=n_small, freq="20s")

    big = pd.DataFrame({
        "scet": times_big,
        "name": "SPu",
        "value": np.sin(np.linspace(0, 10, n_big)),
    })
    small = pd.DataFrame({
        "scet": times_small,
        "name": "VBBz",
        "value": np.cos(np.linspace(0, 10, n_small)),
    })
    return pd.concat([big, small], ignore_index=True)


@pytest.fixture
def orchestrator_df():
    """Minimal DTAT DataFrame suitable for PlotOrchestrator."""
    n = 600
    times = pd.date_range("2026-01-01", periods=n, freq="1s")
    a = pd.DataFrame({"scet": times, "name": "A", "value": np.sin(np.linspace(0, 6, n))})
    b = pd.DataFrame({"scet": times, "name": "B", "value": np.cos(np.linspace(0, 6, n))})
    return pd.concat([a, b], ignore_index=True)


# ---------------------------------------------------------------------------
# T1 — downsample_series
# ---------------------------------------------------------------------------

class TestDownsampleSeries:
    def test_output_length_at_most_n_points(self, large_series):
        x, y = large_series
        x_ds, y_ds = downsample_series(x, y, 100)
        assert len(x_ds) <= 100
        assert len(y_ds) <= 100

    def test_output_lengths_match(self, large_series):
        x, y = large_series
        x_ds, y_ds = downsample_series(x, y, 200)
        assert len(x_ds) == len(y_ds)

    def test_passthrough_when_input_small(self):
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        x_ds, y_ds = downsample_series(x, y, 10)
        np.testing.assert_array_equal(x_ds, x)
        np.testing.assert_array_equal(y_ds, y)

    def test_returns_numpy_arrays(self, large_series):
        x, y = large_series
        x_ds, y_ds = downsample_series(x, y, 50)
        assert isinstance(x_ds, np.ndarray)
        assert isinstance(y_ds, np.ndarray)

    def test_first_and_last_preserved(self, large_series):
        """LTTB always preserves first and last data points."""
        x, y = large_series
        x_ds, y_ds = downsample_series(x, y, 50)
        assert x_ds[0] == pytest.approx(x[0])
        assert x_ds[-1] == pytest.approx(x[-1])


# ---------------------------------------------------------------------------
# T2 — downsample (per-trace wrapper)
# ---------------------------------------------------------------------------

class TestDownsample:
    def test_big_trace_is_downsampled(self, dtat_df):
        ds = downsample(dtat_df, n_points=100)
        big_rows = ds[ds["name"] == "SPu"]
        assert len(big_rows) <= 100

    def test_small_trace_not_decimated(self, dtat_df):
        """VBBz has 50 rows; with n_points=100 it should be untouched."""
        ds = downsample(dtat_df, n_points=100)
        small_rows = ds[ds["name"] == "VBBz"]
        assert len(small_rows) == 50

    def test_per_trace_independence(self, dtat_df):
        """Big trace being downsampled must not affect the small trace count."""
        ds = downsample(dtat_df, n_points=100)
        assert len(ds[ds["name"] == "VBBz"]) == 50
        assert len(ds[ds["name"] == "SPu"]) <= 100

    def test_schema_preserved(self, dtat_df):
        ds = downsample(dtat_df, n_points=100)
        assert set(ds.columns) == set(dtat_df.columns)

    def test_empty_dataframe(self):
        empty = pd.DataFrame(columns=["scet", "name", "value"])
        result = downsample(empty, n_points=100)
        assert result.empty
        assert list(result.columns) == ["scet", "name", "value"]

    def test_two_traces_both_present(self, dtat_df):
        ds = downsample(dtat_df, n_points=100)
        assert set(ds["name"].unique()) == {"SPu", "VBBz"}


# ---------------------------------------------------------------------------
# T3 — max_points on make_stacked_graph
# ---------------------------------------------------------------------------

class TestMaxPoints:
    def test_no_downsampling_by_default(self, dtat_df):
        """Without max_points, all rows flow through."""
        fig, _, _, _ = plot.make_stacked_graph(
            data=dtat_df,
            y_vars=[["SPu"], ["VBBz"]],
            x_var="scet",
        )
        assert isinstance(fig, go.Figure)
        spu_trace = next(t for t in fig.data if t.name == "SPu")
        assert len(spu_trace.x) == 1000

    def test_max_points_limits_trace_length(self, dtat_df):
        fig, _, _, _ = plot.make_stacked_graph(
            data=dtat_df,
            y_vars=[["SPu"], ["VBBz"]],
            x_var="scet",
            max_points=50,
        )
        spu_trace = next(t for t in fig.data if t.name == "SPu")
        assert len(spu_trace.x) <= 50

    def test_existing_tests_unaffected(self, orchestrator_df):
        """max_points=None must not break normal callers."""
        fig, colors, markers, traces = plot.make_stacked_graph(
            data=orchestrator_df,
            y_vars=[["A"], ["B"]],
            x_var="scet",
        )
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 2


# ---------------------------------------------------------------------------
# T4 — PlotOrchestrator
# ---------------------------------------------------------------------------

class TestPlotOrchestrator:
    def test_plot_returns_figure(self, orchestrator_df):
        orch = PlotOrchestrator(orchestrator_df, [["A"], ["B"]], n_points=100)
        fig = orch.plot()
        assert isinstance(fig, go.Figure)

    def test_trace_count_matches_y_vars(self, orchestrator_df):
        orch = PlotOrchestrator(orchestrator_df, [["A"], ["B"]], n_points=100)
        fig = orch.plot()
        assert len(fig.data) == 2

    def test_trace_points_at_most_n_points(self, orchestrator_df):
        orch = PlotOrchestrator(orchestrator_df, [["A"], ["B"]], n_points=50)
        fig = orch.plot()
        for trace in fig.data:
            assert len(trace.x) <= 50

    def test_config_mutates_n_points(self, orchestrator_df):
        orch = PlotOrchestrator(orchestrator_df, [["A"], ["B"]], n_points=500)
        orch.config(n_points=30)
        assert orch._n_points == 30

    def test_config_returns_self_for_chaining(self, orchestrator_df):
        orch = PlotOrchestrator(orchestrator_df, [["A"], ["B"]])
        result = orch.config(n_points=200)
        assert result is orch

    def test_chained_config_and_plot(self, orchestrator_df):
        orch = PlotOrchestrator(orchestrator_df, [["A"], ["B"]], n_points=500)
        fig = orch.config(n_points=25).plot()
        for trace in fig.data:
            assert len(trace.x) <= 25

    def test_config_y_vars(self, orchestrator_df):
        orch = PlotOrchestrator(orchestrator_df, [["A", "B"]], n_points=100)
        orch.config(y_vars=[["A"], ["B"]])
        fig = orch.plot()
        assert len(fig.data) == 2

    def test_interactive_raises_not_implemented(self, orchestrator_df):
        orch = PlotOrchestrator(orchestrator_df, [["A"]])
        with pytest.raises(NotImplementedError):
            orch.interactive()

    def test_repr(self, orchestrator_df):
        orch = PlotOrchestrator(orchestrator_df, [["A"], ["B"]], n_points=200)
        r = repr(orch)
        assert "PlotOrchestrator" in r
        assert "200" in r
