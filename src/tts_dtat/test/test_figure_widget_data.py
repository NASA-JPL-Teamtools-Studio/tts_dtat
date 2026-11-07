"""
Test that FigureWidget created by interactive() has data in traces.
"""
import pandas as pd
import pytest
from tts_dtat.downsample import PlotOrchestrator


class TestFigureWidgetData:
    """Verify that FigureWidget traces have data."""

    def test_figure_widget_has_trace_data(self):
        """FigureWidget must have data in all traces."""
        data = pd.DataFrame({
            'scet': pd.date_range('2026-01-01', periods=1000, freq='1s'),
            'name': ['CH1'] * 500 + ['CH2'] * 500,
            'value': list(range(500)) + list(range(100, 600)),
        })
        
        orch = PlotOrchestrator(data, [['CH1'], ['CH2']], n_points=100, x_var='scet')
        
        try:
            fw = orch.interactive()
        except ImportError:
            pytest.skip("ipywidgets not available")
        
        # Check that FigureWidget has traces
        assert len(fw.data) == 2, f"Expected 2 traces, got {len(fw.data)}"
        
        # Check that each trace has data
        for i, trace in enumerate(fw.data):
            print(f"Trace {i} ({trace.name}):")
            print(f"  x length: {len(trace.x)}")
            print(f"  y length: {len(trace.y)}")
            print(f"  x type: {type(trace.x)}")
            print(f"  y type: {type(trace.y)}")
            
            assert len(trace.x) > 0, f"Trace {i} has no x data"
            assert len(trace.y) > 0, f"Trace {i} has no y data"
            assert len(trace.x) == len(trace.y), (
                f"Trace {i} has mismatched x/y: {len(trace.x)} vs {len(trace.y)}"
            )

    def test_figure_widget_trace_names(self):
        """FigureWidget traces must have correct names."""
        data = pd.DataFrame({
            'scet': pd.date_range('2026-01-01', periods=1000, freq='1s'),
            'name': ['SP_VEL_U'] * 500 + ['SP_VEL_V'] * 500,
            'value': list(range(500)) + list(range(100, 600)),
        })
        
        orch = PlotOrchestrator(data, [['SP_VEL_U'], ['SP_VEL_V']], n_points=100, x_var='scet')
        
        try:
            fw = orch.interactive()
        except ImportError:
            pytest.skip("ipywidgets not available")
        
        trace_names = [t.name for t in fw.data]
        assert 'SP_VEL_U' in trace_names, f"SP_VEL_U not in {trace_names}"
        assert 'SP_VEL_V' in trace_names, f"SP_VEL_V not in {trace_names}"

    def test_figure_widget_x_axis_type(self):
        """FigureWidget x-axis must be datetime."""
        data = pd.DataFrame({
            'scet': pd.date_range('2026-01-01', periods=1000, freq='1s'),
            'name': ['CH1'] * 1000,
            'value': range(1000),
        })
        
        orch = PlotOrchestrator(data, [['CH1']], n_points=100, x_var='scet')
        
        try:
            fw = orch.interactive()
        except ImportError:
            pytest.skip("ipywidgets not available")
        
        # Check x-axis type
        print(f"xaxis type: {fw.layout.xaxis.type}")
        # Should be 'date' for datetime data
        assert fw.layout.xaxis.type == 'date', (
            f"Expected xaxis.type='date', got '{fw.layout.xaxis.type}'"
        )

    def test_plot_vs_widget_consistency(self):
        """plot() and interactive() must have same number of traces with same data."""
        data = pd.DataFrame({
            'scet': pd.date_range('2026-01-01', periods=1000, freq='1s'),
            'name': ['CH1'] * 500 + ['CH2'] * 500,
            'value': list(range(500)) + list(range(100, 600)),
        })
        
        orch = PlotOrchestrator(data, [['CH1'], ['CH2']], n_points=100, x_var='scet')
        
        fig = orch.plot()
        
        try:
            fw = orch.interactive()
        except ImportError:
            pytest.skip("ipywidgets not available")
        
        # Both should have same number of traces
        assert len(fig.data) == len(fw.data), (
            f"plot() has {len(fig.data)} traces, interactive() has {len(fw.data)}"
        )
        
        # Traces should have same names
        fig_names = sorted([t.name for t in fig.data])
        fw_names = sorted([t.name for t in fw.data])
        assert fig_names == fw_names, f"Names mismatch: {fig_names} vs {fw_names}"
        
        # Traces should have same number of points (or close, due to downsampling)
        for fig_trace, fw_trace in zip(fig.data, fw.data):
            assert fig_trace.name == fw_trace.name
            # Allow small difference due to downsampling
            assert abs(len(fig_trace.x) - len(fw_trace.x)) <= 1, (
                f"Trace {fig_trace.name}: plot() has {len(fig_trace.x)} points, "
                f"interactive() has {len(fw_trace.x)}"
            )
