import unittest
from src.api.routes.routing import decode_polyline

class TestRouting(unittest.TestCase):
    def test_decode_polyline_empty(self):
        """Test decoding an empty polyline."""
        self.assertEqual(decode_polyline(""), [])

    def test_decode_polyline_single_point(self):
        """Test decoding a single coordinate point."""
        # Represents [38.5, -120.2]
        polyline = "_p~iF~ps|U"
        expected = [[38.5, -120.2]]
        decoded = decode_polyline(polyline)

        self.assertEqual(len(decoded), len(expected))
        for d, e in zip(decoded, expected):
            self.assertAlmostEqual(d[0], e[0], places=5)
            self.assertAlmostEqual(d[1], e[1], places=5)

    def test_decode_polyline_multiple_points(self):
        """Test decoding a multi-point polyline from Google documentation."""
        # Represents [[38.5, -120.2], [40.7, -120.95], [43.252, -126.453]]
        polyline = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
        expected = [[38.5, -120.2], [40.7, -120.95], [43.252, -126.453]]
        decoded = decode_polyline(polyline)

        self.assertEqual(len(decoded), len(expected))
        for d, e in zip(decoded, expected):
            self.assertAlmostEqual(d[0], e[0], places=5)
            self.assertAlmostEqual(d[1], e[1], places=5)

    def test_decode_polyline_negative_values(self):
        """Test decoding polyline with negative coordinates."""
        # Represents [[-38.5, -120.2]]
        polyline = "~o~iF~ps|U"
        expected = [[-38.5, -120.2]]
        decoded = decode_polyline(polyline)

        self.assertEqual(len(decoded), len(expected))
        for d, e in zip(decoded, expected):
            self.assertAlmostEqual(d[0], e[0], places=5)
            self.assertAlmostEqual(d[1], e[1], places=5)

if __name__ == '__main__':
    unittest.main()
