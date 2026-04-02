import unittest
from src.api.routes.routing import point_to_segment_distance, haversine

class TestRouting(unittest.TestCase):
    def test_point_to_segment_distance_zero_length(self):
        point = (51.5, -0.1)
        line_start = (51.6, -0.2)
        line_end = (51.6, -0.2)
        dist = point_to_segment_distance(point, line_start, line_end)
        expected_dist = haversine(51.6, -0.2, 51.5, -0.1)
        self.assertAlmostEqual(dist, expected_dist)

    def test_point_to_segment_distance_obtuse_start(self):
        point = (0.0, 0.0)
        line_start = (0.0, 1.0)
        line_end = (0.0, 2.0)
        dist = point_to_segment_distance(point, line_start, line_end)
        expected_dist = haversine(0.0, 1.0, 0.0, 0.0)
        self.assertAlmostEqual(dist, expected_dist)

    def test_point_to_segment_distance_obtuse_end(self):
        point = (0.0, 2.0)
        line_start = (0.0, 0.0)
        line_end = (0.0, 1.0)
        dist = point_to_segment_distance(point, line_start, line_end)
        expected_dist = haversine(0.0, 1.0, 0.0, 2.0)
        self.assertAlmostEqual(dist, expected_dist)

    def test_point_to_segment_distance_perpendicular(self):
        point = (1.0, 0.0)
        line_start = (0.0, -1.0)
        line_end = (0.0, 1.0)
        dist = point_to_segment_distance(point, line_start, line_end)
        expected_dist = haversine(1.0, 0.0, 0.0, 0.0)
        self.assertAlmostEqual(dist, expected_dist, delta=100)

    def test_point_on_line(self):
        point = (0.0, 1.0)
        line_start = (0.0, 0.0)
        line_end = (0.0, 2.0)
        dist = point_to_segment_distance(point, line_start, line_end)
        self.assertAlmostEqual(dist, 0.0, delta=1.0)

if __name__ == '__main__':
    unittest.main()