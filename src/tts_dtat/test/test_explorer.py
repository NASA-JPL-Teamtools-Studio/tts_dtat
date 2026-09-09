"""Tests for tts_dtat.explorer — ChannelExplorer widget (T6, T7, T8)."""

import pandas as pd
import pytest

from tts_dtat.explorer import ChannelExplorer, _parse_channel_dict


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class _MockEntry:
    """Minimal SemanticDictionary-style entry with a .name attribute."""
    def __init__(self, name: str) -> None:
        self.name = name


def _empty_df() -> pd.DataFrame:
    return pd.DataFrame({"scet": [], "name": [], "value": []})


# ---------------------------------------------------------------------------
# T6 — _parse_channel_dict
# ---------------------------------------------------------------------------

class TestParseChannelDict:
    def test_dict_is_multi_source(self):
        _, _, multi = _parse_channel_dict({"A": ["ch1", "ch2"], "B": ["ch3"]})
        assert multi is True

    def test_dict_sources_preserved(self):
        sources, _, _ = _parse_channel_dict({"src1": ["a", "b"], "src2": ["c"]})
        assert sources == ["src1", "src2"]

    def test_dict_channel_map(self):
        _, channel_map, _ = _parse_channel_dict({"src1": ["a", "b"], "src2": ["c"]})
        assert channel_map["src1"] == ["a", "b"]
        assert channel_map["src2"] == ["c"]

    def test_flat_list_is_single_source(self):
        sources, channel_map, multi = _parse_channel_dict(["ch1", "ch2", "ch3"])
        assert multi is False
        assert sources == ["default"]
        assert channel_map["default"] == ["ch1", "ch2", "ch3"]

    def test_semantic_dict_is_single_source(self):
        entries = [_MockEntry("SPu"), _MockEntry("VBBz")]
        sources, channel_map, multi = _parse_channel_dict(entries)
        assert multi is False
        assert channel_map["default"] == ["SPu", "VBBz"]

    def test_semantic_dict_uses_name_attr(self):
        entries = [_MockEntry("X"), _MockEntry("Y"), _MockEntry("Z")]
        _, channel_map, _ = _parse_channel_dict(entries)
        assert channel_map["default"] == ["X", "Y", "Z"]


# ---------------------------------------------------------------------------
# T6 — Source selector visibility
# ---------------------------------------------------------------------------

class TestSourceSelectorVisibility:
    def test_single_source_not_multi(self):
        ex = ChannelExplorer(["ch1", "ch2"])
        assert not ex._multi_source

    def test_multi_source_flagged(self):
        ex = ChannelExplorer({"src1": ["ch1"], "src2": ["ch2"]})
        assert ex._multi_source

    def test_multi_source_selector_has_correct_options(self):
        ex = ChannelExplorer({"src1": ["ch1"], "src2": ["ch2"]})
        assert list(ex._source_selector.options) == ["src1", "src2"]

    def test_source_change_updates_combobox_options(self):
        ex = ChannelExplorer({"src1": ["a", "b"], "src2": ["c", "d"]})
        ex._source_selector.value = "src2"
        assert set(ex._combobox.options) == {"c", "d"}


# ---------------------------------------------------------------------------
# T6 — Add button / chip management
# ---------------------------------------------------------------------------

class TestAddButton:
    def test_add_channel(self):
        ex = ChannelExplorer(["ch1", "ch2"])
        ex._combobox.value = "ch1"
        ex._on_add(None)
        assert "ch1" in ex.selected_channels

    def test_add_no_duplicates(self):
        ex = ChannelExplorer(["ch1", "ch2"])
        ex._combobox.value = "ch1"
        ex._on_add(None)
        ex._combobox.value = "ch1"
        ex._on_add(None)
        assert ex.selected_channels.count("ch1") == 1

    def test_add_empty_value_ignored(self):
        ex = ChannelExplorer(["ch1"])
        ex._combobox.value = ""
        ex._on_add(None)
        assert ex.selected_channels == []

    def test_add_clears_combobox(self):
        ex = ChannelExplorer(["ch1"])
        ex._combobox.value = "ch1"
        ex._on_add(None)
        assert ex._combobox.value == ""

    def test_add_multiple(self):
        ex = ChannelExplorer(["ch1", "ch2", "ch3"])
        for ch in ["ch1", "ch2", "ch3"]:
            ex._combobox.value = ch
            ex._on_add(None)
        assert ex.selected_channels == ["ch1", "ch2", "ch3"]


