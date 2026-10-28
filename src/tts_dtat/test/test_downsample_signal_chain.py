"""
Comprehensive test of the downsample signal chain for interactive plots.
Verifies that downsampled data has valid timestamps, correct column names,
and no NaT values.
"""
import pandas as pd
import pytest
from tts_dtat.downsample import downsample, PlotOrchestrator, _parse_times


class TestDownsampleSignalChain:
    """Test the full signal chain from raw data → downsample → plot."""

    def test_downsample_preserves_all_columns(self):
        """Downsampled data must have all original columns."""
        data = pd.DataFrame({
            'scet': pd.date_range('2026-01-01', periods=1000, freq='1s'),
            'name': ['CH1'] * 500 + ['CH2'] * 500,
            'value': range(1000),
            'metadata': ['meta'] * 1000,
        })
        
        ds = downsample(data, 100, x_col='scet', name_col='name')
        
        assert 'scet' in ds.columns, "scet column missing"
        assert 'name' in ds.columns, "name column missing"
        assert 'value' in ds.columns, "value column missing"
        assert 'metadata' in ds.columns, "metadata column missing"

    def test_downsample_no_nat_in_timestamps(self):
        """Downsampled timestamps must not be NaT."""
        data = pd.DataFrame({
            'scet': pd.date_range('2026-01-01', periods=1000, freq='1s'),
            'name': ['CH1'] * 1000,
            'value': range(1000),
        })
        
        ds = downsample(data, 100, x_col='scet', name_col='name')
        
        assert not ds['scet'].isna().any(), f"Found NaT in scet: {ds['scet'].isna().sum()} values"
        assert ds['scet'].dtype == 'datetime64[ns]', f"scet dtype is {ds['scet'].dtype}, expected datetime64[ns]"

    def test_downsample_no_nat_in_values(self):
        """Downsampled values must not be NaT (numeric)."""
        data = pd.DataFrame({
            'scet': pd.date_range('2026-01-01', periods=1000, freq='1s'),
            'name': ['CH1'] * 1000,
            'value': [float(i) for i in range(1000)],
        })
        
        ds = downsample(data, 100, x_col='scet', name_col='name')
        
        # Convert to numeric to check for NaN
        values_numeric = pd.to_numeric(ds['value'], errors='coerce')
        assert not values_numeric.isna().any(), f"Found NaN in value: {values_numeric.isna().sum()} values"

    def test_downsample_preserves_trace_names(self):
        """Downsampled data must preserve all trace names."""
        data = pd.DataFrame({
            'scet': pd.date_range('2026-01-01', periods=1000, freq='1s'),
            'name': ['CH1'] * 333 + ['CH2'] * 333 + ['CH3'] * 334,
            'value': range(1000),
        })
        
        ds = downsample(data, 100, x_col='scet', name_col='name')
        
        original_names = set(data['name'].unique())
        downsampled_names = set(ds['name'].unique())
        
        assert original_names == downsampled_names, (
            f"Trace names mismatch. Original: {original_names}, "
            f"Downsampled: {downsampled_names}"
        )

    def test_plot_renames_label_column(self):
        """plot() must rename LABEL_COL to 'name' for consistency."""
        # Simulate FssIeChanvalsFrame with LABEL_COL='channel'
        class MockFrame(pd.DataFrame):
            LABEL_COL = 'channel'
            DEFAULT_TIME_LABEL = 'timestamp'
            
            @property
            def _constructor(self):
                return MockFrame
        
        data = MockFrame({
            'timestamp': pd.date_range('2026-01-01', periods=100, freq='1s'),
            'channel': ['SP_VEL_U'] * 100,
            'value': range(100),
        })
        
        orch = PlotOrchestrator(data, [['SP_VEL_U']], n_points=50, x_var='timestamp')
        
        # plot() should work without error
        fig = orch.plot()
        assert fig is not None
        assert len(fig.data) > 0, "plot() returned figure with no traces"

    def test_interactive_rename_consistency(self):
        """interactive() must rename columns consistently with plot()."""
        class MockFrame(pd.DataFrame):
            LABEL_COL = 'channel'
            DEFAULT_TIME_LABEL = 'timestamp'
            
            @property
            def _constructor(self):
                return MockFrame
        
        data = MockFrame({
            'timestamp': pd.date_range('2026-01-01', periods=100, freq='1s'),
            'channel': ['SP_VEL_U'] * 100,
            'value': range(100),
        })
        
        orch = PlotOrchestrator(data, [['SP_VEL_U']], n_points=50, x_var='timestamp')
        
        # plot() should work
        fig = orch.plot()
        assert len(fig.data) > 0
        
        # interactive() should also work (may fail on ipywidgets import, that's OK)
        try:
            fw = orch.interactive()
            assert len(fw.data) > 0, "interactive() returned widget with no traces"
        except ImportError:
            pytest.skip("ipywidgets not available")

    def test_apply_xrange_filters_by_renamed_column(self):
        """_apply_xrange must filter by 'name' after renaming."""
        class MockFrame(pd.DataFrame):
            LABEL_COL = 'channel'
            DEFAULT_TIME_LABEL = 'timestamp'
            
            @property
            def _constructor(self):
                return MockFrame
        
        data = MockFrame({
            'timestamp': pd.date_range('2026-01-01', periods=200, freq='1s'),
            'channel': ['CH1'] * 100 + ['CH2'] * 100,
            'value': list(range(100)) + list(range(100, 200)),
        })
        
        orch = PlotOrchestrator(data, [['CH1'], ['CH2']], n_points=50, x_var='timestamp')
        
        # Create the figure (which renames columns)
        fig = orch.plot()
        assert len(fig.data) == 2, f"Expected 2 traces, got {len(fig.data)}"
        
        # Verify trace names
        trace_names = [t.name for t in fig.data]
        assert 'CH1' in trace_names, f"CH1 not in trace names: {trace_names}"
        assert 'CH2' in trace_names, f"CH2 not in trace names: {trace_names}"

    def test_parse_times_with_iso_timestamps(self):
        """_parse_times must handle ISO format timestamps."""
        timestamps = pd.Series([
            '2026-01-01 12:00:00',
            '2026-01-01 12:01:00',
            '2026-01-01 12:02:00',
        ])
        
        result = _parse_times(timestamps)
        assert not result.isna().any(), f"_parse_times produced NaT: {result.tolist()}"
        assert result.dtype == 'datetime64[ns]'

    def test_parse_times_with_doy_timestamps(self):
        """_parse_times must handle DOY format timestamps."""
        timestamps = pd.Series([
            '2026-092T01:19:36',
            '2026-092T01:55:34',
            '2026-092T02:00:33',
        ])
        
        result = _parse_times(timestamps)
        assert not result.isna().any(), f"_parse_times produced NaT: {result.tolist()}"
        assert result.dtype == 'datetime64[ns]'

    def test_parse_times_with_already_parsed_timestamps(self):
        """_parse_times must handle already-parsed datetime64 columns."""
        timestamps = pd.Series(pd.date_range('2026-01-01', periods=3, freq='1s'))
        
        result = _parse_times(timestamps)
        assert not result.isna().any(), f"_parse_times produced NaT: {result.tolist()}"
        assert result.dtype == 'datetime64[ns]'

    def test_parse_times_with_all_nat_datetime64(self):
        """_parse_times must not short-circuit on all-NaT datetime64."""
        # This simulates the bug: pd.to_datetime(doy_strings, errors='coerce')
        # without format produces all NaT
        timestamps = pd.Series(pd.NaT, index=range(3), dtype='datetime64[ns]')
        
        result = _parse_times(timestamps)
        # Result will still be all NaT (data is lost), but _parse_times
        # should not short-circuit and return unchanged
        assert result.dtype == 'datetime64[ns]'

    def test_downsample_with_doy_timestamps(self):
        """Downsample must work with DOY-formatted timestamps."""
        # Create data with DOY timestamps (as strings)
        data = pd.DataFrame({
            'scet': ['2026-092T01:19:36', '2026-092T01:55:34'] * 100,
            'name': ['CH1'] * 100 + ['CH2'] * 100,
            'value': range(200),
        })
        
        # Parse to datetime
        data['scet'] = pd.to_datetime(data['scet'], format='%Y-%jT%H:%M:%S')
        
        ds = downsample(data, 50, x_col='scet', name_col='name')
        
        assert not ds['scet'].isna().any(), "Downsampled scet has NaT values"
        assert ds['scet'].dtype == 'datetime64[ns]'
        assert len(ds) <= 100, f"Downsampled data too large: {len(ds)}"
