"""Module containing type definitions"""
import collections
import json

try:
    # Try the standard library first (Python 3.8+)
    from typing import TypedDict
    from collections.abc import MutableMapping
except ImportError:
    # Fall back to the extension (Python 3.7)
    from typing_extensions import TypedDict
    from typing import MutableMapping

from typing import Any, Optional

class Line(TypedDict):
    """
    Defines the properties of a line in a plot.

    Attributes:
        width (float): The width of the line in pixels.
        color (str): The color of the line (hex code or name).
        shape (Optional[str]): The shape of the line (e.g., 'linear', 'hv', 'vh', 'spline').
    """
    width: float
    color: str
    shape: Optional[str]


class CustomizedTrace(TypedDict):
    """
    Defines customization options for a specific trace in a plot.

    Attributes:
        size (int): The size of the markers in the trace.
        symbol (str): The symbol used for markers (e.g., 'circle', 'square').
        color (str): The color of the markers or line.
        colorscale (str): The name of the color scale to use (e.g., 'Viridis').
        showscale (bool): Whether to display the color scale bar.
        line (Line): A dictionary defining the properties of the trace's line.
        z_var (Optional[str]): The name of the variable determining the Z-axis or color dimension.
        mode (str): The drawing mode for the trace (e.g., 'lines', 'markers', 'lines+markers').
        marker_line_width (float): Specific width for the marker border/stroke. Overrides line['width'] for markers.
    """
    size: int
    symbol: str
    color: str
    colorscale: str
    showscale: bool
    line: Line
    z_var: Optional[str]
    mode: str
    marker_line_width: float


class CustomizationOptions(MutableMapping[str, CustomizedTrace]):
    """
    A mutable mapping that associates trace names (str) with their corresponding
    CustomizedTrace configuration dictionaries.
    """
    pass


class CustomizedMarker(TypedDict):
    """
    Defines the properties of a marker in a plot.

    Attributes:
        size (int): The size of the marker.
        symbol (str): The shape of the marker (e.g., 'circle').
        color (str): The color of the marker.
        colorscale (str): The color scale applied to the marker.
        showscale (bool): Whether to show the color scale associated with the marker.
        line (Line): The outline properties of the marker.
    """
    size: int
    symbol: str
    color: str
    colorscale: str
    showscale: bool
    line: Line