class TestClearAll:
    def test_clear_resets_selection(self):
        ex = ChannelExplorer(["ch1", "ch2"])
        for ch in ["ch1", "ch2"]:
            ex._combobox.value = ch
            ex._on_add(None)
        ex._on_clear(None)
        assert ex.selected_channels == []

    def test_clear_updates_chip_box(self):
        ex = ChannelExplorer(["ch1"])
        ex._combobox.value = "ch1"
        ex._on_add(None)
        ex._on_clear(None)
        assert len(ex._chip_box.children) == 0


# ---------------------------------------------------------------------------
# T6 — Time format toggle
# ---------------------------------------------------------------------------

class TestTimeFormat:
    def test_default_is_doy(self):
        ex = ChannelExplorer(["ch1"])
        assert ex._time_format == "doy"
        assert ex._fmt_toggle.value == "DOY"

    def test_kwarg_iso(self):
        ex = ChannelExplorer(["ch1"], time_format="iso")
        assert ex._time_format == "iso"
        assert ex._fmt_toggle.value == "ISO"

    def test_toggle_to_iso(self):
        ex = ChannelExplorer(["ch1"])
        ex._fmt_toggle.value = "ISO"
        assert ex._time_format == "iso"

    def test_toggle_back_to_doy(self):
        ex = ChannelExplorer(["ch1"], time_format="iso")
        ex._fmt_toggle.value = "DOY"
        assert ex._time_format == "doy"

    def test_toggle_updates_placeholder(self):
        ex = ChannelExplorer(["ch1"])
        ex._fmt_toggle.value = "ISO"
        assert "MM-DD" in ex._begin_input.placeholder

    def test_parse_doy(self):
        ex = ChannelExplorer(["ch1"])
        ts = ex._parse_time("2026-001T00:00:00")
        assert ts == pd.Timestamp("2026-01-01 00:00:00")

    def test_parse_iso(self):
        ex = ChannelExplorer(["ch1"], time_format="iso")
        ts = ex._parse_time("2026-01-15T12:30:00")
        assert ts == pd.Timestamp("2026-01-15 12:30:00")

    def test_parse_bad_string_raises(self):
        ex = ChannelExplorer(["ch1"])
        with pytest.raises(ValueError):
            ex._parse_time("not-a-date")


# ---------------------------------------------------------------------------
# T6 — Callback routing
# ---------------------------------------------------------------------------

