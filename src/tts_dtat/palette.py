"""Default color palette for charts"""
from typing import Optional, Tuple, cast

"""Default accessible palette"""
DEFAULT_BG_COLOR = "#fefefe"
DEFAULT_AXIS_LINE_COLOR = "#DDE1E7"
default_colors = {
    "#0078AF": {"line_color": "#0073FF", "name": "Dark-Blue"},
    "#B85146": {"line_color": "#CA243C", "name": "Dark-Red"},
    "#C99E44": {"line_color": "#FFE100", "name": "Dark-Yellow"},
    "#8D4485": {"line_color": "#FC5E24", "name": "Dark-Purple"},
    "#717171": {"line_color": "#FFE100", "name": "Dark-Grey"},
    "#459D4C": {"line_color": "#459D4C", "name": "Dark-Green"},

    "#3498DB": {"line_color": "#3498DB", "name": "Med-Blue"},
    "#E26352": {"line_color": "#E26352", "name": "Med-Red"},
    "#E3B740": {"line_color": "#E3B740", "name": "Med-Yellow"},
    "#A55A10": {"line_color": "#A55A10", "name": "Med-Purple"},
    "#8B8B8B": {"line_color": "#8B8B8B", "name": "Med-Grey"},
    "#4CBB51": {"line_color": "#4CBB51", "name": "Med-Green"},

    "#51B0DA": {"line_color": "#51B0DA", "name": "Light-Blue"},
    "#E26352": {"line_color": "#E26352", "name": "Light-Red"},
    "#FFCE59": {"line_color": "#FFCE59", "name": "Light-Yellow"},
    "#B072B7": {"line_color": "#B072B7", "name": "Light-Purple"},
    "#A5A5A5": {"line_color": "#A5A5A5", "name": "Light-Grey"},
    "#66D46E": {"line_color": "#66D46E", "name": "Light-Green"}
}


def get_default_colors():
    """Returns a list of the hex values with default colors

    Returns:
        list: A list of string hex color codes available in the default palette.
    """
    return list(default_colors.keys())


def get_default_color_options():
    """Creates properly formatted dropdown labels for the default color options.

    Returns:
        list: A list of dictionaries, where each dictionary represents an option
              containing 'label', 'value', 'className', and 'title'.
    """
    labels = []
    for color in default_colors.keys():
        labels.append(
            {
                "label": "",
                "value": color,
                "className": str(
                    default_colors[color]["name"]
                    + "-color-option color-swatch-option fa fa-circle"
                ),
                "title": default_colors[color]["name"],
            }
        )
    return labels


def get_default_shape_options():
    """Creates properly formatted dropdown labels for the default shape options.

    Returns:
        list: A list of dictionaries, where each dictionary represents a shape option
              containing 'label', 'value', 'className', and 'title'.
    """
    labels = []
    for shape in [
        ["circle", "circle-icon-option"],
        ["circle-open", "circle-open-icon-option"],
        ["square", "square-icon-option"],
        ["square-open", "square-open-icon-option"],
        ["diamond", "diamond-icon-option"],
        ["diamond-open", "diamond-open-icon-option"],
        ["triangle-up", "triangle-up-icon-option"],
        ["triangle-up-open", "triangle-up-open-icon-option"],
        ["asterisk-open", "fa fa-asterisk"],
        ["cross-thin-open", "fa fa-plus"],
    ]:
        labels.append(
            {
                "label": "",
                "value": shape[0],
                "className": str("color-swatch-option fa " + shape[1]),
                "title": shape[0],
            }
        )
    return labels


def get_line_color(color):
    """Tries to return a related line color.
    If not found, returns the color again.

    Args:
        color (str): The hex code of the fill color.

    Returns:
        str: The hex code of the corresponding line color, or the original color
             if no mapping is found.
    """
    if (
        color is None
        or not isinstance(color, str)
        or color not in default_colors.keys()
    ):
        return color
    return default_colors[color]["line_color"]


def pop_next_color(
    unassigned_colors=None,
) -> Tuple[str, list]:
    """Retrieves the next available color from the unassigned list.
    If the list is empty or None, it resets with default colors.

    Args:
        unassigned_colors (list, optional): The current list of available color hex codes.

    Returns:
        Tuple[str, list]: A tuple containing the popped color (str) and the
                          updated list of unassigned colors.
    """
    if unassigned_colors is None or not unassigned_colors:
        unassigned_colors = list(default_colors)
    return unassigned_colors.pop(0), unassigned_colors


