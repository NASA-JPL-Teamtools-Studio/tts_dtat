"""
Plotly and other functions for a stacked plot graph

This version makes an arrow for each event
"""
from typing import TYPE_CHECKING, Optional, Sequence, List, Dict, Tuple, Union
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import tts_dtat.dtatdata as dtatdata
import tts_dtat.datachecker as datachecker
import tts_dtat.mouseover_maker as mouseover_maker
import tts_dtat.commonchartfuncs as common
import tts_dtat.palette as palette
from tts_dtat.types import CustomizationOptions

import warnings
warnings.filterwarnings('ignore')


def make_stacked_graph(
    data: "pd.DataFrame",
    y_vars: Sequence[Sequence[str]],
    x_var: str = "scet",
    z_var: Optional[str] = None,
    multi_axis: bool = False,
    plot_lines: bool = True,
    figure_title: str = None,
    y_axis_title: Union[str, List[str]] = None,
    customize_dict: Optional[CustomizationOptions] = None,
    unassigned_colors: Optional[List] = None,
    background_color: str = '#fcfcfc',
    axis_line_color: str = '#555555',
    figure_margins: dict = None,
    figure_height: int = None,
    figure_width: int = None,
    events: Dict[str, List[Tuple]] = {},
    event_line: bool = None,
    doy: bool = True,
    global_y_label: bool = False,
):
    """
    Creates a stacked graph with multiple subplots using Plotly.

    Args:
        data (pd.DataFrame): The pandas DataFrame containing the data to plot.
        y_vars (Sequence[Sequence[str]]): A list of lists of variable names to plot.
        x_var (str, optional): The name of the column to use for the X-axis. Defaults to "scet".
        z_var (Optional[str], optional): The name of the column to use for the Z-axis (color scale).
        multi_axis (bool, optional): If True, creates multiple Y-axes for traces within the same subplot.
        plot_lines (bool, optional): If True, plots lines and markers. If False, plots markers only.
        figure_title (str, optional): The title of the figure.
        y_axis_title (Union[str, List[str]], optional): The title(s) for the Y-axis. Can be a single string (applied to all or used globally), or a list of strings (one per subplot).
        customize_dict (Optional[CustomizationOptions], optional): Customization options for specific traces.
        unassigned_colors (Optional[List], optional): A list of colors to use for traces without assignments.
        background_color (str, optional): The background color of the plot.
        axis_line_color (str, optional): The color of the axis lines.
        figure_margins (dict, optional): Margins for the figure (l, r, t, b).
        figure_height (int, optional): The height of the figure in pixels.
        figure_width (int, optional): The width of the figure in pixels.
        events (Dict[str, List[Tuple]], optional): A dictionary of events to annotate.
        event_line (bool, optional): If True, draws a vertical line at the event time.
        doy (bool, optional): If True and x_var is a time type, formats the X-axis ticks using dates.
        global_y_label (bool, optional): If True, treats y_axis_title as a single label for the whole figure.

    Returns:
        tuple: (graph, unassigned_colors, marker_values, visible_traces)
    """
    graph = go.Figure()
    graph.update_layout(
        plot_bgcolor=background_color,
        xaxis=dict(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3, # BOLD DEFAULT
        ),
        yaxis=dict(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3, # BOLD DEFAULT
        ),
    )
    
    visible_traces = []
    marker_values = {}
    if customize_dict is not None and len(customize_dict) > 0:
        for t in customize_dict.keys():
            marker_values[t] = common.get_plotly_marker_values(customize_dict[t])

    if unassigned_colors is None:
        unassigned_colors = palette.get_default_colors()

    num_subplots = len(y_vars)

    # Adjust margins if global label is present to avoid cutoff
    default_left_margin = 100 if global_y_label else 75
    figure_margins = dict(l=default_left_margin, b=100, t=50, r=75) if figure_margins is None else figure_margins

    if figure_height is None:
        figure_height = max(450, 200 * num_subplots + 2)

    if y_vars is not None and len(y_vars) > 0:
        graph = make_subplots(num_subplots, cols=1, shared_xaxes=True, vertical_spacing = 0.2).update_layout(
            plot_bgcolor=background_color,
            xaxis=dict(
                showline=True,
                showgrid=True,
                gridcolor=axis_line_color,
                zerolinecolor=axis_line_color,
                linecolor=axis_line_color,
                linewidth=3, # BOLD DEFAULT
            ),
            yaxis=dict(
                showline=True,
                showgrid=True,
                gridcolor=axis_line_color,
                zerolinecolor=axis_line_color,
                linecolor=axis_line_color,
                linewidth=3, # BOLD DEFAULT
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            height=figure_height
        )

        # determine if plot lines should be shown
        line_mode = "lines+markers" if plot_lines else "markers"

        # Only convert to elapsed_seconds if x_var is not a time type or if explicitly requested
        x_elapsed_seconds = False 
        data, temp = dtatdata.column_values_from_state(data, x_var, time="scet", elapsed_seconds=x_elapsed_seconds)
        data, z_vals = dtatdata.column_values_from_state(data, z_var, time="scet", elapsed_seconds=True)
        
        # Ensure z_vals column exists if we need it
        if z_var is not None and z_vals not in data.columns:
             if "z_numeric" in data.columns:
                 z_vals = "z_numeric"

        vertical_spacing = 0.2 / num_subplots
        subplot_height = (1.0 - vertical_spacing * (num_subplots - 1)) / num_subplots
        
        trace_num = 1
        x_domain_start = 0

        for subplot_num, plot_y_vars in enumerate(y_vars, start=1):

            # setting to -.06 so it will be incremented to zero
            y_axis_position = -0.1
            y_domain_start = (num_subplots - subplot_num + 1) / num_subplots
            domain = [y_domain_start - subplot_height, y_domain_start]
            y_axis_units = dtatdata.get_units_from_states(data, plot_y_vars)

            # --- DETERMINE TITLE FOR THIS SPECIFIC SUBPLOT ---
            current_subplot_title = None

            if global_y_label:
                # If global label is on, subplot titles are suppressed
                current_subplot_title = ""
            elif isinstance(y_axis_title, (list, tuple)):
                # If list, grab the one matching this subplot index
                if (subplot_num - 1) < len(y_axis_title):
                    current_subplot_title = y_axis_title[subplot_num - 1]
            elif isinstance(y_axis_title, str):
                # If string, use it for all (legacy behavior)
                current_subplot_title = y_axis_title
            
            # If no title was set above, auto-generate from variables and units
            if current_subplot_title is None:
                if len(plot_y_vars) == 1:
                    current_subplot_title = f'{plot_y_vars[0]} ({y_axis_units[0]})' if y_axis_units is not None else f'{plot_y_vars[0]}'
                else:
                    current_subplot_title = f'{", ".join(plot_y_vars)} ({y_axis_units if len(y_axis_units) == 1 else ", ".join(y_axis_units)})' if y_axis_units is not None else f'{", ".join(plot_y_vars)}'
            # -------------------------------------------------

            y_axis_layout_name = "yaxis{}".format(subplot_num)
            title_color = "#000000"

            for y_val in plot_y_vars:
            
                if y_val not in visible_traces:
                    visible_traces.append(y_val)
                data_slice = dtatdata.get_data_from_state(data, y_val)
                
                data_slice = data_slice.copy()
                
                try:
                    data_slice.loc[:, "value"] = pd.to_numeric(data_slice["value"])
                except (ValueError, TypeError):
                    pass # Keep as is if conversion fails

                if y_val not in marker_values.keys():
                    if z_var is not None and z_var in data.columns:
                        if z_vals in data.columns:
                             data_slice.loc[:, z_vals] = data.loc[data_slice.index, z_vals]
                             color = data_slice[z_vals]
                        else:
                             color = "#000000"
                        line_color = "#000000"
                    else:
                        color, unassigned_colors = palette.pop_next_color(
                            unassigned_colors
                        )
                        if color in palette.default_colors.keys():
                            line_color = palette.default_colors[color]["line_color"]
                        else:
                            line_color = color
                    colorbar = common.make_colorbar_dict(data, z_var, z_vals, color)
                    marker_values[y_val] = {
                        "size": 8, # BOLDER DEFAULT (was 5)
                        "symbol": "circle",
                        "color": color,
                        "colorscale": palette.make_discrete_colorscale([], []),
                        "showscale": (z_var is not None),
                        "line": {
                            "width": 0.5 if z_var is None else 0,
                            "color": line_color,
                        },
                        "colorbar": colorbar
                    }
                else:
                    if z_var is not None and z_var in data.columns:
                        if z_vals in data.columns:
                             data_slice.loc[:, z_vals] = data.loc[data_slice.index, z_vals]
                             marker_values[y_val]["color"] = data_slice[z_vals]
                        marker_values[y_val]["colorbar"] = common.make_colorbar_dict(data, z_var, z_vals, marker_values[y_val]["colorscale"])
                
                if multi_axis:
                    y_axis_position += 0.1
                    title_color = marker_values[y_val]["line"]["color"]
                    y_axis_units = dtatdata.get_unit_from_state(data, y_val)
                    
                    # Generate specific title for multi-axis
                    multi_axis_title = f'{y_val} ({y_axis_units})' if y_axis_units is not None else f'{y_val}'
                    y_axis_layout_name = "yaxis{}".format(trace_num)
                
                # Determine final title to use for this axis
                final_axis_title = multi_axis_title if multi_axis else current_subplot_title

                graph.update_layout(
                    {
                        y_axis_layout_name: {
                            "title": {
                                "text": final_axis_title,
                                "font": {"color": title_color},
                            },
                            "position": max(y_axis_position, 0),
                            "anchor": "free",
                            "tickfont": {"color": title_color},
                            "domain": domain,
                            "overlaying": "y{}".format(subplot_num),
                        }
                    }
                )

                # --- START: Handle Overrides for Trace Mode and Line Shape ---
                trace_customs = customize_dict.get(y_val, {}) if customize_dict else {}
                trace_mode = trace_customs.get("mode", line_mode)
                trace_line = trace_customs.get("line", {}).copy()
                if "width" not in trace_line:
                    trace_line["width"] = 3
                
                if "color" not in trace_line and "color" in marker_values[y_val]:
                      mv_color = marker_values[y_val]["color"]
                      if isinstance(mv_color, str):
                          trace_line["color"] = mv_color
                # --- END: Handle Overrides ---

                graph.add_trace(
                    go.Scatter(
                        x=data_slice[x_var],
                        y=data_slice["value"],
                        name=y_val,
                        meta=mouseover_maker.make_meta(z_var, data_slice),
                        hovertemplate=mouseover_maker.ht_X_Y_Z_time_names(
                            xaxis=x_var, yaxis=y_val, zaxis=z_var
                        ),
                        mode=trace_mode,
                        line=trace_line,
                        showlegend=True,
                        opacity=0.7,
                        marker=marker_values[y_val],
                    ),
                    row=subplot_num,
                    col=1,
                )
                trace_num += 1

                #EVENT PLOTTING (ARROW)
                for e in events.get(y_val, []):
                    if y_val not in data_slice.columns:
                        data, temp = dtatdata.column_values_from_state(data, y_val, time="scet", elapsed_seconds=True)
                        
                    if datachecker.is_time_type(x_var):
                        event_time = e[0]
                        if isinstance(event_time, str):
                            event_time = datetime.strptime(event_time, "%Y-%jT%H:%M:%S.%f")
                            
                        if len(e) == 2:
                            e = (event_time, e[1])
                        else:
                            e = (event_time, e[1], e[2])
                                                                        
                        if event_line:
                            graph.add_vline(
                                x=e[0],
                                line_width=3, 
                                line_color="black", 
                                row=subplot_num, 
                                col=1
                            )
                        
                        graph.add_annotation(
                            x = e[0], 
                            yref = f'y{subplot_num} domain' if subplot_num > 1 else 'y domain',
                            ayref=f'y{subplot_num} domain' if subplot_num > 1 else 'y domain',
                            y=0, 
                            ay = -0.1,
                            text= e[1],
                            hovertext=e[2] if len(e) > 2 else e[1],
                            arrowhead = 1,
                            showarrow = True
                        )

            x_domain_start = max(x_domain_start, y_axis_position)
        

        if multi_axis:
            for trace_num, trace in enumerate(graph.data, start=1):
                trace.yaxis = "y{}".format(trace_num)
            graph.update_xaxes(
                domain=[x_domain_start, 1], anchor="y{}".format(trace_num)
            )

        graph.update_xaxes(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3
        )
        if doy and datachecker.is_time_type(x_var):
            graph.update_xaxes(
                tickformat='%Y-%m-%d %H:%M:%S',
                type='date'
            )

        graph.update_yaxes(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3
        )

        # --- GLOBAL LABEL ANNOTATION ---
        if global_y_label and isinstance(y_axis_title, str):
            graph.add_annotation(
                x=-0.08, 
                y=0.5,
                xref="paper",
                yref="paper",
                text=y_axis_title,
                textangle=-90,
                showarrow=False,
                font=dict(color="#000000", size=14)
            )

        graph.update_layout(
            {
                'title': {'text': figure_title},
                'font_family': 'Arial',
                'margin': figure_margins
            }
        )

        x_unit = dtatdata.get_unit_from_state(data, x_var)
        graph.update_xaxes(
            title_text=f'{x_var} ({x_unit})' if x_unit is not None else f'{x_var}'
        )

        if figure_width is not None:
            graph.update_layout({'width': figure_width})
        
        return graph, unassigned_colors, marker_values, visible_traces

    return graph, {}, {}, []


def make_diff_graph(
    data: "pd.DataFrame",
    y1: str,
    y2: str,
    y_axis_units: Sequence[str] = [], 
    x_var: str = "scet",
    figure_title: str = None,
    unassigned_colors: Optional[List] = None, 
    background_color: str = '#fcfcfc',
    axis_line_color: str = '#555555',
    figure_margins: dict = None,
    figure_height: int = None,
    figure_width: int = None,
):
    graph = go.Figure()
    graph.update_layout(
        plot_bgcolor=background_color,
        xaxis=dict(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
        ),
        yaxis=dict(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
        ),
    )
    
    visible_traces = []
    marker_values = {}

    if unassigned_colors is None:
        unassigned_colors = palette.get_default_colors()

    num_subplots = 1

    figure_margins = dict(l=75, b=100, t=50, r=75) if figure_margins is None else figure_margins

    if figure_height is None:
        figure_height = max(450, 200 * num_subplots + 2)

    graph = make_subplots(num_subplots, cols=1, shared_xaxes=True, vertical_spacing = 0.2).update_layout(
        plot_bgcolor=background_color,
        xaxis=dict(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
        ),
        yaxis=dict(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        height=figure_height
    )

    data, temp = dtatdata.column_values_from_state(data, x_var, time="scet", elapsed_seconds=True)

    y1_data_slice = dtatdata.get_data_from_state(data, y1)
    y2_data_slice = dtatdata.get_data_from_state(data, y2)

    graph.add_trace(go.Scatter(
        x = y1_data_slice[x_var], 
        y = y1_data_slice["value"], 
        fill='tozeroy',
        name=y1,
        meta=mouseover_maker.make_meta(None, y1_data_slice),
        hovertemplate=mouseover_maker.ht_X_Y_Z_time_names(
            xaxis=x_var, yaxis=y1, zaxis=None
        ),
    ))
    graph.add_trace(go.Scatter(
            x = y2_data_slice[x_var], 
            y = y2_data_slice["value"], 
            fill='tozeroy',
            name=y2,
            meta=mouseover_maker.make_meta(None, y2_data_slice),
            hovertemplate=mouseover_maker.ht_X_Y_Z_time_names(
                xaxis=x_var, yaxis=y2, zaxis=None
            ),
        ))

    graph.update_layout(showlegend=False)
    graph.update_layout(xaxis_title = x_var, title = f"Difference between {y1} and {y2}")

            
    graph.update_xaxes(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
        )
    graph.update_yaxes(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
            title_text=f'{y1} diff {y2}'
        )

    graph.update_layout(
            {
                'title': {'text': figure_title},
                'font_family': 'Arial',
                'margin': figure_margins
            }
        )

    graph.update_xaxes(
            title_text=x_var
        )

    if figure_width is not None:
            graph.update_layout({'width': figure_width})
        
    return graph, unassigned_colors, marker_values, visible_traces


def make_bar_graph(
    data: "pd.DataFrame",
    y1: str,
    y2: str,
    y_axis_units: Sequence[str] = [], 
    x_var: str = "scet",
    figure_title: str = None,
    unassigned_colors: Optional[List] = None, 
    background_color: str = '#fcfcfc',
    axis_line_color: str = '#555555',
    figure_margins: dict = None,
    figure_height: int = None,
    figure_width: int = None,
    bar_width: int = 1,
    plot_lines: bool = False,
    bar_color: str= "#005500"
):
    graph = go.Figure()
    graph.update_layout(
        plot_bgcolor=background_color,
        xaxis=dict(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
        ),
        yaxis=dict(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
        ),
    )
    
    visible_traces = []
    marker_values = {}

    if unassigned_colors is None:
        unassigned_colors = palette.get_default_colors()

    num_subplots = 1

    figure_margins = dict(l=75, b=100, t=50, r=75) if figure_margins is None else figure_margins

    if figure_height is None:
        figure_height = max(450, 200 * num_subplots + 2)

    graph = make_subplots(num_subplots, cols=1, shared_xaxes=True, vertical_spacing = 0.2).update_layout(
        plot_bgcolor=background_color,
        xaxis=dict(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
        ),
        yaxis=dict(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        height=figure_height
    )

    data, temp = dtatdata.column_values_from_state(data, x_var, time="scet", elapsed_seconds=True)

    interpolated = dtatdata.column_values_from_state(data, y2, time=x_var)[0]
    
    y1_data_slice = dtatdata.get_data_from_state(interpolated, y1)
    y2_data_slice = dtatdata.get_data_from_state(interpolated, y2)

    diff_slice = y1_data_slice['value'] - y1_data_slice[y2]

    average_time = y1_data_slice[x_var].max() - y1_data_slice[x_var].min()
    if datachecker.is_time_type(x_var):
        average_time = average_time.total_seconds()

    graph.add_traces(go.Bar(x=y1_data_slice[x_var], y = diff_slice, 
                        width=average_time*bar_width,
                        marker_color= bar_color,
                        opacity=0.7
                    ))
        
    if plot_lines:
        graph.add_trace(go.Scatter(
            x = y1_data_slice[x_var], 
            y = y1_data_slice["value"], 
            name=y1,
            meta=mouseover_maker.make_meta(None, y1_data_slice),
            hovertemplate=mouseover_maker.ht_X_Y_Z_time_names(
                xaxis=x_var, yaxis=y1, zaxis=None
            )
        ))
        graph.add_trace(go.Scatter(
            x = y2_data_slice[x_var], 
            y = y2_data_slice["value"], 
            name=y2,
            meta=mouseover_maker.make_meta(None, y2_data_slice),
            hovertemplate=mouseover_maker.ht_X_Y_Z_time_names(
                xaxis=x_var, yaxis=y2, zaxis=None
            )
    ))
            
    graph.update_xaxes(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
        )
    graph.update_yaxes(
            showline=True,
            showgrid=True,
            gridcolor=axis_line_color,
            zerolinecolor=axis_line_color,
            linecolor=axis_line_color,
            linewidth=3,
            title_text=f'{y1} diff {y2}'
        )

    graph.update_layout(
            {
                'title': {'text': figure_title},
                'font_family': 'Arial',
                'margin': figure_margins
            }
        )

    graph.update_xaxes(
            title_text=x_var
        )

    if figure_width is not None:
            graph.update_layout({'width': figure_width})
        
    return graph, unassigned_colors, marker_values, visible_traces