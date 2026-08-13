"""
Test that mimics the exact notebook flow for interactive plots.
"""
import pandas as pd
import pytest
from tts_dtat.downsample import PlotOrchestrator


class TestInteractiveNotebookFlow:
    """Test the exact flow from the notebook."""

    def test_ie_interactive_flow(self):
        """Mimic the IE interactive plot flow from the notebook."""
        # Create IE-like data with 'channel' and 'timestamp' columns
        ie_data = pd.DataFrame({
            'session_id': ['PBAT24583_fsw_testing/4.2'] * 1000,
            'venue': ['FSW_testing'] * 1000,
            'run_id': ['SCI_009ede_p2'] * 1000,
            'channel': ['SP_VEL_U'] * 500 + ['SP_VEL_V'] * 500,
            'timestamp': pd.date_range('2026-03-22 22:56:04', periods=1000, freq='1s'),
            'value': list(range(500)) + list(range(100, 600)),
        })
        
        # Simulate FssIeChanvalsFrame
        class IEFrame(pd.DataFrame):
            LABEL_COL = 'channel'
            DEFAULT_TIME_LABEL = 'timestamp'
            
            @property
            def _constructor(self):
                return IEFrame
        
        ie = IEFrame(ie_data)
        
        # Build y_vars like the notebook does
        IE_CHANNELS = ['SP_VEL_U', 'SP_VEL_V', 'VBB_VEL']
        ie_y_vars = [[ch] for ch in IE_CHANNELS if ch in ie['channel'].unique()]
        
        print(f"IE channels found: {ie_y_vars}")
        assert len(ie_y_vars) == 2, f"Expected 2 channels, got {len(ie_y_vars)}"
        
        # Create PlotOrchestrator like the notebook does
        orch = PlotOrchestrator(
            ie, ie_y_vars,
            n_points=500,
            x_var="timestamp",
            figure_title="IE Playback — LTTB 500 pts/trace",
        )
        
        # Test plot() first
        fig = orch.plot()
        assert fig is not None, "plot() returned None"
        assert len(fig.data) == 2, f"Expected 2 traces, got {len(fig.data)}"
        
        # Verify trace names
        trace_names = [t.name for t in fig.data]
        print(f"Trace names: {trace_names}")
        assert 'SP_VEL_U' in trace_names
        assert 'SP_VEL_V' in trace_names
        
        # Verify traces have data
        for trace in fig.data:
            assert len(trace.x) > 0, f"Trace '{trace.name}' has no x data"
            assert len(trace.y) > 0, f"Trace '{trace.name}' has no y data"
            assert len(trace.x) == len(trace.y), (
                f"Trace '{trace.name}' has mismatched x/y lengths: "
                f"{len(trace.x)} vs {len(trace.y)}"
            )
            print(f"  {trace.name}: {len(trace.x)} points")
        
        # Test interactive() 
        try:
            fw = orch.interactive()
            assert fw is not None, "interactive() returned None"
            assert len(fw.data) == 2, f"Expected 2 traces in widget, got {len(fw.data)}"
            
            # Verify widget traces have data
            for trace in fw.data:
                assert len(trace.x) > 0, f"Widget trace '{trace.name}' has no x data"
                assert len(trace.y) > 0, f"Widget trace '{trace.name}' has no y data"
                print(f"  Widget {trace.name}: {len(trace.x)} points")
        except ImportError:
            pytest.skip("ipywidgets not available")

    def test_fcpu_interactive_flow(self):
        """Mimic the FCPU interactive plot flow from the notebook."""
        # Create FCPU-like data with 'channel_name' and 'scet' columns
        fcpu_data = pd.DataFrame({
            'session_id': ['PBAT24583/4.4'] * 1000,
            'venue': ['FSW_testing'] * 1000,
            'scet': pd.date_range('2026-04-02 01:19:36', periods=1000, freq='1s'),
            'channel_name': ['BATTERY_OUTPUT_VOLTAGE_TLM'] * 500 + ['BATTERY_CURRENT_TLM'] * 500,
            'value': list(range(500)) + list(range(100, 600)),
        })
        
        # Simulate FssFcpuChannelFrame
        class FCPUFrame(pd.DataFrame):
            LABEL_COL = 'channel_name'
            DEFAULT_TIME_LABEL = 'scet'
            
            @property
            def _constructor(self):
                return FCPUFrame
        
        fcpu = FCPUFrame(fcpu_data)
        
        # Build y_vars like the notebook does
        FCPU_CHANNELS = ['BATTERY_OUTPUT_VOLTAGE_TLM', 'BATTERY_CURRENT_TLM']
        fcpu_y_vars = [[ch] for ch in FCPU_CHANNELS if ch in fcpu['channel_name'].unique()]
        
        print(f"FCPU channels found: {fcpu_y_vars}")
        assert len(fcpu_y_vars) == 2, f"Expected 2 channels, got {len(fcpu_y_vars)}"
        
        # Create PlotOrchestrator like the notebook does
        orch = PlotOrchestrator(
            fcpu, fcpu_y_vars,
            n_points=500,
            x_var="scet",
            figure_title="FCPU Channel Values",
        )
        
        # Test plot() first
        fig = orch.plot()
        assert fig is not None, "plot() returned None"
        assert len(fig.data) == 2, f"Expected 2 traces, got {len(fig.data)}"
        
        # Verify trace names
        trace_names = [t.name for t in fig.data]
        print(f"Trace names: {trace_names}")
        assert 'BATTERY_OUTPUT_VOLTAGE_TLM' in trace_names
        assert 'BATTERY_CURRENT_TLM' in trace_names
        
        # Verify traces have data
        for trace in fig.data:
            assert len(trace.x) > 0, f"Trace '{trace.name}' has no x data"
            assert len(trace.y) > 0, f"Trace '{trace.name}' has no y data"
            print(f"  {trace.name}: {len(trace.x)} points")
        
        # Test interactive()
        try:
            fw = orch.interactive()
            assert fw is not None, "interactive() returned None"
            assert len(fw.data) == 2, f"Expected 2 traces in widget, got {len(fw.data)}"
            
            # Verify widget traces have data
            for trace in fw.data:
                assert len(trace.x) > 0, f"Widget trace '{trace.name}' has no x data"
                assert len(trace.y) > 0, f"Widget trace '{trace.name}' has no y data"
                print(f"  Widget {trace.name}: {len(trace.x)} points")
        except ImportError:
            pytest.skip("ipywidgets not available")