class TestCallbackRouting:
    def test_single_source_query_fn_called(self):
        calls = []

        def query_fn(channels, t0, t1):
            calls.append((channels, t0, t1))
            return _empty_df()

        ex = ChannelExplorer(["ch1", "ch2"], query_fn=query_fn)
        ex._combobox.value = "ch1"
        ex._on_add(None)
        ex._begin_input.value = "2026-001T00:00:00"
        ex._end_input.value = "2026-001T01:00:00"
        ex._on_plot(None)

        assert len(calls) == 1
        assert calls[0][0] == ["ch1"]

    def test_single_source_passes_timestamps(self):
        calls = []

        def query_fn(channels, t0, t1):
            calls.append((t0, t1))
            return _empty_df()

        ex = ChannelExplorer(["ch1"], query_fn=query_fn)
        ex._combobox.value = "ch1"
        ex._on_add(None)
        ex._begin_input.value = "2026-001T00:00:00"
        ex._end_input.value = "2026-002T00:00:00"
        ex._on_plot(None)

        assert calls[0][0] == pd.Timestamp("2026-01-01")
        assert calls[0][1] == pd.Timestamp("2026-01-02")

    def test_multi_source_routes_to_correct_fn(self):
        calls_a, calls_b = [], []

        def fn_a(channels, t0, t1):
            calls_a.append(channels)
            return _empty_df()

        def fn_b(channels, t0, t1):
            calls_b.append(channels)
            return _empty_df()

        ex = ChannelExplorer(
            {"src_a": ["ch1"], "src_b": ["ch2"]},
            query_fns={"src_a": fn_a, "src_b": fn_b},
        )
        ex._source_selector.value = "src_a"
        ex._combobox.value = "ch1"
        ex._on_add(None)
        ex._source_selector.value = "src_b"
        ex._combobox.value = "ch2"
        ex._on_add(None)

        ex._begin_input.value = "2026-001T00:00:00"
        ex._end_input.value = "2026-001T01:00:00"
        ex._on_plot(None)

        assert calls_a == [["ch1"]]
        assert calls_b == [["ch2"]]

    def test_no_query_fn_returns_empty(self):
        ex = ChannelExplorer(["ch1"])
        ex._combobox.value = "ch1"
        ex._on_add(None)
        result = ex._run_query(pd.Timestamp("2026-01-01"), pd.Timestamp("2026-01-02"))
        assert result.empty

    def test_plot_with_no_channels_does_not_call_query(self):
        calls = []

        def query_fn(channels, t0, t1):
            calls.append(channels)
            return _empty_df()

        ex = ChannelExplorer(["ch1"], query_fn=query_fn)
        ex._begin_input.value = "2026-001T00:00:00"
        ex._end_input.value = "2026-001T01:00:00"
        ex._on_plot(None)

        assert calls == []


# ---------------------------------------------------------------------------
# T7 — Stack / Overlay y_vars + toggle
# ---------------------------------------------------------------------------

class TestBuildYVars:
    def test_stack_one_subplot_per_channel(self):
        ex = ChannelExplorer(["ch1", "ch2", "ch3"])
        for ch in ["ch1", "ch2", "ch3"]:
            ex._combobox.value = ch
            ex._on_add(None)
        ex._mode = "stack"
        assert ex._build_y_vars() == [["ch1"], ["ch2"], ["ch3"]]

    def test_overlay_all_on_one_subplot(self):
        ex = ChannelExplorer(["ch1", "ch2", "ch3"])
        for ch in ["ch1", "ch2", "ch3"]:
            ex._combobox.value = ch
            ex._on_add(None)
        ex._mode = "overlay"
        assert ex._build_y_vars() == [["ch1", "ch2", "ch3"]]

    def test_toggle_to_overlay(self):
        ex = ChannelExplorer(["ch1"])
        ex._mode_toggle.value = "Overlay"
        assert ex._mode == "overlay"

    def test_toggle_back_to_stack(self):
        ex = ChannelExplorer(["ch1"])
        ex._mode_toggle.value = "Overlay"
        ex._mode_toggle.value = "Stack"
        assert ex._mode == "stack"


# ---------------------------------------------------------------------------
# T8 — Per-chip ✕ remove
# ---------------------------------------------------------------------------

class TestChipRemove:
    def test_remove_channel_removes_only_that_channel(self):
        ex = ChannelExplorer(["ch1", "ch2", "ch3"])
        for ch in ["ch1", "ch2", "ch3"]:
            ex._combobox.value = ch
            ex._on_add(None)

        ex._remove_channel("default", "ch2")
        assert "ch2" not in ex.selected_channels
        assert "ch1" in ex.selected_channels
        assert "ch3" in ex.selected_channels

    def test_remove_channel_decrements_count(self):
        ex = ChannelExplorer(["ch1", "ch2", "ch3"])
        for ch in ["ch1", "ch2", "ch3"]:
            ex._combobox.value = ch
            ex._on_add(None)

        before = len(ex.selected_channels)
        ex._remove_channel("default", "ch1")
        assert len(ex.selected_channels) == before - 1

    def test_remove_nonexistent_channel_is_safe(self):
        ex = ChannelExplorer(["ch1"])
        ex._remove_channel("default", "does_not_exist")
        assert ex.selected_channels == []

    def test_chip_box_updated_after_remove(self):
        ex = ChannelExplorer(["ch1", "ch2"])
        for ch in ["ch1", "ch2"]:
            ex._combobox.value = ch
            ex._on_add(None)
        chip_count_before = len(ex._chip_box.children)
        ex._remove_channel("default", "ch1")
        assert len(ex._chip_box.children) == chip_count_before - 1


