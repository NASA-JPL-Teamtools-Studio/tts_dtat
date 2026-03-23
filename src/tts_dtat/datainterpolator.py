"""Helper functions to create additional numeric scales for figure traces"""

import logging
from datetime import datetime

import pandas as pd

import tts_dtat.datachecker as datachecker


class DefaultInterpolator:
    """Default interpolator logic module. See the documentation for details."""

    def __init__(self, data):
        """:keyword data: pandas dataframe with "apidName" and "dn" columns sorted by a time type"""
        self.data = data

    def make_column_values(self, state, elapsed_seconds=False):
        """Interpolate data as necessary (pad then backfill)
        to provide a continuous set of color values for the "z-axis" of a data set.
        This method assumes data has been sorted by the primary time type used for the graph.
        :keyword state: apidName to make into a column of numeric values to use as a colorscale
        :keyword time_in_seconds: return a time type as a series of seconds elapsed since 1/1/2018"""

        if state is None or self.data is None or self.data.empty:
            return self.data

        self.data.reset_index()
        if datachecker.is_time_type(state) and elapsed_seconds:
            logging.debug("z_var is a time type")
            # Check if we're dealing with numpy datetime64 objects
            if hasattr(self.data[state].dtype, 'type') and self.data[state].dtype.type == 'datetime64[ns]':
                # Convert numpy datetime64 to Python datetime objects to avoid dtype issues
                self.data[state] = self.data[state].dt.to_pydatetime()
                
            # Calculate elapsed seconds since reference date
            try:
                reference_date = datetime(2018, 1, 1, tzinfo=self.data[state][0].tzinfo)
                self.data["elapsed_seconds"] = (
                    (self.data[state] - reference_date)
                    .dt.total_seconds()
                    .astype(float)
                )
            except (AttributeError, TypeError):
                # Handle case where tzinfo might be missing or other issues
                self.data["elapsed_seconds"] = pd.to_numeric(self.data[state])
                
            return self.data

        # If state is in columns, ensure z_numeric exists
        if state in self.data.columns:
            logging.debug("found z_var in %s", self.data.columns)
            
            # If z_numeric exists and is valid, return
            if "z_numeric" in self.data.columns:
                if not pd.isnull(self.data[state]).all() and not pd.isnull(self.data["z_numeric"]).all():
                    return self.data
            
            try:
                self.data["z_numeric"] = self.data[state].astype(float)
            except (ValueError, TypeError):
                self.data["z_numeric"] = self.make_num_vals_from_strings(self.data[state])
            return self.data

        if state not in self.data.name.values:
            logging.debug("%s is not a state in data", state)
            return self.data
        logging.debug("making new data column")
        return self.make_num_col_from_state(state)

    def make_num_col_from_state(self, state):
        """Make a new column of non-empty numeric types based on the data from state.
        Interpolate data as necessary (pad then backfill).
        :keyword state: apidName to make into a column of numeric values to use as a colorscale"""
        locs = self.data.name.eq(state)
        state_data = self.data["value"].where(locs, None)
        
        state_data = state_data.ffill()
        state_data = state_data.bfill()
        
        try:
            numeric_data = state_data.astype(float)
        except ValueError:
            numeric_data = self.make_num_vals_from_strings(state_data)

        self.data[state] = state_data
        self.data["z_numeric"] = numeric_data

        return self.data

    def make_num_vals_from_strings(self, col):
        """Make a new column of non-empty numeric types from a column of string values.
        :keyword col: column of string values"""
        lookup = {}
        int_state_data = []
        i = 0
        for item in col:
            if item not in lookup.keys():
                lookup[item] = len(lookup)
            int_state_data.insert(i, lookup[item])
            i += 1
        return int_state_data