import pandas as pd
import tts_dtat.datachecker

class CSVConnector:
    """
    Connector object to read data from a file

    This is the simplest possible connector that does little other
    than covnert time strings into datetime objects for plotting.
    Data must otherwise already be formatted in the way DTAT expects
    with the columns scet, value, name, unit, and one chanval per
    row. Additional columns are OK, but will be ignored.

    Any other data format needs its own connector.
    """

    def __init__(self, file):
        """
        Initializes the CSVConnector with a file path.

        Args:
            file (str): The path to the CSV file to be read.
        """
        self.__file = file

        self.__data = pd.DataFrame()

        self.refresh_data()

        tts_dtat.datachecker.verify_header(self.__data)

        self.__states = self.__scrape_states()

    def get_file(self):
        """Returns the name of the file this connector reads from"""
        return self.__file

    def get_data(self):
        """Read the data stored by the object"""
        return self.__data

    def refresh_data(self):
        """Refresh the data stored by the object with the latest from the original file"""

        def handle_mixed_time_formats(timestamp):
            """Tries to convert a string with subseconds first,
            if that fails, tries without subseconds,
            and otherwise returns an error if both fail"""
            import datetime
            try:
                return datetime.datetime.strptime(timestamp, "%Y-%jT%H:%M:%S.%f")
            except ValueError:
                return datetime.datetime.strptime(timestamp, "%Y-%jT%H:%M:%S")

        def make_datetime_column(time_data):
            """Returns a transformed column of strings to datetime objects"""
            try:
                return pd.to_datetime(time_data, utc=True, format="%Y-%jT%H:%M:%S.%f")
            except ValueError:
                try:
                    return pd.to_datetime(time_data, utc=True, format="%Y-%jT%H:%M:%S")
                except ValueError:
                    return time_data.apply(handle_mixed_time_formats)

        self.__data = pd.read_csv(self.__file, skipinitialspace=True)

        self.__data["scet"] = make_datetime_column(
            self.__data["scet"]
        )
        
    def __scrape_states(self):
        """
        Extracts the unique state names from the loaded data.

        Returns:
            numpy.ndarray: An array of unique state names found in the 'name' column,
                           or an empty list if the column does not exist.
        """
        if "name" not in self.__data.columns:
            return []
        return self.__data.name.unique()
    
    def get_states(self):
        """Returns the names of the states contained in this connector"""
        return self.__states