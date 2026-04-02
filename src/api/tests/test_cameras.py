import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from src.api.routes.cameras import fetch_cameras_from_overpass

class TestCamerasRoutes(unittest.IsolatedAsyncioTestCase):
    @patch('src.api.routes.cameras.httpx.AsyncClient.post')
    async def test_fetch_cameras_from_overpass_valid_bbox(self, mock_post):
        mock_res = MagicMock()
        mock_res.status_code = 200
        mock_res.json.return_value = {'elements': []}
        mock_post.return_value = mock_res

        bbox = "-122.4,37.7,-122.3,37.8"
        cameras = await fetch_cameras_from_overpass(bbox)

        self.assertEqual(cameras, [])
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        data = call_args[1]['data']['data']
        self.assertIn("37.7,-122.4,37.8,-122.3", data)

    async def test_fetch_cameras_from_overpass_invalid_bbox(self):
        bbox = "-122.4,37.7,-122.3,invalid"
        with self.assertRaises(ValueError):
            await fetch_cameras_from_overpass(bbox)

if __name__ == '__main__':
    unittest.main()
