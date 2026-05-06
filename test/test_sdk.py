import unittest
from unittest.mock import patch
from ytmd_sdk import YTMD
from requests import Session

APP_ID      = "test-app"
APP_NAME    = "Test Application"
APP_VERSION = "1.0.0"


class TestYTMD(unittest.TestCase):
    def _ytmd(self) -> YTMD:
        """Return a fresh, unauthenticated YTMD instance."""
        return YTMD(APP_ID, APP_NAME, APP_VERSION)

    def _authed_ytmd(self, token: str = "test-token") -> YTMD:
        """Return a YTMD instance with a token already registered."""
        ytmd = self._ytmd()
        ytmd.update_token(token)
        return ytmd

    def test_authenticate(self):
        with patch.object(Session, "post") as session_mock:
            ytmd = self._ytmd()
            session_mock.return_value.status_code = 400
            session_mock.return_value.text = "Unittest"
            self.assertRaises(Exception, ytmd.authenticate)

    def test_get_version(self):
        with patch.object(Session, "get") as session_mock:
            ytmd = self._ytmd()
            session_mock.return_value.status_code = 200
            session_mock.return_value.json.return_value = {"apiVersions": ["v1"]}
            response = ytmd.get_version()
            self.assertEqual(response, ["v1"])

    def test_get_state(self):
        with patch.object(Session, "get") as session_mock:
            ytmd = self._ytmd()
            self.assertRaises(Exception, ytmd.get_state)  # no token

            ytmd.update_token("test-token")
            session_mock.return_value.status_code = 200
            self.assertEqual(ytmd.get_state().status_code, 200)

    def test_ytmd_post_methods(self):
        post_methods = ["play", "pause", "volume_up", "volume_down",
                        "mute", "unmute", "next", "previous",
                        "shuffle", "toggle_like", "toggle_dislike"]
        methods_with_args = ["set_volume", "seek_to", "repeatMode", "play_index"]

        for method in post_methods:
            with patch.object(Session, "post") as session_mock:
                ytmd = self._ytmd()
                self.assertRaises(Exception, getattr(ytmd, method))
                ytmd.update_token("test-token")
                session_mock.return_value.status_code = 200
                response = getattr(ytmd, method)()
                self.assertEqual(response.status_code, 200)

        for method in methods_with_args:
            with patch.object(Session, "post") as session_mock:
                ytmd = self._ytmd()
                self.assertRaises(Exception, getattr(ytmd, method), 1)
                ytmd.update_token("test-token")
                session_mock.return_value.status_code = 200
                response = getattr(ytmd, method)(1)
                self.assertEqual(response.status_code, 200)

        # Verify zero-valued arguments are sent (not silently dropped).          
        with patch.object(Session, "post") as session_mock:
            ytmd = self._authed_ytmd()
            session_mock.return_value.status_code = 200
            ytmd.set_volume(0)
            call_body = str(session_mock.call_args)
            self.assertIn('"data": 0', call_body)

    def test_get_playlists(self):
        with patch.object(Session, "get") as session_mock:
            ytmd = self._ytmd()
            self.assertRaises(Exception, ytmd.get_playlists)  # no token
            ytmd.update_token("test-token")
            session_mock.return_value.status_code = 200
            self.assertEqual(ytmd.get_playlists().status_code, 200)

    def test_change_video(self):
        with patch.object(Session, "post") as session_mock:
            ytmd = self._ytmd()
            self.assertRaises(Exception, ytmd.change_video, None, "PLxxx")
            ytmd.update_token("test-token")
            session_mock.return_value.status_code = 200
            response = ytmd.change_video(playlist_id="PLxxx")
            self.assertEqual(response.status_code, 200)
            self.assertIn("changeVideo", str(session_mock.call_args))

    def test_update_endpoint(self):
        ytmd = self._ytmd()

        # host and port are reflected on the instance
        ytmd.update_endpoint("192.168.1.10", 9863)
        self.assertEqual(ytmd.host, "192.168.1.10")
        self.assertEqual(ytmd.port, 9863)
        self.assertEqual(ytmd.url, "http://192.168.1.10:9863/api/v1")

        # url is rebuilt when only port changes
        ytmd.update_endpoint("192.168.1.10", 1234)
        self.assertEqual(ytmd.port, 1234)
        self.assertEqual(ytmd.url, "http://192.168.1.10:1234/api/v1")

        # url is rebuilt when only host changes
        ytmd.update_endpoint("10.0.0.1", 1234)
        self.assertEqual(ytmd.host, "10.0.0.1")
        self.assertEqual(ytmd.url, "http://10.0.0.1:1234/api/v1")

    def test_is_token_valid(self):
        ytmd = self._ytmd()
        timeout = 5 #seconds
        # No token → always invalid
        self.assertFalse(ytmd.is_token_valid(timeout))

        with patch.object(Session, "get") as session_mock:
            ytmd.update_token("test-token")
            session_mock.return_value.status_code = 200
            self.assertTrue(ytmd.is_token_valid(timeout))

            session_mock.return_value.status_code = 401
            self.assertFalse(ytmd.is_token_valid(timeout))

            # Network errors should not trigger re-auth
            session_mock.side_effect = Exception("connection refused")
            self.assertTrue(ytmd.is_token_valid(timeout))
            
            # TODO: Do we want to have a timeout test that simulates a hanging request?
            
    def test_revoke_token(self):
        ytmd = self._authed_ytmd("my-secret-token")
        self.assertEqual(ytmd.token, "my-secret-token")
        self.assertIn("Authorization", ytmd.session.headers)

        ytmd.revoke_token()

        self.assertIsNone(ytmd.token)
        self.assertNotIn("Authorization", ytmd.session.headers)

        # revoke_token is idempotent — calling it again should not raise
        ytmd.revoke_token()

    def test_fetch_cover_art(self):
        fake_image = b'\x89PNG\r\n\x1a\n'  # minimal PNG magic bytes

        with patch.object(Session, "get") as session_mock:
            ytmd = self._ytmd()
            session_mock.return_value.status_code = 200
            session_mock.return_value.content = fake_image
            session_mock.return_value.raise_for_status.return_value = None

            result = ytmd.fetch_cover_art("https://example.com/art.jpg")

            self.assertEqual(result, fake_image)
            session_mock.assert_called_once_with("https://example.com/art.jpg", timeout=5)

    def test_fetch_cover_art_raises_on_error(self):
        with patch.object(Session, "get") as session_mock:
            ytmd = self._ytmd()
            session_mock.return_value.raise_for_status.side_effect = Exception("404 Not Found")

            self.assertRaises(Exception, ytmd.fetch_cover_art, "https://example.com/missing.jpg")