def remove_unseen_bins(color_set: list, custom_divisions: list):
    """Removes bins (colors and divisions) that fall outside the normalized 0-1 range.
    Ensures that the lowest remaining bin starts at 0.

    Args:
        color_set (list): A list of colors assigned to bins.
        custom_divisions (list): A list of normalized starting points (0-1) for each bin.

    Returns:
        tuple: A tuple containing the filtered (color_set, custom_divisions).
    """
    combined = []
    for i, c in enumerate(color_set):
        combined.append([custom_divisions[i], c])
    combined.sort()
    low_bin = {"loc": -1, "val": None}
    for i, b in enumerate(combined):
        # remove any high bins that wouldn't be shown
        if b[0] > 1:
            combined.pop(i)
        # remove any low bins that wouldn't be shown; only one bin starting at or below zero should be kept
        elif b[0] <= 0:
            if low_bin["val"] is None:  # first low bin found
                low_bin = {"loc": i, "val": b[0]}
            else:  # there is already a low bin
                if low_bin["val"] < b[0]:
                    combined.pop(low_bin["loc"])
                    low_bin["val"] = b[0]
                    low_bin["loc"] = i - 1
                else:
                    combined.pop(i)
    # force the lowest bin left to start at 0
    if low_bin["loc"] > -1:
        combined[low_bin["loc"]][0] = 0
    # de-aggregate bins
    color_set = [b[1] for b in combined]
    custom_divisions = [b[0] for b in combined]
    return color_set, custom_divisions


def clean_and_sort_colorscale(
    color_set: list, custom_divisions: list, data_min=0, data_max=1
):
    """Cleans, sorts, and normalizes the colorscale bins based on data ranges.

    Args:
        color_set (list): The list of colors.
        custom_divisions (list): The list of raw start values for the bins.
        data_min (float, optional): The minimum value of the dataset. Defaults to 0.
        data_max (float, optional): The maximum value of the dataset. Defaults to 1.

    Returns:
        tuple: A tuple containing the processed (color_set, custom_divisions) lists,
               where divisions are normalized to 0-1.
    """
    # clean out bins with no start point
    for i, c in enumerate(color_set):
        if custom_divisions[i] is None or len(str(custom_divisions[i])) < 1:
            color_set.pop(i)
            custom_divisions.pop(i)
    # normalize any negative bin division values by shifting everything so the data minimum is 0
    if len(custom_divisions) > 0:
        custom_divisions = [
            ((d - data_min) / (data_max - data_min)) for d in custom_divisions
        ]
    color_set, custom_divisions = remove_unseen_bins(color_set, custom_divisions)
    return color_set, custom_divisions


def make_discrete_colorscale(
    color_set: list, custom_divisions: list, data_min=0, data_max=1
):
    """Creates a discrete Plotly colorscale based on specified colors and division points.

    Args:
        color_set (list): A list of color codes.
        custom_divisions (list): A list of values where each color bin starts.
        data_min (float, optional): The minimum value in the data range. Defaults to 0.
        data_max (float, optional): The maximum value in the data range. Defaults to 1.

    Returns:
        list: A list of tuples compatible with Plotly's colorscale format, or "jet"
              if no colors are provided.
    """
    color_set, custom_divisions = clean_and_sort_colorscale(
        color_set, custom_divisions, data_min, data_max
    )
    custom_divisions.append(1)  # add ending bin value
    colorscale = []
    num_colors = len(color_set)
    if num_colors == 0:
        return "jet"  # default rainbow colorscale
    for color in color_set:  # Loop over the color sets
        colorscale.append((custom_divisions.pop(0), color))  # start color block
        colorscale.append((custom_divisions[0] - 0.001, color))  # end color block
    colorscale[-1] = (1, colorscale[-1][1])
    colorscale.insert(0, (0, colorscale[0][1]))
    return colorscale

def make_discrete_colorscale_from_data(
        color_set: list, bin_lower_bounds: list, color_data
):
    """Generates a discrete colorscale by deriving min/max values directly from the data.

    Args:
        color_set (list): A list of color codes.
        bin_lower_bounds (list): A list of values where each color bin starts.
        color_data (pd.DataFrame): The dataframe containing the 'value' column to determine range.

    Returns:
        list: A discrete Plotly colorscale.
    """
    datamin = color_data.min()['value']
    datamax = color_data.max()['value']
    return make_discrete_colorscale(
        color_set=color_set,
        custom_divisions=bin_lower_bounds,
        data_min=datamin,
        data_max=datamax,
        )