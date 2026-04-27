import unittest
import os
import tempfile
from unittest.mock import patch
from ytmd_sdk import YTMD
from requests import Session

class TestYTMD(unittest.TestCase):
    def test_authenticate(self):
        with patch.object(Session, "post") as session_mock:
            ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
            session_mock.return_value.status_code = 400
            session_mock.return_value.text = "Unittest"
            self.assertRaises(Exception, ytmd.authenticate)

    def test_get_version(self):
        with patch.object(Session, "get") as session_mock:
            ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
            session_mock.return_value.status_code = 200
            session_mock.return_value.json.return_value = {"apiVersions": ["v1"]}
            response = ytmd.get_version()
            self.assertEqual(response, ["v1"])

    def test_get_state(self):
        with patch.object(Session, "get") as session_mock:
            ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
            self.assertRaises(Exception, ytmd.get_state) # no token

            ytmd.update_token("token")
            session_mock.return_value.status_code = 200
            self.assertEqual(ytmd.get_state().status_code, 200)

    def test_ytmd_post_methods(self):
        post_methods = ["play", "pause", "volume_up", "volume_down",
                        "mute", "unmute", "next", "previous",
                        "shuffle", "toggle_like", "toggle_dislike"]
        methods_with_args = ["set_volume", "seek_to", "repeatMode", "play_index"]

        for method in post_methods:
            with patch.object(Session, "post") as session_mock:
                ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
                self.assertRaises(Exception, getattr(ytmd, method))
                ytmd.update_token("token")
                session_mock.return_value.status_code = 200
                response = getattr(ytmd, method)()
                self.assertEqual(response.status_code, 200)

        for method in methods_with_args:
            with patch.object(Session, "post") as session_mock:
                ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
                self.assertRaises(Exception, getattr(ytmd, method), 1)
                ytmd.update_token("token")
                session_mock.return_value.status_code = 200
                response = getattr(ytmd, method)(1)
                self.assertEqual(response.status_code, 200)

        # Verify zero-valued arguments are sent (not silently dropped).
        with patch.object(Session, "post") as session_mock:
            ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
            ytmd.update_token("token")
            session_mock.return_value.status_code = 200
            ytmd.set_volume(0)
            call_body = str(session_mock.call_args)
            self.assertIn('"data": 0', call_body)

    def test_get_playlists(self):
        with patch.object(Session, "get") as session_mock:
            ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
            self.assertRaises(Exception, ytmd.get_playlists)  # no token
            ytmd.update_token("token")
            session_mock.return_value.status_code = 200
            self.assertEqual(ytmd.get_playlists().status_code, 200)

    def test_change_video(self):
        with patch.object(Session, "post") as session_mock:
            ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
            self.assertRaises(Exception, ytmd.change_video, None, "PLxxx")
            ytmd.update_token("token")
            session_mock.return_value.status_code = 200
            response = ytmd.change_video(playlist_id="PLxxx")
            self.assertEqual(response.status_code, 200)
            call_body = session_mock.call_args
            self.assertIn("changeVideo", str(call_body))

    def test_update_endpoint(self):
        ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
        ytmd.update_endpoint("192.168.1.10", 9863)
        self.assertEqual(ytmd.host, "192.168.1.10")
        self.assertEqual(ytmd.port, 9863)
        self.assertEqual(ytmd.url, "http://192.168.1.10:9863/api/v1")

    def test_is_token_valid(self):
        ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
        # No token → always invalid
        self.assertFalse(ytmd.is_token_valid())

        with patch.object(Session, "get") as session_mock:
            ytmd.update_token("token")
            session_mock.return_value.status_code = 200
            self.assertTrue(ytmd.is_token_valid())

            session_mock.return_value.status_code = 401
            self.assertFalse(ytmd.is_token_valid())

            # Network errors should not trigger re-auth
            session_mock.side_effect = Exception("connection refused")
            self.assertTrue(ytmd.is_token_valid())

    def test_token_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "auth_token.txt")

            ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")

            # load_token returns None when file doesn't exist
            result = ytmd.load_token(path)
            self.assertIsNone(result)
            self.assertIsNone(ytmd.token)

            # save_token raises when there is no token
            self.assertRaises(ValueError, ytmd.save_token, path)

            # save then load round-trip
            ytmd.update_token("my-secret-token")
            ytmd.save_token(path)
            self.assertTrue(os.path.exists(path))

            ytmd2 = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")
            loaded = ytmd2.load_token(path)
            self.assertEqual(loaded, "my-secret-token")
            self.assertEqual(ytmd2.token, "my-secret-token")
            self.assertEqual(ytmd2.session.headers.get("Authorization"), "my-secret-token")

            # clear_token removes file and clears in-memory token
            ytmd2.clear_token(path)
            self.assertIsNone(ytmd2.token)
            self.assertNotIn("Authorization", ytmd2.session.headers)
            self.assertFalse(os.path.exists(path))

            # clear_token is idempotent when file already gone
            ytmd2.clear_token(path)  # should not raise


if __name__ == "__main__":
    unittest.main()