class TestYTMDUrl(unittest.TestCase):
    '''
        These might be redundant since the url method is pretty simple,
        But they are a good sanity check that URLs are formatted as expected.
    '''
    def _ytmd(self, host: str = "127.0.0.1", port: int = 9863) -> YTMD:
        """Return a YTMD instance with the given host and port."""
        return YTMD(APP_ID, APP_NAME, APP_VERSION, host=host, port=port)

    def test_happy_path(self):
        """Standard string host, int port, int version produces a well-formed URL."""
        result = self._ytmd("127.0.0.1", 9863)._url(1)
        self.assertEqual(result, "http://127.0.0.1:9863/api/v1")

    def test_named_host(self):
        """Hostname strings are preserved as-is."""
        result = self._ytmd("localhost", 9863)._url(1)
        self.assertEqual(result, "http://localhost:9863/api/v1")

    def test_float_version(self):
        """Float versions are rendered exactly as Python formats them."""
        result = self._ytmd("127.0.0.1", 9863)._url(1.5)
        self.assertEqual(result, "http://127.0.0.1:9863/api/v1.5")

    def test_int_version_as_expected_for_api(self):
        """Int version 1 produces 'v1', not 'v1.0'."""
        result = self._ytmd("127.0.0.1", 9863)._url(1)
        self.assertIn("v1", result)
        self.assertNotIn("v1.0", result)

    def test_url_starts_with_http(self):
        """Returned URL always starts with http://."""
        result = self._ytmd("127.0.0.1", 9863)._url(1)
        self.assertTrue(result.startswith("http://"))

    def test_url_contains_api_prefix(self):
        """Returned URL always contains the /api/v prefix."""
        result = self._ytmd("127.0.0.1", 9863)._url(1)
        self.assertIn("/api/v", result)

    def test_host_reflected_in_url(self):
        """The host set on the instance appears in the returned URL."""
        result = self._ytmd("192.168.1.50", 9863)._url(1)
        self.assertIn("192.168.1.50", result)

    def test_port_reflected_in_url(self):
        """The port set on the instance appears in the returned URL."""
        result = self._ytmd("127.0.0.1", 1234)._url(1)
        self.assertIn("1234", result)


if __name__ == "__main__":
    unittest.main()
