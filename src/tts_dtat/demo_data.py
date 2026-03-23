import pdb
import numpy as np
import pandas as pd

def make_time_col(length=1000):
    """Generates a list of timestamps starting from the current time.

    Args:
        length (int, optional): The number of minutes to generate timestamps for. 
            Defaults to 1000.

    Returns:
        list: A list of pandas Timestamps with minute frequency.
    """
    start_time = pd.Timestamp.now().floor('min')
    end_time = start_time + pd.Timedelta(minutes=(length-1))
    return pd.date_range(start=start_time, end=end_time, freq='min').to_list()

def instrument_turn_on():
    """Simulates data for an instrument turning on. Used for demo jupyter notebook,
    and has no operational purpose.

    Generates synthetic data for Voltage, Current, and Mode states over time,
    simulating a startup sequence from TEST to INIT to OPERATIONAL.

    Returns:
        pd.DataFrame: A DataFrame containing columns for 'scet' (time), 'name', 
            'value', and 'unit'.
    """
    #box turns on at x=-60
    x = (np.arange(1000)-300)*2
    voltage = 20*np.exp(0.025*x)/(20+np.exp(0.025*x))+10*np.random.rand(len(x))
    current = 5*np.exp(0.025*x)/(5+np.exp(0.025*x))+1*np.random.rand(len(x))
    std_deviations = np.array([1.0, 2.0])
    random_array = np.random.randn(1000) * 10

    return pd.DataFrame({
        "scet": make_time_col(length=1000) + make_time_col(length=1000) + make_time_col(length=1000),
        "name": ["Voltage"]*1000 + ["Current"]*1000 + ["Mode"]*1000,
        "value": list(voltage) + list(current) + ['TEST']*300 + ['INIT']*150 + ['OPERATIONAL']*550,
        "unit": ["volts"]*1000 + ["amps"]*1000 + ["mode"]*1000,
        })

def drifting_off_nominal():
    """Simulates data for an instrument drifting off its nominal values.
	Used for demo jupyter notebook, and has no operational purpose.
	
    Generates synthetic data for Voltage and Current that drifts over time,
    along with Mode state changes.

    Returns:
        pd.DataFrame: A DataFrame containing columns for 'scet' (time), 'name',
            and 'value'.
    """
    alpha = (np.arange(1000))*2-1925
    t = 10 + 2000*np.exp(0.005*alpha)/(2000+np.exp(0.005*alpha))+0*np.random.rand(len(alpha))

    num_rows = 1000
    num_cols = 2

    # Specify different standard deviations for each column
    std_deviations = np.array([1.0, 2.0])

    # Generate random array with specified shape and standard deviations
    random_array = np.random.randn(num_rows, num_cols) * std_deviations

    x = t*5 + 3*random_array[:,0]
    y = t*6 + random_array[:,1]
    # plt.plot(x,y,'.')
    # plt.show()
    return pd.DataFrame({
        "scet": make_time_col(length=1000) + make_time_col(length=1000) + make_time_col(length=1000),
        "name": ["Voltage"]*1000 + ["Current"]*1000 + ["Mode"]*1000,
        "value": list(x) + list(y) + ["OFF"]*300 + ["ON"]*700
        })

if __name__ == '__main__':
    drifting_off_nominal()
    # x, y = turn_on_data()

    pdb.set_trace()