# ---------------------------------------------------------------------------
# T8 — Remove Subplot button
# ---------------------------------------------------------------------------

class TestRemoveSubplot:
    def test_stack_pops_last_channel(self):
        ex = ChannelExplorer(["ch1", "ch2", "ch3"])
        for ch in ["ch1", "ch2", "ch3"]:
            ex._combobox.value = ch
            ex._on_add(None)

        ex._mode = "stack"
        ex._on_remove_subplot(None)
        assert ex.selected_channels == ["ch1", "ch2"]

    def test_overlay_is_noop(self):
        ex = ChannelExplorer(["ch1", "ch2", "ch3"])
        for ch in ["ch1", "ch2", "ch3"]:
            ex._combobox.value = ch
            ex._on_add(None)

        ex._mode = "overlay"
        ex._on_remove_subplot(None)
        assert len(ex.selected_channels) == 3

    def test_single_channel_stack_is_noop(self):
        ex = ChannelExplorer(["ch1"])
        ex._combobox.value = "ch1"
        ex._on_add(None)

        ex._mode = "stack"
        ex._on_remove_subplot(None)
        assert ex.selected_channels == ["ch1"]

    def test_subsequent_plot_reflects_removed_channel(self):
        calls = []

        def query_fn(channels, t0, t1):
            calls.append(list(channels))
            return _empty_df()

        ex = ChannelExplorer(["ch1", "ch2", "ch3"], query_fn=query_fn)
        for ch in ["ch1", "ch2", "ch3"]:
            ex._combobox.value = ch
            ex._on_add(None)

        ex._mode = "stack"
        ex._on_remove_subplot(None)

        ex._begin_input.value = "2026-001T00:00:00"
        ex._end_input.value = "2026-001T01:00:00"
        ex._on_plot(None)

        assert "ch3" not in calls[-1]

    def test_remove_subplot_btn_disabled_in_overlay(self):
        ex = ChannelExplorer(["ch1", "ch2"])
        for ch in ["ch1", "ch2"]:
            ex._combobox.value = ch
            ex._on_add(None)
        ex._mode_toggle.value = "Overlay"
        assert ex._remove_subplot_btn.disabled

    def test_remove_subplot_btn_enabled_in_stack_multiple(self):
        ex = ChannelExplorer(["ch1", "ch2"])
        for ch in ["ch1", "ch2"]:
            ex._combobox.value = ch
            ex._on_add(None)
        ex._mode_toggle.value = "Stack"
        assert not ex._remove_subplot_btn.disabled

    def test_remove_subplot_btn_disabled_with_one_channel(self):
        ex = ChannelExplorer(["ch1"])
        ex._combobox.value = "ch1"
        ex._on_add(None)
        ex._mode_toggle.value = "Stack"
        assert ex._remove_subplot_btn.disabled


# ---------------------------------------------------------------------------
# T9 — LogExplorer
# ---------------------------------------------------------------------------

from tts_dtat.explorer import LogExplorer
from tts_data_utils.core.log import TtsLogFrame, TtsLogRowSeries
import ipywidgets as widgets


_SAMPLE_ROWS = [
    {'scet': '2024-001T00:00:00', 'name': 'SEQ_LOAD',  'level': 'ACTIVITY_LO', 'message': 'Loading cmds'},
    {'scet': '2024-001T00:01:00', 'name': 'CRC_FAIL',  'level': 'WARNING_HI',  'message': 'CRC mismatch block 5'},
    {'scet': '2024-001T00:02:00', 'name': 'SAFE_MODE', 'level': 'FATAL',       'message': 'Entering safe mode'},
    {'scet': '2024-001T00:03:00', 'name': 'DIAG',      'level': 'DIAGNOSTIC',  'message': 'Boot OK'},
]


