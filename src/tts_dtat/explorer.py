"""tts_dtat.explorer — interactive mission-agnostic ChannelExplorer widget.

Public API
----------
ChannelExplorer(channel_dict, query_fn=None, query_fns=None, n_points=None,
                time_format=None)
    ipywidgets-based UI for selecting telemetry channels, entering time
    bounds, and plotting queried data via PlotOrchestrator or
    make_stacked_graph.

Channel dict protocol
---------------------
- ``dict`` → multi-source mode; keys are source names, values are channel
  name iterables.
- Non-dict iterable whose first element has a ``.name`` attribute →
  SemanticDictionary (single-source); channels extracted via ``.name``.
- Any other iterable → flat list of strings (single-source).

Closes: #15 (T6), #16 (T7), #17 (T8)
"""

from __future__ import annotations

import datetime
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, Tuple

import ipywidgets as widgets
import pandas as pd
from IPython.display import clear_output
from IPython.display import display as _ipy_display


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

_TIME_FORMATS: Dict[str, str] = {
    "doy": "%Y-%jT%H:%M:%S",
    "iso": "%Y-%m-%dT%H:%M:%S",
}

_TIME_PLACEHOLDERS: Dict[str, str] = {
    "doy": "YYYY-DDDTHH:MM:SS",
    "iso": "YYYY-MM-DDTHH:MM:SS",
}


def _parse_channel_dict(
    channel_dict: Any,
) -> Tuple[List[str], Dict[str, List[str]], bool]:
    """Inspect *channel_dict* and return ``(sources, channel_map, multi_source)``.

    Args:
        channel_dict: One of:
            - ``dict`` → multi-source.
            - Iterable whose first item has a ``.name`` attr → SemanticDictionary.
            - Any other iterable → flat channel list.

    Returns:
        Tuple of ``(sources, channel_map, multi_source)`` where *sources* is a
        list of source-name strings, *channel_map* maps each source to its
        channel list, and *multi_source* is ``True`` for dict input.
    """
    if isinstance(channel_dict, dict):
        sources = list(channel_dict.keys())
        channel_map = {src: list(chs) for src, chs in channel_dict.items()}
        return sources, channel_map, True

    items = list(channel_dict)
    if items and hasattr(items[0], "name"):
        channels = [c.name for c in items]
    else:
        channels = [str(c) for c in items]

    return ["default"], {"default": channels}, False


# ---------------------------------------------------------------------------
# ChannelExplorer
# ---------------------------------------------------------------------------

