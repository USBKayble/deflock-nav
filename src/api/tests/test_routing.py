import unittest
import math
from src.api.routes.routing import haversine

class TestRoutingHaversine(unittest.TestCase):
    def test_zero_distance(self):
        """Test distance between the same point is 0."""
        self.assertEqual(haversine(0, 0, 0, 0), 0.0)
        self.assertEqual(haversine(40.7128, -74.0060, 40.7128, -74.0060), 0.0)

    def test_one_degree_equator(self):
        """Test distance of 1 degree along the equator."""
        # 1 degree of longitude at the equator is approx 111.19 km
        expected_distance = (2 * math.pi * 6371e3) / 360
        distance = haversine(0.0, 0.0, 0.0, 1.0)
        self.assertAlmostEqual(distance, expected_distance, places=2)

    def test_one_degree_meridian(self):
        """Test distance of 1 degree along a meridian."""
        expected_distance = (2 * math.pi * 6371e3) / 360
        distance = haversine(0.0, 0.0, 1.0, 0.0)
        self.assertAlmostEqual(distance, expected_distance, places=2)

    def test_new_york_to_london(self):
        """Test distance between New York and London."""
        # NY: 40.7128 N, 74.0060 W
        # London: 51.5074 N, 0.1278 W
        distance = haversine(40.7128, -74.0060, 51.5074, -0.1278)
        # Haversine distance with R=6371km yields ~5570222 meters
        self.assertAlmostEqual(distance, 5570222, delta=10) # 10 meters tolerance

    def test_antipodal_points(self):
        """Test distance between antipodal points (half circumference)."""
        expected_distance = math.pi * 6371e3
        distance = haversine(0.0, 0.0, 0.0, 180.0)
        self.assertAlmostEqual(distance, expected_distance, places=2)

        distance2 = haversine(90.0, 0.0, -90.0, 0.0)
        self.assertAlmostEqual(distance2, expected_distance, places=2)

if __name__ == "__main__":
    unittest.main()
