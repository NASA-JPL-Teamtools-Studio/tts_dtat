"""Common functions for charts"""
import datetime as dt

import tts_dtat.palette as palette
from tts_dtat.types import CustomizedMarker, CustomizedTrace
import tts_dtat.datachecker as datachecker


def get_plotly_marker_values(customize_dict: CustomizedTrace) -> CustomizedMarker:
    """
    Extracts and defaults marker configuration values for a Plotly trace.

    Args:
        customize_dict (CustomizedTrace): A dictionary containing customization options
            for the trace, such as color, symbol, size, and colorscale.

    Returns:
        CustomizedMarker: A dictionary formatted for use as a Plotly marker configuration,
            containing keys for size, symbol, color, colorscale, showscale, and line properties.
    """
    keys = customize_dict.keys()
    if "color" not in keys or customize_dict["color"] is None:
        customize_dict["color"] = "#000000"
    if "symbol" not in keys or customize_dict["symbol"] is None:
        customize_dict["symbol"] = "circle"
    
    # Default size (Increased to 8 for better visibility)
    if "size" not in keys or customize_dict["size"] is None:
        customize_dict["size"] = 8
        
    if "z_var" not in keys:
        customize_dict["z_var"] = None
    if "showscale" not in keys or not isinstance(customize_dict["showscale"], bool):
        customize_dict["showscale"] = False
    if "colorscale" not in keys or customize_dict["colorscale"] is None:
        customize_dict["colorscale"] = palette.make_discrete_colorscale([], [])

    # --- RESOLVE MARKER LINE WIDTH ---
    # 1. Get user's line config (if any)
    user_line_config = customize_dict.get("line", {}) or {}
    
    # 2. Check for explicit marker line width in two places:
    #    a) Root level: customize_dict['marker_line_width']
    #    b) Line dict:  customize_dict['line']['marker_line_width']
    explicit_width = customize_dict.get("marker_line_width")
    if explicit_width is None:
        explicit_width = user_line_config.get("marker_line_width")

    # 3. Determine Final Width
    if explicit_width is not None:
        # If user explicitly set it (even to 0.1), use it.
        marker_line_width = explicit_width
    elif "width" in user_line_config:
        # Fallback 1: Inherit from trace line width
        marker_line_width = user_line_config["width"]
    else:
        # Fallback 2: Defaults
        if customize_dict["z_var"] is not None:
            marker_line_width = 0
        else:
            marker_line_width = 1.0 

    return {
        "size": customize_dict["size"],
        "symbol": customize_dict["symbol"],
        "color": customize_dict["color"],
        "colorscale": customize_dict["colorscale"],
        "showscale": customize_dict["showscale"],
        "line": {
            "width": marker_line_width,
            "color": palette.get_line_color(customize_dict["color"]),
        }
    }

def make_colorbar_dict(data, z_var, z_vals, color) -> dict:
    """
    Creates a dictionary defining the properties of a Plotly colorbar.

    Determines the appropriate tick values and text based on the data type of the
    Z-axis variable (time, discrete bins, or categorical strings).

    Args:
        data (pd.DataFrame): The DataFrame containing the data.
        z_var (str): The name of the column used for the Z-axis (color dimension).
        z_vals (str): The name of the column containing the numeric values for the Z-axis.
        color (list or str): The color configuration, which can be a list of bins or a single color.

    Returns:
        dict: A dictionary containing title, tickmode, tickvals, and ticktext for the colorbar.
    """
    colorbar = {
        "title": z_var
    }
    if z_var is not None:
        if datachecker.is_time_type(z_var) and 'elapsed_seconds' in data.columns:
            es_min = data["elapsed_seconds"].min()
            es_max = data["elapsed_seconds"].max()
            es_step = (es_max - es_min) / 6
            colorbar['tickmode'] = 'array'
            colorbar['tickvals'] = [
                es_min, 
                es_min + (es_step * 1),
                es_min + (es_step * 2),
                es_min + (es_step * 3),
                es_min + (es_step * 4),
                es_min + (es_step * 5),
                es_max
            ]
            colorbar['ticktext'] = [elapsed_seconds_to_dt_str(d) for d in colorbar['tickvals']]
        elif isinstance(color, list):
            bin_min = data[z_vals].min()
            bin_max = data[z_vals].max()
            colorbar['tickmode'] = 'array'
            colorbar['tickvals'] = ['{:0.3f}'.format(bin_min)]
            for i, b in enumerate(color):
                if i % 2 == 0:
                    colorbar['tickvals'].append('{:0.3f}'.format(b[0] * bin_max))
            colorbar['tickvals'].append('{:0.3f}'.format(bin_max))
        elif data.dtypes[z_var] in ['object', 'string']:
            colorbar['tickmode'] = 'array'
            colorbar['tickvals'] = data['z_numeric'].unique()
            colorbar['ticktext'] = data[z_var].unique()
    return colorbar

def elapsed_seconds_to_dt_str(es_flt) -> str:
    """
    Converts elapsed seconds since a reference epoch (2018-01-01) to a formatted string.

    Args:
        es_flt (float): The number of seconds elapsed since January 1, 2018.

    Returns:
        str: A datetime string formatted as '%Y-%jT%H:%M:%S'.
    """
    es_dt = dt.datetime(2018, 1, 1) + dt.timedelta(seconds = es_flt)
    es_str = es_dt.strftime('%Y-%jT%H:%M:%S')
    return es_str