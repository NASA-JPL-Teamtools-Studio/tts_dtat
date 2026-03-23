"""Utility functions for verifying and identifying data"""

import datetime
import logging

import pandas as pd


def header():
    """The datacache header"""
    return ["scet", "ert", "name", "value"]


def min_header():
    """The smallest valid header for imported information"""
    return ["scet", "name", "value"]


def valid_value_col_names():
    """A list of all valid generic 'value' column names.
    This is the source of truth definition."""
    return ["value"]


def valid_time_type_cols():
    """A list of all valid time type column names.
    This is the source of truth definition."""
    return ["scet", "ert", "doy"]


def verify_header(data):
    """Verifies that the header of a dataframe has the necessary columns"""
    for col in min_header():
        if col not in data.columns:
            raise Exception("Invalid column headers, '{}' not found".format(col))
    return True


def is_time_type(state):
    """Returns true if the state is a known time type"""
    return state in valid_time_type_cols()


def make_datetime_column(time_data):
    """Returns a transformed column of strings to datetime objects"""
    try:
        return pd.to_datetime(time_data, utc=True, format="%Y-%jT%H:%M:%S.%f")
    except ValueError:
        try:
            return pd.to_datetime(time_data, utc=True, format="%Y-%jT%H:%M:%S")
        except ValueError:
            return time_data.apply(handle_mixed_time_formats)


def handle_mixed_time_formats(timestamp):
    """Tries to convert a string with subseconds first,
    if that fails, tries without subseconds,
    and otherwise returns an error if both fail"""
    try:
        return datetime.datetime.strptime(timestamp, "%Y-%jT%H:%M:%S.%f")
    except ValueError:
        return datetime.datetime.strptime(timestamp, "%Y-%jT%H:%M:%S")


def find_value_header(cols):
    """Returns the column name of the 'value' in the data, given the column names as a list"""
    for name in valid_value_col_names():
        if name in cols:
            return name
    return None
