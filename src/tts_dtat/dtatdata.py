"""Datacache object functions for a cache for data from one or more sources"""

import logging
import datetime
import warnings

import pandas as pd

import tts_dtat.datachecker as datachecker
import tts_dtat.datainterpolator as interpolate
#import appmgr.utilfuncs as utils
#import connectors.bin_connector as binc
#import connectors.csv_connector as csvc
#import connectors.mcws_connector as mcwsc
#import connectors.states_connector as statesc


def make_pd_cache_from_data(data_lists):
    """
    Creates a pandas DataFrame cache from a list of data sources.

    Args:
        data_lists (list): A list of JSON strings or objects containing data to be loaded.

    Returns:
        pd.DataFrame: A consolidated DataFrame containing data from all sources,
                      with standardized headers and datetime conversions.
    """
    cache = pd.DataFrame(columns=datachecker.header())
    for d in data_lists:
        new_df = pd.read_json(d)
        for col in datachecker.header():
            if col not in new_df.columns:
                new_df[col] = None
        cache = pd.concat([cache, new_df[datachecker.header()]], ignore_index=True, axis=0, join='outer')
    for time_type in datachecker.valid_time_type_cols():
        cache[time_type] = pd.to_datetime(
            cache[time_type], unit="ms", utc=True
        )  # PSA: pd.to_json saves in ms, pd.to_datetime expects ns
    return cache


def get_min_date(data):
    """Returns the minimum date of data in this cache.

    Args:
        data (pd.DataFrame): The DataFrame containing the data.

    Returns:
        datetime: The minimum datetime found in the 'scet' column, or None if empty.
    """
    if len(data["scet"]) > 0:
        return data["scet"].min()
    else:
        return None


def get_max_date(data):
    """Returns the maximum date of data in this cache.

    Args:
        data (pd.DataFrame): The DataFrame containing the data.

    Returns:
        datetime: The maximum datetime found in the 'scet' column, or None if empty.
    """
    if len(data["scet"]) > 0:
        return data["scet"].max()
    else:
        return None


def sort_by(data, col, ascending=True):
    """Sorts the data by the given column name.

    Args:
        data (pd.DataFrame): The DataFrame to sort.
        col (str): The name of the column to sort by.
        ascending (bool, optional): Whether to sort in ascending order. Defaults to True.

    Returns:
        pd.DataFrame: The sorted DataFrame.
    """
    if col not in data.columns:
        return data
    data = data.sort_values(by=col, ignore_index=True, ascending=ascending)
    logging.debug("sort data log")
    log_data(data)
    return data


def get_data_from_state(data, state):
    """Returns only the data for the given state.
    Does not modify the cache.
    Returns empty if state is invalid.

    Args:
        data (pd.DataFrame): The DataFrame containing the data.
        state (str): The name of the state to filter by.

    Returns:
        pd.DataFrame: A subset of the data containing only rows for the specified state.
    """
    if state in data.name.unique():
        return data[data["name"] == state]
    else:
        return pd.DataFrame(columns=datachecker.header())


def get_data_from_states(data, filter_states):
    """Returns only data for the given list of states.
    Does not modify the cache.
    Returns empty if all states are invalid,
    otherwise skips invalid states.

    Args:
        data (pd.DataFrame): The DataFrame containing the data.
        filter_states (list): A list of state names to filter by.

    Returns:
        pd.DataFrame: A subset of the data containing only rows for the specified states.
    """
    if set(filter_states):
        return data.loc[data.name.isin(filter_states)]
    return pd.DataFrame(columns=datachecker.header())


def column_values_from_state(data, state, time="scet", elapsed_seconds=False):
    """Makes a column of values for the given state.
    Returns the data and column name.
    
    Args:
        data (pd.DataFrame): DataFrame containing the data
        state (str): The state/column to process
        time (str, optional): The time column to sort by. Defaults to "scet".
        elapsed_seconds (bool, optional): Whether to convert time to elapsed seconds. 
            Defaults to False.
    
    Returns:
        tuple: A tuple containing (processed data, column name).
    """
    # Make sure time column exists
    if time not in data.columns:
        if "scet" in data.columns:
            time = "scet"
        elif len(data.columns) > 0:
            # Use the first column as a fallback
            time = data.columns[0]
        else:
            # Return unmodified data if no columns exist
            return data, state
    
    data = sort_by(data, time)
    interpolator = interpolate.DefaultInterpolator(data)
    data = interpolator.make_column_values(state, elapsed_seconds)
    log_data(data)
    
    if datachecker.is_time_type(state) and elapsed_seconds:
        state = "elapsed_seconds"
    else:
        state = "z_numeric"
    return data, state


def log_data(data):
    """Log the current data as a debug message.

    Args:
        data (pd.DataFrame): The DataFrame to log.
    """
    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        logging.debug("\n %s", data)


def print_data(data):
    """Print the current data to console.

    Args:
        data (pd.DataFrame): The DataFrame to print.
    """
    with pd.option_context("display.max_rows", None, "display.max_columns", None):
        print("\n %s", data)


def get_units_from_states(data, states):
    """Retrieves the units for a list of states or a single state.

    Args:
        data (pd.DataFrame): The DataFrame containing the data.
        states (Union[str, list]): A single state name or a list of state names.

    Returns:
        Union[str, list]: A unit string if the input was a single state, 
                          or a list of unit strings if the input was a list.
    """
    if isinstance(states, list):
        units = []
        for state in states:
            r = get_unit_from_state(data, state)
            units.append(r)
        return units
    else: 
        return get_unit_from_state(data, states)

def get_unit_from_state(data, state):
    """Retrieves the unit associated with a specific state.

    Args:
        data (pd.DataFrame): The DataFrame containing the data.
        state (str): The name of the state to find the unit for.

    Returns:
        str: The unit string (e.g., 'Time', 'volts'), or 'Unknown' if not found.
    """
    if datachecker.is_time_type(state):
        return 'Time'
    if 'unit' in data.columns:
        state_data = get_data_from_state(data, state)
        if len(state_data) > 0:
            unit = state_data['unit'].unique()
            if len(unit) == 1:
                return unit[0]
            warnings.warn(f'DTAT has detected multiple units for a single state. {state} has units {unit}.')
            return unit
    return 'Unknown'


def make_doy_from_state(data, state):
    """Creates a 'doy' (Day of Year) formatted string column from a time state.

    Args:
        data (pd.DataFrame): The DataFrame containing the data.
        state (str): The name of the time column to convert.

    Returns:
        pd.DataFrame: The DataFrame with an added 'doy' column.
    """
    print (data.columns)
    if datachecker.is_time_type(state) and 'doy' not in data.columns:
        data['doy'] = data.apply(
            lambda row: datetime.datetime.strftime(row[state], '%Y/%jT%H:%M:%S.%f'), 
            axis=1)
        #print (data['doy'])
    return data