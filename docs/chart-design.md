# Chart design guidance for complex telemetry plots

This document is a draft design reference for `tts_dtat` plots. It is intentionally open to review and challenge. It records principles that should guide plotting defaults and warnings before they become hard validation rules.

## Core principles

1. Prefer one conceptual comparison per subplot.
2. Keep telemetry that belongs to the same operational family together when that improves interpretation, even when the channels use different units.
3. Prefer one visible y-axis on the left and one on the right. Additional scales are supported for advanced cases, but they increase cognitive load and should produce a warning.
4. Label each visible scale with a human-readable quantity and unit where metadata is available.
5. Keep trace identity in the plot key and tooltip; axis labels should identify the scale, not repeat every channel mnemonic.
6. Treat color as a supporting identity cue, not the only identity cue.
7. Keep stacked telemetry panels aligned on a shared time axis.
8. A static export should remain understandable without requiring hover interaction.
9. Reserve layout space for figure titles, legends, subplot titles, axis titles, and tick labels so they do not overlap.

## Multiple scales

Multiple y-axes are appropriate only when the comparison is useful and the scales can be associated unambiguously with their traces. A second axis should normally be on the right. More than two axes may be necessary for expert analysis, but the result should be treated as an advanced layout and called out to the user.

When a plot becomes difficult to read, prefer another aligned subplot over adding more floating axes. The library should warn before silently producing a layout with more than two overlaid scales.

## Label responsibilities

- **Axis title:** quantity and unit represented by the scale.
- **Tick labels:** numeric or enumerated values on that scale.
- **Plot key:** trace/channel identity.
- **Tooltip:** exact channel, value, unit, and timestamp.
- **Figure/subplot title:** context and conceptual grouping.

These elements complement one another; one should not be overloaded with all of the others' responsibilities.

## Accessibility and export

Pair color with a plot-key entry, line style, marker, direct label, or axis association. Use consistent units and terminology. Check dense figures at their intended exported size, not only in an interactive browser.

## Primary references

- [Plotly: Multiple Y-Axes](https://plotly.com/python/multiple-axes/)
- [Plotly: Axes](https://plotly.com/python/axes/)
- [Matplotlib: Axis labels](https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.set_ylabel.html)
- [Matplotlib: Shared subplots](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html)
- [NASA Open MCT: Telemetry](https://nasa.github.io/openmct/docs/concepts/telemetry/)
- [NASA Open MCT: Plot plugin](https://nasa.github.io/openmct/docs/plugins/plot/)
- [NIST/SEMATECH: Graphical Methods](https://www.itl.nist.gov/div898/handbook/eda/section3/graphdes.htm)
- [IBM Carbon: Chart anatomy](https://carbondesignsystem.com/data-visualization/chart%20anatomy/)
- [Stephen Few: Dual-Scaled Axes in Graphs](https://www.perceptualedge.com/articles/visual_business_intelligence/dual-scaled_axes.pdf)
- [AGU: Graphics guidance](https://www.agu.org/Publish-with-AGU/Publish/Author-Resources/Graphics)
- [Nature: Reporting standards](https://www.nature.com/nature-portfolio/editorial-policies/reporting-standards)

## Review status

Draft. Maintainers and mission users should challenge these principles with concrete telemetry examples before they become mandatory validation policy.
