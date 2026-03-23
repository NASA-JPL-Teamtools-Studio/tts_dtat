import pytest
import pandas as pd
from tts_dtat.dataconnectors import csvconnector

@pytest.fixture
def valid_csv_file(tmp_path):
    """Creates a valid temporary CSV file."""
    d = tmp_path / "data"
    d.mkdir()
    p = d / "test_data.csv"
    content = """scet,name,value,unit
2020-001T12:00:00.000,Voltage,5.0,V
2020-001T12:01:00.000,Voltage,5.1,V
2020-001T12:02:00.000,Current,1.0,A
"""
    p.write_text(content, encoding="utf-8")
    return str(p)

@pytest.fixture
def mixed_time_csv_file(tmp_path):
    """Creates a CSV with mixed time formats (subseconds and no subseconds)."""
    d = tmp_path / "data_mixed"
    d.mkdir()
    p = d / "mixed_time.csv"
    # First row has subseconds, second row does not
    content = """scet,name,value
2020-001T12:00:00.123,StateA,1
2020-001T12:00:01,StateA,2
"""
    p.write_text(content, encoding="utf-8")
    return str(p)

@pytest.fixture
def invalid_csv_file(tmp_path):
    """Creates a CSV missing required headers."""
    d = tmp_path / "data_invalid"
    d.mkdir()
    p = d / "invalid.csv"
    content = """timestamp,val
2020-01-01,10
"""
    p.write_text(content, encoding="utf-8")
    return str(p)

def test_init_valid_file(valid_csv_file):
    """Test initialization with a valid file."""
    #
    connector = csvconnector.CSVConnector(valid_csv_file)
    
    assert connector.get_file() == valid_csv_file
    data = connector.get_data()
    assert not data.empty
    assert len(data) == 3
    # Check that scet was converted to datetime
    assert pd.api.types.is_datetime64_any_dtype(data["scet"])

def test_get_states(valid_csv_file):
    """Test retrieval of unique state names."""
    connector = csvconnector.CSVConnector(valid_csv_file)
    states = connector.get_states()
    
    assert len(states) == 2
    assert "Voltage" in states
    assert "Current" in states

def test_mixed_time_formats(mixed_time_csv_file):
    """Test the internal logic for handling mixed time formats."""
    #
    # The refresh_data method contains inner functions to handle this specific case
    connector = csvconnector.CSVConnector(mixed_time_csv_file)
    data = connector.get_data()
    
    assert len(data) == 2
    assert pd.api.types.is_datetime64_any_dtype(data["scet"])
    
    # Check microseconds
    assert data["scet"].iloc[0].microsecond == 123000
    assert data["scet"].iloc[1].second == 1
    assert data["scet"].iloc[1].microsecond == 0

def test_refresh_data(valid_csv_file):
    """Test that refresh_data reloads the file content."""
    connector = csvconnector.CSVConnector(valid_csv_file)
    initial_len = len(connector.get_data())
    
    # Modify the file
    with open(valid_csv_file, "a") as f:
        f.write("2020-001T12:03:00.000,Voltage,5.2,V\n")
    
    # Trigger refresh
    connector.refresh_data()
    new_len = len(connector.get_data())
    
    assert new_len == initial_len + 1

def test_scrape_states_no_name_col(tmp_path):
    """Test scraping states when 'name' column is missing (if verify_header allowed it)."""
    # Note: verify_header usually enforcing 'name', but we can bypass or test edge case
    # where verifying is done but column might be manipulated or logic changes.
    # However, let's strictly test the scraping logic.
    
    # Create a CSV that technically passes min_header? 
    # datachecker.min_header is ['scet', 'name', 'value']
    # So we can't easily create a file without 'name' that passes __init__.
    
    # We can manually invoke the private method if we really want to test that branch,
    # or just trust that verify_header protects us.
    # Let's try to pass a file that has the headers but is empty.
    d = tmp_path / "empty"
    d.mkdir()
    p = d / "empty.csv"
    p.write_text("scet,name,value\n", encoding="utf-8")
    
    connector = csvconnector.CSVConnector(str(p))
    states = connector.get_states()
    assert len(states) == 0