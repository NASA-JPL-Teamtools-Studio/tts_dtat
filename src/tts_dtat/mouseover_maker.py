"""Functions to create a properly formatted hovertemplate string for plotly charts"""

import tts_dtat.datachecker as checker


def default_hovertemplate():
    """Return a hovertemplate string for a generic
    graph. This is the only hovertemplate method
    in this module that can used without setting meta
    to the output of make_meta()

    Returns:
        str: A generic hovertemplate string displaying X and Y values.
    """
    template = "X: %{x}<br>" "Y: %{y}<br>"
    return template


def make_meta(zvar, data, time_col="scet"):
    """Returns the meta value for a chart which should
    be set to allow the Z and time values to be reflected
    in hovertext tooltips made by this module.
    This method should be run on the data and set to meta before
    using any of the below 'ht' hovertemplate methods in this module.

    Args:
        zvar (str): The name of the column containing the Z-axis (color) data.
                    Can be None if no Z-axis is used.
        data (pd.DataFrame): The pandas DataFrame containing the chart data,
                             including the time column and the zvar column.
        time_col (str): Name of the time column.  Defaults to ``"scet"``.
                        Rows where this column is absent produce ``None`` for
                        the time entry in meta.

    Returns:
        list: A list of lists, where each inner list contains [z_value, time_value]
              corresponding to a row in the dataframe.
    """
    _tcol = time_col if time_col in data.columns else None
    n = len(data)
    meta = ""
    if zvar is not None and zvar in data.columns:
        if _tcol:
            meta = [[data[zvar].iloc[i], data[_tcol].iloc[i]] for i in range(n)]
        else:
            meta = [[data[zvar].iloc[i], None] for i in range(n)]
    else:
        if _tcol:
            meta = [[None, data[_tcol].iloc[i]] for i in range(n)]
        else:
            meta = [[None, None] for _ in range(n)]
    return meta


def ht_X_Y_Z_names(xaxis="X", yaxis="Y", zaxis="Z"):
    """Return a hovertemplate that uses the x and y
    axis names to label the values. The meta field
    should be set to the output of make_meta() for
    this hovertemplate to work properly.

    Args:
        xaxis (str, optional): The label for the X-axis. Defaults to "X".
        yaxis (str, optional): The label for the Y-axis. Defaults to "Y".
        zaxis (str, optional): The label for the Z-axis (color). Defaults to "Z".

    Returns:
        str: A formatted plotly hovertemplate string.
    """
    if checker.is_time_type(xaxis):
        x = "X: %{x|%Y-%jT%H:%M:%S.%L}"
    else:
        x = "X: %{x}"
    if checker.is_time_type(yaxis):
        y = "Y: %{y|%Y-%jT%H:%M:%S.%L}"
    else:
        y = "Y: %{y}"
    if checker.is_time_type(zaxis):
        z = "Z: %{meta[0]|%Y-%jT%H:%M:%S.%L}"
    else:
        z = "Z: %{meta[0]}"
    template = "X: " + xaxis + ": " + x + "<br>" + "Y: " + yaxis + ": " + y
    if zaxis is not None:
        template = template + "<br>" + "Z: " + zaxis + ": " + z
    template = template + "<extra></extra>"  # removes the trace tag
    return template


def ht_X_Y_Z_time_names(xaxis="X", yaxis="Y", zaxis="Z"):
    """Return a hovertemplate that uses the x and y
    axis names to label the values. The meta field
    should be set to the output of make_meta() for
    this hovertemplate to work properly.

    Args:
        xaxis (str, optional): The label for the X-axis. Defaults to "X".
        yaxis (str, optional): The label for the Y-axis. Defaults to "Y".
        zaxis (str, optional): The label for the Z-axis (color). Defaults to "Z".

    Returns:
        str: A formatted plotly hovertemplate string that includes a dedicated Time field.
    """
    if checker.is_time_type(xaxis):
        x = "%{x|%Y-%jT%H:%M:%S.%L}"
    else:
        x = "%{x}"
    if checker.is_time_type(yaxis):
        y = "%{y|%Y-%jT%H:%M:%S.%L}"
    else:
        y = "%{y}"
    if checker.is_time_type(zaxis):
        z = "%{meta[0]|%Y-%jT%H:%M:%S.%L}"
    else:
        z = "%{meta[0]}"
    time = "%{meta[1]|%Y-%jT%H:%M:%S.%L}"
    template = "X: " + xaxis + ": " + x + "<br>" + "Y: " + yaxis + ": " + y
    if zaxis is not None:
        template = template + "<br>" + "Z: " + zaxis + ": " + z
    template += "<br>Time: scet: " + time
    template = template + "<extra></extra>"  # removes the trace tag
    return template