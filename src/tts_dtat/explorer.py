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


def _right_pad(s: str, width: int) -> str:
    """Right-pad *s* with zeros to *width*, truncating if longer."""
    return (s + "0" * width)[:width]


def _complete_doy(s: str) -> str:
    """Complete a partial DOY timestamp string to YYYY-DDDTHH:MM:SS.

    Rules:
    - DOY field: zero-pad on the LEFT to three digits (``42`` → ``042``).
    - Hour/minute/second fields: zero-pad on the RIGHT to two digits
      (``3`` → ``30``, ``12:2`` → ``12:20:00``).

    Examples::

        _complete_doy("2026")         == "2026-001T00:00:00"
        _complete_doy("2026-042")     == "2026-042T00:00:00"
        _complete_doy("2026-042T12")  == "2026-042T12:00:00"
        _complete_doy("2026-042T12:2") == "2026-042T12:20:00"
    """
    s = s.strip()
    if not s:
        return s
    if "-" not in s:
        year = s[:4] if len(s) >= 4 else _right_pad(s, 4)
        return f"{year}-001T00:00:00"
    year, rest = s.split("-", 1)
    if "T" not in rest:
        doy = rest.zfill(3)[:3] if rest else "001"
        return f"{year}-{doy}T00:00:00"
    doy_raw, time_part = rest.split("T", 1)
    doy = doy_raw.zfill(3)[:3] if doy_raw else "001"
    if not time_part:
        return f"{year}-{doy}T00:00:00"
    tparts = time_part.split(":", 2)
    hour = _right_pad(tparts[0], 2) if tparts[0] else "00"
    minute = _right_pad(tparts[1], 2) if len(tparts) > 1 else "00"
    second = _right_pad(tparts[2], 2) if len(tparts) > 2 else "00"
    return f"{year}-{doy}T{hour}:{minute}:{second}"


def _complete_iso(s: str) -> str:
    """Complete a partial ISO timestamp string to YYYY-MM-DDTHH:MM:SS.

    Month, day, hour, minute, and second fields are right-padded with zeros.

    Examples::

        _complete_iso("2026")            == "2026-01-01T00:00:00"
        _complete_iso("2026-03")         == "2026-03-01T00:00:00"
        _complete_iso("2026-03-22T12")   == "2026-03-22T12:00:00"
        _complete_iso("2026-03-22T12:3") == "2026-03-22T12:30:00"
    """
    s = s.strip()
    if not s:
        return s
    if "T" in s:
        date_part, time_part = s.split("T", 1)
        dp = date_part.split("-")
        year = dp[0] if dp else "0000"
        month = _right_pad(dp[1], 2) if len(dp) > 1 else "01"
        day = _right_pad(dp[2], 2) if len(dp) > 2 else "01"
        tparts = time_part.split(":", 2)
        hour = _right_pad(tparts[0], 2) if tparts[0] else "00"
        minute = _right_pad(tparts[1], 2) if len(tparts) > 1 else "00"
        second = _right_pad(tparts[2], 2) if len(tparts) > 2 else "00"
        return f"{year}-{month}-{day}T{hour}:{minute}:{second}"
    dp = s.split("-")
    year = dp[0] if dp else "0000"
    month = _right_pad(dp[1], 2) if len(dp) > 1 else "01"
    day = _right_pad(dp[2], 2) if len(dp) > 2 else "01"
    return f"{year}-{month}-{day}T00:00:00"