class ChannelExplorer:
    """Interactive ipywidgets panel for exploring and plotting telemetry channels.

    Args:
        channel_dict: Channel source — see module docstring for accepted shapes.
        query_fn: ``Callable(channels: list[str], t0: pd.Timestamp,
            t1: pd.Timestamp) → pd.DataFrame``.  Single-source mode.
        query_fns: ``dict[source_name, Callable]`` — each callable has the
            same signature as *query_fn*.  Multi-source mode; results are
            concatenated.
        n_points: When set, each Plot click wraps queried data in a
            :class:`~tts_dtat.downsample.PlotOrchestrator` with this LTTB
            budget.  When ``None``, :func:`~tts_dtat.plot.make_stacked_graph`
            is used directly.
        time_format: ``"doy"`` (default) or ``"iso"``.  Initial time-input
            format; the DOY/ISO toggle overrides it at runtime.

    Example::

        explorer = ChannelExplorer(
            {"IE": fss.get_ie_chanvals, "FCPU": fss.get_fcpu_chanvals},
            query_fns={...},
            n_points=500,
        )
        explorer  # displays in Jupyter
    """

    def __init__(
        self,
        channel_dict: Any,
        query_fn: Optional[Callable] = None,
        query_fns: Optional[Dict[str, Callable]] = None,
        n_points: Optional[int] = None,
        time_format: Optional[str] = None,
    ) -> None:
        self._n_points = n_points
        self._time_format: str = (time_format or "doy").lower()
        self._query_fn = query_fn
        self._query_fns: Dict[str, Callable] = query_fns or {}

        self._sources, self._channel_map, self._multi_source = _parse_channel_dict(
            channel_dict
        )
        self._selected: List[Tuple[str, str]] = []
        self._mode: str = "stack"

        self._build_ui()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def display(self) -> None:
        """Render the widget.  Called automatically by Jupyter via
        ``_ipython_display_``."""
        _ipy_display(self._ui)

    def _ipython_display_(self, **kwargs: Any) -> None:
        self.display()

    @property
    def selected_channels(self) -> List[str]:
        """Channel names currently in the selection (without source prefix)."""
        return [ch for _, ch in self._selected]

    @property
    def selected_items(self) -> List[Tuple[str, str]]:
        """``(source, channel)`` pairs currently selected."""
        return list(self._selected)

    def _build_y_vars(self) -> List[List[str]]:
        """Compute ``y_vars`` from the current selection and Stack/Overlay mode.

        Stack → ``[[ch] for ch in selected]``
        Overlay → ``[selected]``
        """
        channels = self.selected_channels
        if self._mode == "stack":
            return [[ch] for ch in channels]
        return [channels]

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ----- Source selector (hidden in single-source mode) -----
        self._source_selector = widgets.Dropdown(
            options=self._sources,
            value=self._sources[0],
            description="Source:",
            layout=widgets.Layout(width="220px"),
        )
        self._source_selector.observe(self._on_source_change, names="value")

        # ----- Channel combobox + Add -----
        self._combobox = widgets.Combobox(
            options=self._channel_map[self._sources[0]],
            placeholder="Type to search channels\u2026",
            ensure_option=False,
            layout=widgets.Layout(width="320px"),
        )
        self._add_btn = widgets.Button(
            description="Add",
            button_style="primary",
            layout=widgets.Layout(width="80px"),
        )
        self._add_btn.on_click(self._on_add)

        # ----- Chip area + Clear All -----
        self._chip_box = widgets.HBox(
            [], layout=widgets.Layout(flex_flow="row wrap", margin="4px 0")
        )
        self._clear_btn = widgets.Button(
            description="Clear All",
            button_style="warning",
            layout=widgets.Layout(width="100px"),
        )
        self._clear_btn.on_click(self._on_clear)

        # ----- Time inputs -----
        ph = _TIME_PLACEHOLDERS[self._time_format]
        self._begin_input = widgets.Text(
            placeholder=ph,
            description="Begin:",
            layout=widgets.Layout(width="300px"),
        )
        self._end_input = widgets.Text(
            placeholder=ph,
            description="End:",
            layout=widgets.Layout(width="300px"),
        )

        # ----- DOY / ISO toggle -----
        self._fmt_toggle = widgets.ToggleButtons(
            options=["DOY", "ISO"],
            value="DOY" if self._time_format == "doy" else "ISO",
            layout=widgets.Layout(width="200px"),
        )
        self._fmt_toggle.observe(self._on_fmt_change, names="value")

        # ----- Stack / Overlay toggle (T7) -----
        self._mode_toggle = widgets.ToggleButtons(
            options=["Stack", "Overlay"],
            value="Stack",
            layout=widgets.Layout(width="220px"),
        )
        self._mode_toggle.observe(self._on_mode_change, names="value")

        # ----- Plot button -----
        self._plot_btn = widgets.Button(
            description="Plot",
            button_style="success",
            layout=widgets.Layout(width="100px"),
        )
        self._plot_btn.on_click(self._on_plot)

        # ----- Remove Subplot button (T8) -----
        self._remove_subplot_btn = widgets.Button(
            description="Remove Subplot",
            button_style="danger",
            layout=widgets.Layout(width="160px"),
        )
        self._remove_subplot_btn.on_click(self._on_remove_subplot)
        self._refresh_remove_btn_state()

        # ----- Output widget -----
        self._output = widgets.Output()

        # ----- Assemble layout -----
        search_row = widgets.HBox([self._combobox, self._add_btn])
        chip_row = widgets.HBox([self._chip_box, self._clear_btn])
        time_row = widgets.VBox([
            widgets.HBox([self._begin_input, self._end_input]),
            widgets.HBox([widgets.Label("Time format:"), self._fmt_toggle]),
        ])
        control_row = widgets.HBox([
            widgets.Label("Layout:"),
            self._mode_toggle,
            self._plot_btn,
            self._remove_subplot_btn,
        ])

        rows: List[Any] = []
        if self._multi_source:
            rows.append(widgets.HBox([self._source_selector]))
        rows += [search_row, chip_row, time_row, control_row, self._output]
        self._ui = widgets.VBox(rows)

    # ------------------------------------------------------------------
    # Chip management
    # ------------------------------------------------------------------

    def _render_chips(self) -> None:
        """Rebuild the chip display from the current ``_selected`` list."""
        chips = []
        for source, ch in self._selected:
            label_text = f"{source}/{ch}" if self._multi_source else ch
            lbl = widgets.Label(value=label_text)
            rm_btn = widgets.Button(
                description="\u2715",
                button_style="",
                layout=widgets.Layout(width="28px", height="28px", padding="0"),
            )
            rm_btn.on_click(self._make_remover(source, ch))
            chip = widgets.HBox(
                [lbl, rm_btn],
                layout=widgets.Layout(
                    border="1px solid #aaa",
                    margin="2px",
                    padding="2px 6px",
                ),
            )
            chips.append(chip)
        self._chip_box.children = chips
        self._refresh_remove_btn_state()

    def _make_remover(self, source: str, channel: str) -> Callable:
        """Return a click handler that removes *channel* from *source*."""
        def _remove(_: Any) -> None:
            self._remove_channel(source, channel)
        return _remove

    def _remove_channel(self, source: str, channel: str) -> None:
        """Remove a single ``(source, channel)`` pair from the selection."""
        try:
            self._selected.remove((source, channel))
        except ValueError:
            return
        self._render_chips()

    def _refresh_remove_btn_state(self) -> None:
        """Disable Remove Subplot when in Overlay mode or only one channel selected."""
        self._remove_subplot_btn.disabled = (
            self._mode == "overlay" or len(self._selected) <= 1
        )

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_source_change(self, change: Dict) -> None:
        src = change["new"]
        self._combobox.options = self._channel_map.get(src, [])
        self._combobox.value = ""

    def _on_add(self, _: Any) -> None:
        raw = (self._combobox.value or "").strip()
        if not raw:
            return
        source = (
            self._source_selector.value if self._multi_source else self._sources[0]
        )
        item = (source, raw)
        if item not in self._selected:
            self._selected.append(item)
            self._render_chips()
        self._combobox.value = ""

    def _on_clear(self, _: Any) -> None:
        self._selected.clear()
        self._render_chips()

    def _on_fmt_change(self, change: Dict) -> None:
        self._time_format = "doy" if change["new"] == "DOY" else "iso"
        ph = _TIME_PLACEHOLDERS[self._time_format]
        self._begin_input.placeholder = ph
        self._end_input.placeholder = ph

    def _on_mode_change(self, change: Dict) -> None:
        self._mode = change["new"].lower()
        self._refresh_remove_btn_state()

    def _on_plot(self, _: Any) -> None:
        """Execute query, build figure, render into Output widget (T7)."""
        if not self._selected:
            with self._output:
                clear_output(wait=True)
                print("No channels selected.")
            return

        t0_str = self._begin_input.value.strip()
        t1_str = self._end_input.value.strip()
        if not t0_str or not t1_str:
            with self._output:
                clear_output(wait=True)
                print("Please enter both begin and end times.")
            return

        try:
            t0 = self._parse_time(t0_str)
            t1 = self._parse_time(t1_str)
        except ValueError as exc:
            with self._output:
                clear_output(wait=True)
                print(f"Time parse error: {exc}")
            return

        try:
            data = self._run_query(t0, t1)
        except Exception as exc:
            with self._output:
                clear_output(wait=True)
                print(f"Query error: {exc}")
            return

        y_vars = self._build_y_vars()

        with self._output:
            clear_output(wait=True)
            if data is None or (hasattr(data, "empty") and data.empty):
                print("No data returned for the selected channels and time range.")
                return
            if self._n_points is not None:
                from tts_dtat.downsample import PlotOrchestrator
                fig = PlotOrchestrator(
                    data, y_vars, n_points=self._n_points
                ).plot()
            else:
                from tts_dtat.plot import make_stacked_graph
                fig, *_ = make_stacked_graph(data, y_vars)
            _ipy_display(fig)

    def _on_remove_subplot(self, _: Any) -> None:
        """Pop the last selected channel in Stack mode (T8)."""
        if self._mode == "overlay" or len(self._selected) <= 1:
            return
        self._selected.pop()
        self._render_chips()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _parse_time(self, s: str) -> pd.Timestamp:
        """Parse a time string using the active format."""
        fmt = _TIME_FORMATS[self._time_format]
        try:
            return pd.Timestamp(datetime.datetime.strptime(s.strip(), fmt))
        except ValueError as exc:
            raise ValueError(
                f"Cannot parse {s!r} with format {fmt!r}: {exc}"
            ) from exc

    def _run_query(self, t0: pd.Timestamp, t1: pd.Timestamp) -> pd.DataFrame:
        """Dispatch query to ``query_fn`` or ``query_fns`` and return results."""
        if self._multi_source:
            by_source: Dict[str, List[str]] = defaultdict(list)
            for source, ch in self._selected:
                by_source[source].append(ch)
            frames = []
            for source, channels in by_source.items():
                fn = self._query_fns.get(source)
                if fn is None:
                    continue
                result = fn(channels, t0, t1)
                if result is not None and len(result) > 0:
                    frames.append(result)
            return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        else:
            if self._query_fn is None:
                return pd.DataFrame()
            channels = [ch for _, ch in self._selected]
            return self._query_fn(channels, t0, t1)
