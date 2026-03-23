import pytest
from tts_dtat import palette

def test_defaults_exist():
    """Test that default colors and options are populated."""
    # Test that we have default colors
    colors = palette.get_default_colors()
    assert isinstance(colors, list)
    assert len(colors) > 0
    # Check a known color exists (e.g., the first one in the list #0078AF)
    assert "#0078AF" in colors

def test_get_default_color_options():
    """Test the dropdown option generator for colors."""
    options = palette.get_default_color_options()
    assert isinstance(options, list)
    assert len(options) == len(palette.default_colors)
    
    first_opt = options[0]
    assert "label" in first_opt
    assert "value" in first_opt
    assert "className" in first_opt
    assert "title" in first_opt

def test_get_default_shape_options():
    """Test the dropdown option generator for shapes."""
    options = palette.get_default_shape_options()
    assert isinstance(options, list)
    assert len(options) > 0
    assert options[0]["value"] == "circle"

def test_get_line_color_valid():
    """Test retrieving a line color for a known fill color."""
    # #0078AF (Dark-Blue) should map to #0073FF
    line_col = palette.get_line_color("#0078AF")
    assert line_col == "#0073FF"

def test_get_line_color_invalid():
    """Test that unknown colors return themselves."""
    unknown_color = "#123456"
    assert palette.get_line_color(unknown_color) == unknown_color
    assert palette.get_line_color(None) is None

def test_pop_next_color_normal():
    """Test popping a color from an existing list."""
    # Create a small list of colors
    colors = ["#A", "#B", "#C"]
    
    color, remaining = palette.pop_next_color(colors)
    
    assert color == "#A"
    assert remaining == ["#B", "#C"]

def test_pop_next_color_empty():
    """Test that an empty/None list resets to defaults."""
    # Should reset to default list and pop the first one
    color, remaining = palette.pop_next_color(None)
    
    default_keys = list(palette.default_colors.keys())
    assert color == default_keys[0]
    assert len(remaining) == len(default_keys) - 1

def test_remove_unseen_bins():
    """Test logic for removing bins outside the 0-1 range."""
    # 0.5 is valid, 1.2 is too high, -0.5 is too low
    color_set = ["red", "green", "blue"]
    custom_divisions = [0.5, 1.2, -0.5]
    
    new_colors, new_divs = palette.remove_unseen_bins(color_set, custom_divisions)
    
    # Logic should:
    # 1. Sort combined list: [(-0.5, blue), (0.5, red), (1.2, green)]
    # 2. Remove high bin (1.2) -> [(-0.5, blue), (0.5, red)]
    # 3. Handle low bin: -0.5 is <= 0. It's the lowest, so force it to 0.
    
    assert len(new_colors) == 2
    assert new_divs[0] == 0  # Forced to 0
    assert new_colors[0] == "blue" # The color associated with -0.5
    assert new_divs[1] == 0.5
    assert new_colors[1] == "red"

def test_clean_and_sort_colorscale_normalization():
    """Test that divisions are normalized based on data min/max."""
    colors = ["red", "blue"]
    divisions = [10, 20]
    dmin = 0
    dmax = 100
    
    # 10 should become 0.1, 20 should become 0.2
    c, d = palette.clean_and_sort_colorscale(colors, divisions, dmin, dmax)
    
    assert d == [0.1, 0.2]
    assert c == ["red", "blue"]

def test_make_discrete_colorscale_empty():
    """Test behavior when no colors are provided."""
    scale = palette.make_discrete_colorscale([], [])
    assert scale == "jet"

def test_make_discrete_colorscale_logic():
    """Test the generation of the discrete step-function colorscale."""
    # Simple case: 2 colors splitting at 0.5
    colors = ["red", "blue"]
    divisions = [0, 0.5] 
    
    #
    # Logic adds an ending bin (1) and creates steps
    # Structure: [(val, color), (next_val-epsilon, color), ...]
    scale = palette.make_discrete_colorscale(colors, divisions)
    
    # The function explicitly inserts a (0, color) at index 0 at the very end
    # AND the loop generates a (0.0, color) as the first bin start.
    # So we expect duplicate 0 entries at the start.
    assert scale[0] == (0, "red")
    assert scale[1] == (0.0, "red") 
    
    # "red" block ends just before 0.5 (Index 2 due to the duplicate 0 start)
    assert scale[2][0] == 0.499 # 0.5 - 0.001
    assert scale[2][1] == "red"
    
    # "blue" block starts at 0.5
    assert scale[3][0] == 0.5
    assert scale[3][1] == "blue"
    
    # Ends at 1
    assert scale[-1][0] == 1
    assert scale[-1][1] == "blue"