def _complete_timestamp(s: str, fmt: str) -> str:
    """Dispatch to :func:`_complete_doy` or :func:`_complete_iso`."""
    if fmt == "doy":
        return _complete_doy(s)
    return _complete_iso(s)


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
        begin_time: Initial begin-time string (overrides class-level default).
        end_time: Initial end-time string (overrides class-level default).

    Class attributes:
        DEFAULT_BEGIN_OFFSET: :class:`datetime.timedelta` subtracted from
            ``utcnow()`` to produce the default begin time.  Subclasses may
            override this.  Default: 24 hours.
        DEFAULT_END_OFFSET: :class:`datetime.timedelta` subtracted from
            ``utcnow()`` to produce the default end time.  Default: 0
            (i.e., now).

    Example::

        explorer = ChannelExplorer(
            {"IE": fss.get_ie_chanvals, "FCPU": fss.get_fcpu_chanvals},
            query_fns={...},
            n_points=500,
        )
        explorer  # displays in Jupyter
    """

    DEFAULT_BEGIN_OFFSET: datetime.timedelta = datetime.timedelta(hours=24)
    DEFAULT_END_OFFSET: datetime.timedelta = datetime.timedelta(seconds=0)

    def __init__(
        self,
        channel_dict: Any,
        query_fn: Optional[Callable] = None,
        query_fns: Optional[Dict[str, Callable]] = None,
        n_points: Optional[int] = None,
        time_format: Optional[str] = None,
        begin_time: Optional[str] = None,
        end_time: Optional[str] = None,
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

        fmt = _TIME_FORMATS[self._time_format]
        now = datetime.datetime.utcnow()
        self._default_begin: str = (
            begin_time if begin_time is not None
            else (now - self.DEFAULT_BEGIN_OFFSET).strftime(fmt)
        )
        self._default_end: str = (
            end_time if end_time is not None
            else (now - self.DEFAULT_END_OFFSET).strftime(fmt)
        )

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
        _btn_layout = widgets.Layout(height="32px")
        _toggle_style = {"button_width": "auto", "font_size": "12px"}

        # ----- Source selector (hidden in single-source mode) -----
        self._source_selector = widgets.Dropdown(
            options=self._sources,
            value=self._sources[0],
            description="Source:",
            layout=widgets.Layout(width="220px", height="32px"),
        )
        self._source_selector.observe(self._on_source_change, names="value")

        # ----- Channel text input + Add -----
        _initial_opts = self._channel_map.get(self._sources[0], [])
        self._combobox = widgets.Combobox(
            options=list(_initial_opts),
            ensure_option=False,
            placeholder="Type channel name\u2026",
            layout=widgets.Layout(width="320px", height="32px"),
        )
        self._combobox_val: str = ""
        self._combobox.observe(self._on_combobox_change, names="value")
        self._combobox.on_submit(self._on_add)
        self._add_btn = widgets.Button(
            description="Add",
            button_style="primary",
            layout=widgets.Layout(width="64px", height="32px"),
        )
        self._add_btn.on_click(self._on_add)

        # ----- Chip area + Clear All -----
        self._chip_box = widgets.HBox(
            [], layout=widgets.Layout(flex_flow="row wrap", margin="4px 0")
        )
        self._clear_btn = widgets.Button(
            description="Clear All",
            button_style="warning",
            layout=widgets.Layout(width="84px", height="32px"),
        )
        self._clear_btn.on_click(self._on_clear)

        # ----- Time inputs with Enter-key completion -----
        ph = _TIME_PLACEHOLDERS[self._time_format]
        self._begin_input = widgets.Text(
            value=self._default_begin,
            placeholder=ph,
            description="Begin:",
            layout=widgets.Layout(width="280px"),
        )
        self._end_input = widgets.Text(
            value=self._default_end,
            placeholder=ph,
            description="End:",
            layout=widgets.Layout(width="280px"),
        )
        self._begin_input.on_submit(self._on_time_submit)
        self._end_input.on_submit(self._on_time_submit)

        # ----- DOY / ISO toggle -----
        self._fmt_toggle = widgets.ToggleButtons(
            options=["DOY", "ISO"],
            value="DOY" if self._time_format == "doy" else "ISO",
            style=_toggle_style,
            layout=widgets.Layout(width="auto"),
        )
        self._fmt_toggle.observe(self._on_fmt_change, names="value")

        # ----- Stack / Overlay toggle -----
        self._mode_toggle = widgets.ToggleButtons(
            options=["Stack", "Overlay"],
            value="Stack",
            style=_toggle_style,
            layout=widgets.Layout(width="auto"),
        )
        self._mode_toggle.observe(self._on_mode_change, names="value")

        # ----- Plot button -----
        self._plot_btn = widgets.Button(
            description="Plot",
            button_style="success",
            layout=widgets.Layout(width="72px", height="32px"),
        )
        self._plot_btn.on_click(self._on_plot)

        # ----- Remove Subplot button -----
        self._remove_subplot_btn = widgets.Button(
            description="\u2212 Subplot",
            button_style="danger",
            layout=widgets.Layout(width="90px", height="32px"),
        )
        self._remove_subplot_btn.on_click(self._on_remove_subplot)
        self._refresh_remove_btn_state()

        # ----- Output widget -----
        self._output = widgets.Output()

        # ----- Assemble layout -----
        _center = widgets.Layout(align_items="center")
        search_row = widgets.HBox(
            [self._combobox, self._add_btn],
            layout=widgets.Layout(align_items="center", gap="6px"),
        )
        chip_row = widgets.HBox(
            [self._chip_box, self._clear_btn],
            layout=widgets.Layout(align_items="flex-start", gap="6px"),
        )
        time_row = widgets.HBox(
            [self._begin_input, self._end_input],
            layout=widgets.Layout(gap="12px"),
        )
        control_row = widgets.HBox(
            [
                self._fmt_toggle,
                widgets.HTML("<span style='margin:auto 6px;font-size:12px'>Layout:</span>"),
                self._mode_toggle,
                self._plot_btn,
                self._remove_subplot_btn,
            ],
            layout=widgets.Layout(align_items="center", gap="6px"),
        )

        rows: List[Any] = []
        if self._multi_source:
            rows.append(widgets.HBox([self._source_selector]))
        rows += [search_row, chip_row, time_row, control_row, self._output]
        self._ui = widgets.VBox(
            rows,
            layout=widgets.Layout(gap="6px"),
        )

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
        self._combobox.options = list(self._channel_map.get(src, []))
        self._combobox.value = ""
        self._combobox_val = ""

    def _on_combobox_change(self, change: Dict) -> None:
        self._combobox_val = change["new"] or ""

    def _on_add(self, _: Any) -> None:
        raw = (self._combobox_val or "").strip()
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
        self._combobox_val = ""

    def _on_clear(self, _: Any) -> None:
        self._selected.clear()
        self._render_chips()

    def _on_time_submit(self, widget: Any) -> None:
        """Tab-complete a partial timestamp when Enter is pressed."""
        val = widget.value.strip()
        if val:
            widget.value = _complete_timestamp(val, self._time_format)

    def _on_fmt_change(self, change: Dict) -> None:
        old_fmt = self._time_format
        self._time_format = "doy" if change["new"] == "DOY" else "iso"
        ph = _TIME_PLACEHOLDERS[self._time_format]
        self._begin_input.placeholder = ph
        self._end_input.placeholder = ph
        # Reformat existing text values to the new format
        for widget in (self._begin_input, self._end_input):
            val = widget.value.strip()
            if val:
                try:
                    dt = datetime.datetime.strptime(val, _TIME_FORMATS[old_fmt])
                    widget.value = dt.strftime(_TIME_FORMATS[self._time_format])
                except ValueError:
                    widget.value = ""

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

        # Complete partial timestamps the same way on_submit does — ensures
        # plotting works even when Enter-key completion was not triggered.
        t0_raw = self._begin_input.value.strip()
        t1_raw = self._end_input.value.strip()
        if not t0_raw or not t1_raw:
            with self._output:
                clear_output(wait=True)
                print("Please enter both begin and end times.")
            return
        t0_str = _complete_timestamp(t0_raw, self._time_format)
        t1_str = _complete_timestamp(t1_raw, self._time_format)
        self._begin_input.value = t0_str
        self._end_input.value = t1_str

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
            x_var = (
                getattr(type(data), "DEFAULT_TIME_LABEL", None)
                or next(
                    (c for c in ("scet", "timestamp", "ert") if c in data.columns),
                    "scet",
                )
            )
            if self._n_points is not None:
                from tts_dtat.downsample import PlotOrchestrator
                fig = PlotOrchestrator(
                    data, y_vars, n_points=self._n_points, x_var=x_var
                ).interactive()
            else:
                from tts_dtat.plot import make_stacked_graph
                fig, *_ = make_stacked_graph(data, y_vars, x_var=x_var)
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
                    label_col = getattr(type(result), "LABEL_COL", None)
                    if label_col and label_col != "name" and label_col in result.columns:
                        result = result.rename(columns={label_col: "name"})
                    time_col = getattr(type(result), "DEFAULT_TIME_LABEL", None) or next(
                        (c for c in ("scet", "timestamp", "ert") if c in result.columns), None
                    )
                    if time_col and time_col != "scet" and time_col in result.columns:
                        result = result.rename(columns={time_col: "scet"})
                    frames.append(result)
            # Wrap in plain pd.DataFrame to strip any TtsDataFrame subclass type.
            # Columns were renamed to "name"/"scet" above; callers (PlotOrchestrator,
            # _on_plot x_var detection) must not pick up stale LABEL_COL /
            # DEFAULT_TIME_LABEL from the original subclass via type(data).
            result = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
            return pd.DataFrame(result)
        else:
            if self._query_fn is None:
                return pd.DataFrame()
            channels = [ch for _, ch in self._selected]
            return self._query_fn(channels, t0, t1)


# ---------------------------------------------------------------------------
# LogExplorer
# ---------------------------------------------------------------------------

class LogExplorer:
    """Interactive ipywidgets panel for exploring log / EVR data.

    The filter controls are built automatically from ``frame_cls.FILTER_COLS``:

    - A column mapped to a *list* of valid values becomes a
      ``SelectMultiple`` widget — the user picks zero or more levels.
    - A column mapped to ``None`` becomes a ``Text`` input — the widget
      applies a case-insensitive substring filter against that column.

    A free-text **Search** box at the bottom applies :meth:`TtsLogFrame.search`
    (regex against ``VALUE_COL``) after the column filters.

    When *query_fn* is supplied the widget also shows time-range inputs and a
    **Load** button; the callable is expected to accept ``(t0, t1)`` and return
    a :class:`~tts_data_utils.core.log.TtsLogFrame` instance.  The returned
    frame is cached internally so that filter changes do not re-query.

    When *frame* is supplied directly (offline / already-loaded data) the time
    inputs are hidden and filtering operates purely client-side.

    Args:
        frame_cls: A :class:`~tts_data_utils.core.log.TtsLogFrame` subclass.
            Must expose ``FILTER_COLS``, ``LEVEL_COL``, ``LABEL_COL``, and
            ``VALUE_COL`` class variables.
        query_fn: Optional ``Callable[[pd.Timestamp, pd.Timestamp], TtsLogFrame]``
            for time-range loading.
        frame: Optional pre-loaded ``TtsLogFrame`` instance.  If both *frame*
            and *query_fn* are provided the pre-loaded frame is shown on open
            and replaced when **Load** is clicked.
        time_format: ``"doy"`` (default) or ``"iso"``.

    Example::

        from tts_dtat.explorer import LogExplorer
        from demosat_data_utils.evr import DemosatEvrFrame

        explorer = LogExplorer(
            DemosatEvrFrame,
            query_fn=lambda t0, t1: my_query.get_evrs(t0=t0, t1=t1),
        )
        explorer  # renders in Jupyter
    """

    def __init__(
        self,
        frame_cls: type,
        query_fn: Optional[Callable] = None,
        frame: Optional[Any] = None,
        time_format: Optional[str] = None,
    ) -> None:
        self._frame_cls = frame_cls
        self._query_fn = query_fn
        self._loaded_frame: Optional[Any] = frame
        self._time_format: str = (time_format or "doy").lower()

        self._filter_widgets: Dict[str, Any] = {}
        self._build_ui()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def display(self) -> None:
        """Render the widget."""
        _ipy_display(self._ui)

    def _ipython_display_(self, **kwargs: Any) -> None:
        self.display()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        rows: List[Any] = []

        # ----- Time range + Load (only when query_fn is supplied) -----
        if self._query_fn is not None:
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
            self._fmt_toggle = widgets.ToggleButtons(
                options=["DOY", "ISO"],
                value="DOY" if self._time_format == "doy" else "ISO",
                layout=widgets.Layout(width="200px"),
            )
            self._fmt_toggle.observe(self._on_fmt_change, names="value")
            self._load_btn = widgets.Button(
                description="Load",
                button_style="primary",
                layout=widgets.Layout(width="100px"),
            )
            self._load_btn.on_click(self._on_load)
            rows.append(widgets.VBox([
                widgets.HBox([self._begin_input, self._end_input]),
                widgets.HBox([widgets.Label("Time format:"), self._fmt_toggle,
                               self._load_btn]),
            ]))
        else:
            self._begin_input = None
            self._end_input = None

        # ----- FILTER_COLS-driven filter section -----
        filter_col_widgets: List[Any] = []
        filter_cols: Dict = getattr(self._frame_cls, 'FILTER_COLS', {})
        for col, valid_values in filter_cols.items():
            if valid_values is not None:
                w = widgets.SelectMultiple(
                    options=valid_values,
                    value=[],
                    description=f"{col}:",
                    layout=widgets.Layout(width="300px", height="120px"),
                )
            else:
                w = widgets.Text(
                    placeholder=f"filter {col}\u2026",
                    description=f"{col}:",
                    layout=widgets.Layout(width="300px"),
                )
            self._filter_widgets[col] = w
            filter_col_widgets.append(w)

        if filter_col_widgets:
            rows.append(widgets.VBox(filter_col_widgets))

        # ----- Message search (regex on VALUE_COL) -----
        value_col = getattr(self._frame_cls, 'VALUE_COL', 'message') or 'message'
        self._search_input = widgets.Text(
            placeholder=f"regex search on {value_col}\u2026",
            description="Search:",
            layout=widgets.Layout(width="400px"),
        )

        # ----- Apply Filters + Clear buttons -----
        self._apply_btn = widgets.Button(
            description="Apply Filters",
            button_style="success",
            layout=widgets.Layout(width="130px"),
        )
        self._apply_btn.on_click(self._on_apply)
        self._clear_filters_btn = widgets.Button(
            description="Clear",
            button_style="warning",
            layout=widgets.Layout(width="80px"),
        )
        self._clear_filters_btn.on_click(self._on_clear_filters)

        rows.append(widgets.HBox([
            self._search_input,
            self._apply_btn,
            self._clear_filters_btn,
        ]))

        # ----- Output widget -----
        self._output = widgets.Output()
        rows.append(self._output)

        self._ui = widgets.VBox(rows)

        # Show pre-loaded frame immediately if supplied
        if self._loaded_frame is not None:
            self._render(self._loaded_frame)

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_fmt_change(self, change: Dict) -> None:
        self._time_format = "doy" if change["new"] == "DOY" else "iso"
        ph = _TIME_PLACEHOLDERS[self._time_format]
        if self._begin_input is not None:
            self._begin_input.placeholder = ph
        if self._end_input is not None:
            self._end_input.placeholder = ph

    def _on_load(self, _: Any) -> None:
        """Call query_fn with the entered time bounds and cache the result."""
        t0_str = (self._begin_input.value or "").strip()
        t1_str = (self._end_input.value or "").strip()
        if not t0_str or not t1_str:
            with self._output:
                clear_output(wait=True)
                print("Enter both begin and end times before loading.")
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
            self._loaded_frame = self._query_fn(t0, t1)
        except Exception as exc:
            with self._output:
                clear_output(wait=True)
                print(f"Query error: {exc}")
            return
        self._on_apply(None)

    def _on_apply(self, _: Any) -> None:
        """Apply all active filters to the loaded frame and render."""
        if self._loaded_frame is None:
            with self._output:
                clear_output(wait=True)
                print("No data loaded. Use Load to fetch data first.")
            return
        try:
            result = self._apply_filters(self._loaded_frame)
        except Exception as exc:
            with self._output:
                clear_output(wait=True)
                print(f"Filter error: {exc}")
            return
        self._render(result)

    def _on_clear_filters(self, _: Any) -> None:
        """Reset all filter widgets to empty/unselected."""
        filter_cols: Dict = getattr(self._frame_cls, 'FILTER_COLS', {})
        for col, valid_values in filter_cols.items():
            w = self._filter_widgets.get(col)
            if w is None:
                continue
            if valid_values is not None:
                w.value = []
            else:
                w.value = ""
        self._search_input.value = ""
        if self._loaded_frame is not None:
            self._render(self._loaded_frame)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def _apply_filters(self, frame: Any) -> Any:
        """Apply FILTER_COLS widgets + search box to *frame* and return result."""
        filter_cols: Dict = getattr(self._frame_cls, 'FILTER_COLS', {})
        level_col = getattr(self._frame_cls, 'LEVEL_COL', None)
        label_col = getattr(self._frame_cls, 'LABEL_COL', None)

        for col, valid_values in filter_cols.items():
            w = self._filter_widgets.get(col)
            if w is None:
                continue
            if valid_values is not None:
                selected = list(w.value)
                if selected:
                    if col == level_col:
                        frame = frame.filter_level(selected)
                    elif col == label_col:
                        frame = frame.filter_label(selected)
                    else:
                        frame = frame[frame[col].isin(selected)]
            else:
                text = (w.value or "").strip()
                if text:
                    frame = frame[
                        frame[col].astype(str).str.contains(text, case=False, na=False)
                    ]

        pattern = (self._search_input.value or "").strip()
        if pattern:
            frame = frame.search(pattern)

        return frame

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def _render(self, frame: Any) -> None:
        """Display *frame* as a sortable, filterable, scrollable HTML table.

        Uses PowerTable's local filter/sort JS injected into a fresh iframe so
        that ``DOMContentLoaded`` fires correctly inside Jupyter output cells.
        Falls back to plain ``_ipy_display`` if the HTML compiler is unavailable.
        """
        with self._output:
            clear_output(wait=True)
            if frame is None or (hasattr(frame, 'empty') and frame.empty):
                print("No rows match the current filters.")
                return
            try:
                from tts_html_utils.core.compiler import HtmlCompiler
                from IPython.display import HTML as _IpyHTML
                table = frame.power_table(add_filters='local', add_sorting='local')
                compiler = HtmlCompiler(title='Log Explorer')
                compiler.add_body_component(table)
                iframe_html = compiler.render_to_jnb_iframe(height='600px')
                _ipy_display(_IpyHTML(iframe_html))
            except Exception:
                _ipy_display(frame)

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
