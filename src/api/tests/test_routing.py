import unittest

from src.api.routes.routing import in_field_of_view

class TestInFieldOfView(unittest.TestCase):
    def test_exact_match(self):
        self.assertTrue(in_field_of_view(90, 90))
        self.assertTrue(in_field_of_view(0, 0))
        self.assertTrue(in_field_of_view(360, 360))
        self.assertTrue(in_field_of_view(180, 180))

    def test_within_fov_boundaries(self):
        # Default fov is 120 (so +/- 60 degrees from camera direction)
        # heading 30, camera 0 -> diff 30 <= 60 (True)
        self.assertTrue(in_field_of_view(30, 0))
        # heading 60, camera 0 -> diff 60 <= 60 (True)
        self.assertTrue(in_field_of_view(60, 0))
        # heading 300 (-60), camera 0 -> diff 60 <= 60 (True)
        self.assertTrue(in_field_of_view(300, 0))

        self.assertTrue(in_field_of_view(120, 150))
        self.assertTrue(in_field_of_view(180, 150))

    def test_outside_fov_boundaries(self):
        # Default fov is 120 (+/- 60)
        # heading 90, camera 0 -> diff 90 > 60 (False)
        self.assertFalse(in_field_of_view(90, 0))
        # heading 270 (-90), camera 0 -> diff 90 > 60 (False)
        self.assertFalse(in_field_of_view(270, 0))

        self.assertFalse(in_field_of_view(250, 150))

    def test_wraparound_360(self):
        # Camera at 10, heading at 350. Diff is 20 degrees.
        # Should be True (20 <= 60)
        self.assertTrue(in_field_of_view(350, 10))
        # Camera at 350, heading at 10. Diff is 20 degrees.
        # Should be True (20 <= 60)
        self.assertTrue(in_field_of_view(10, 350))

        # Camera at 5, heading at 300. Diff is 65 degrees.
        # Should be False (65 > 60)
        self.assertFalse(in_field_of_view(300, 5))

    def test_custom_fov(self):
        # Narrow fov of 60 (+/- 30)
        self.assertTrue(in_field_of_view(20, 0, fov_angle=60))
        self.assertFalse(in_field_of_view(40, 0, fov_angle=60))

        # Wide fov of 180 (+/- 90)
        self.assertTrue(in_field_of_view(80, 0, fov_angle=180))
        self.assertFalse(in_field_of_view(100, 0, fov_angle=180))