class _TestLogFrame(TtsLogFrame):
    DEFAULT_TIME_LABEL = 'scet'
    LEVELS = ['DIAGNOSTIC', 'ACTIVITY_LO', 'WARNING_HI', 'FATAL']
    FILTER_COLS = {
        'level': ['DIAGNOSTIC', 'ACTIVITY_LO', 'WARNING_HI', 'FATAL'],
        'name': None,
    }


class TestLogExplorerWidgets:
    def test_enumerated_filter_col_creates_select_multiple(self):
        ex = LogExplorer(_TestLogFrame)
        assert isinstance(ex._filter_widgets['level'], widgets.SelectMultiple)

    def test_none_filter_col_creates_text_input(self):
        ex = LogExplorer(_TestLogFrame)
        assert isinstance(ex._filter_widgets['name'], widgets.Text)

    def test_no_query_fn_hides_time_inputs(self):
        ex = LogExplorer(_TestLogFrame)
        assert ex._begin_input is None
        assert ex._end_input is None

    def test_query_fn_shows_time_inputs(self):
        ex = LogExplorer(_TestLogFrame, query_fn=lambda t0, t1: _TestLogFrame())
        assert ex._begin_input is not None
        assert ex._end_input is not None

    def test_frame_rendered_immediately_when_passed(self):
        frame = _TestLogFrame(_SAMPLE_ROWS)
        ex = LogExplorer(_TestLogFrame, frame=frame)
        assert ex._loaded_frame is frame


class TestLogExplorerFiltering:
    def setup_method(self):
        self.frame = _TestLogFrame(_SAMPLE_ROWS)

    def test_level_filter_restricts_rows(self):
        ex = LogExplorer(_TestLogFrame, frame=self.frame)
        ex._filter_widgets['level'].value = ('FATAL',)
        result = ex._apply_filters(self.frame)
        assert len(result) == 1
        assert result.iloc[0]['name'] == 'SAFE_MODE'

    def test_name_text_filter_case_insensitive(self):
        ex = LogExplorer(_TestLogFrame, frame=self.frame)
        ex._filter_widgets['name'].value = 'crc'
        result = ex._apply_filters(self.frame)
        assert len(result) == 1
        assert result.iloc[0]['name'] == 'CRC_FAIL'

    def test_search_box_applies_regex(self):
        ex = LogExplorer(_TestLogFrame, frame=self.frame)
        ex._search_input.value = r'block \d+'
        result = ex._apply_filters(self.frame)
        assert len(result) == 1

    def test_empty_filters_return_all_rows(self):
        ex = LogExplorer(_TestLogFrame, frame=self.frame)
        result = ex._apply_filters(self.frame)
        assert len(result) == len(_SAMPLE_ROWS)

    def test_clear_filters_resets_to_all(self):
        ex = LogExplorer(_TestLogFrame, frame=self.frame)
        ex._filter_widgets['level'].value = ('FATAL',)
        ex._on_clear_filters(None)
        assert list(ex._filter_widgets['level'].value) == []

    def test_no_match_renders_message(self):
        ex = LogExplorer(_TestLogFrame, frame=self.frame)
        ex._filter_widgets['level'].value = ('FATAL',)
        ex._search_input.value = 'no_such_string_xyz'
        ex._on_apply(None)

    def test_load_without_times_prints_error(self):
        ex = LogExplorer(_TestLogFrame, query_fn=lambda t0, t1: _TestLogFrame())
        ex._begin_input.value = ''
        ex._end_input.value = ''
        ex._on_load(None)

    def test_load_with_bad_time_prints_error(self):
        ex = LogExplorer(_TestLogFrame, query_fn=lambda t0, t1: _TestLogFrame())
        ex._begin_input.value = 'not-a-time'
        ex._end_input.value = '2024-001T01:00:00'
        ex._on_load(None)
