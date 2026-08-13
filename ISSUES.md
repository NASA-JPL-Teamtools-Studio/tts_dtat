# Open Issues

## Issue 1: FigureWidget Width Not Responsive to Notebook Cell

**Status**: Open  
**Priority**: Medium  
**Component**: `PlotOrchestrator.interactive()`

### Description
The interactive FigureWidget created by `PlotOrchestrator.interactive()` does not take up the full width of the notebook cell, unlike the static plot created by `PlotOrchestrator.plot()`. The widget appears narrower than the cell width regardless of how the notebook window is sized.

### Current Behavior
- Static plot (`plot().show()`) fills the notebook cell width
- Interactive widget (`interactive()`) is narrower than the cell
- Setting `width=None` or `autosize=True` does not fix the issue

### Workaround
Pass `figure_width` parameter when creating PlotOrchestrator:
```python
orch = PlotOrchestrator(
    data, y_vars,
    n_points=500,
    x_var="timestamp",
    figure_width=1200  # Workaround
)
```

### Root Cause
Plotly's FigureWidget in Jupyter has different default width behavior than regular Figure objects. The widget doesn't inherit the responsive width behavior of the static plot.

### Suggested Fix
- Investigate FigureWidget CSS/layout options
- Consider using Plotly's responsive width settings
- Possibly add a `responsive_width` parameter to PlotOrchestrator

---

## Issue 2: LTTB Callbacks Stop Working After Home Button

**Status**: Open  
**Priority**: High  
**Component**: `PlotOrchestrator.interactive()` zoom/pan callbacks

### Description
When using the interactive widget with zoom/pan functionality, the LTTB downsampling callbacks work correctly until the user clicks the home button (double-click to reset zoom). After clicking home, subsequent zoom/pan interactions no longer trigger the LTTB downsampling callback, and the plot becomes unresponsive to zoom changes.

### Current Behavior
1. User creates interactive widget: ✓ Works
2. User zooms to a time range: ✓ LTTB downsampling callback fires, data updates
3. User clicks home button: ✓ Full dataset restored
4. User tries to zoom again: ✗ Callback doesn't fire, plot doesn't update

### Root Cause
The callback registration mechanism (`fw.layout.on_change()`) is not being triggered by Jupyter's widget event system. Investigation shows:
- No callback logs appear even on initial zoom (before home button)
- The callback function is never called by Jupyter
- This suggests the `layout.on_change()` registration isn't working as expected in Jupyter's FigureWidget

### Attempted Fixes
- Removed aggressive `_prev_autorange` state guard
- Tried switching from `layout.on_change()` to `xaxis.observe()` (incompatible with test environment)
- Added debug logging (no logs appear, confirming callback isn't triggered)

### Suggested Fix
- Investigate alternative callback mechanisms for Jupyter FigureWidget
- Consider using JavaScript callbacks via Plotly's `relayout_data`
- Evaluate if this is a Jupyter/ipywidgets version compatibility issue
- Possibly implement zoom detection via polling or alternative event system

### Notes
- Static plots work perfectly
- The zoom/pan UI appears to work (axes update) but no data points are shown
- This is likely a Jupyter environment issue, not a code logic issue
