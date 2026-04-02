import pytest
from src.api.routes.routing import get_heading

def test_get_heading_cardinal_directions():
    # Due North
    assert pytest.approx(get_heading((0, 0), (1, 0)), abs=0.1) == 0.0
    # Due East
    assert pytest.approx(get_heading((0, 0), (0, 1)), abs=0.1) == 90.0
    # Due South
    assert pytest.approx(get_heading((1, 0), (0, 0)), abs=0.1) == 180.0
    # Due West
    assert pytest.approx(get_heading((0, 1), (0, 0)), abs=0.1) == 270.0

def test_get_heading_intercardinal():
    # North East
    assert pytest.approx(get_heading((0, 0), (1, 1)), abs=0.1) == 45.0
    # South East
    assert pytest.approx(get_heading((1, 0), (0, 1)), abs=0.1) == 135.0
    # South West
    assert pytest.approx(get_heading((1, 1), (0, 0)), abs=0.1) == 225.0
    # North West
    assert pytest.approx(get_heading((0, 1), (1, 0)), abs=0.1) == 315.0

def test_get_heading_same_point():
    # If the start and end points are the same, atan2(0, 0) is 0, so it should return 0.0
    assert pytest.approx(get_heading((0, 0), (0, 0)), abs=0.1) == 0.0

def test_get_heading_crossing_antimeridian():
    # Near anti-meridian, e.g., 179 to -179 longitude
    assert pytest.approx(get_heading((0, 179), (0, -179)), abs=0.1) == 90.0

def test_get_heading_different_hemispheres():
    # Moving from Southern to Northern hemisphere
    assert pytest.approx(get_heading((-10, 0), (10, 0)), abs=0.1) == 0.0
    # Moving from Northern to Southern hemisphere
    assert pytest.approx(get_heading((10, 0), (-10, 0)), abs=0.1) == 180.0
