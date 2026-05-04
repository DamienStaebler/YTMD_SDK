import os
import requests
import json
import socketio
from typing import Callable, Optional

class YTMD:
    namespace = "/api/v1/realtime"

    def __init__(self, app_id: str,
                app_name: str, 
                app_version: str,
                host: str = "127.0.0.1",
                port: int = 9863,
                token: Optional[str] = None, logging=False):
        self.id = app_id
        self.name = app_name
        self.version = app_version
        self.host = host
        self.port = port
        self.token = token

        self.url = f"http://{self.host}:{self.port}/api/v1"

        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

        self.socket = socketio.Client(logger=logging)
        self.registered_events = []

    def register_event(self, event: str, callback: Callable) -> None:
        """Register an event to be triggered when the event is emitted by YTMD

        Args:
            event (str): event from Events class
            callback (Callable): function to be called when event is triggered
        """
        if not callable(callback):
            raise Exception("Callback must be a function")
        
        if event in self.registered_events:
            raise Exception(f"Event {event} is already registered")

        self.socket.on(event, callback, namespace=self.namespace)
        self.registered_events.append(event)

    def connect(self) -> None:
        """Connect to YTMD Socket
        """
        self._check_token()

        if not self.registered_events:
            raise Exception("No events registered")
        
        try:
            self.socket.connect(
                f"ws://{self.host}:{self.port}",
                auth={'token': self.token}, transports=["websocket"],
                namespaces=[self.namespace]
            )
        except Exception as e:
            raise Exception(f"Failed to connect to YTMD: {e}")

    def authenticate(self) -> str|None:
        """Authenticate with YTMD application and obtain token.
        If successful, the token is stored in the object and returned.
        This token should be saved and load them using update_token() method.
        """

        code = self.request_code()
        
        if code.status_code == 200:
            token = self.request_token(code.json()["code"])
            
            if token.status_code == 200:
                token = token.json()["token"]
                self.update_token(token)
                return token
            else:
                raise Exception(f"Failed to obtain token: {token.text}")
        
        raise Exception(f"Failed to obtain code: {code.text}")
    
    def update_token(self, token: str) -> None:
        """Whenever the object is created, this method should be
        used to register the token that was obtained from authenticate() method.
        """
        self.token = token
        self.session.headers.update({"Authorization": token})
    
    def request_code(self) -> requests.Response:
        """
        Internal method to request code from YTMD application
        """
        url = self.url + "/auth/requestcode"
        data = {
            "appId": self.id,
            "appName": self.name,
            "appVersion": self.version
        }
        return self.session.post(url, data=json.dumps(data))
    
    def request_token(self, code: str, timeout: int = 35) -> requests.Response:
        """Internal method to request token from YTMD application

        Args:
            code (str): code that was obtained from request_code()
            timeout (int): seconds to wait for user approval (default 35)
        """
        url = self.url + "/auth/request"
        data = {
            "appId": self.id,
            "code": code
        }
        return self.session.post(url, data=json.dumps(data), timeout=timeout)

    def _check_token(self) -> None:
        """Internal method to check if token is present in the object. If not, raise an exception.
        """
        if not self.token or not self.session.headers.get("Authorization"):
            raise Exception("Token is required to communicate with YTMD application. Please authenticate first.")
    
    def _command(self, command: str, data: Optional[int] = None) -> requests.Response:
        """Internal method to send commands to the player"""
        self._check_token()

        url = self.url + "/command"
        request_data = { "command": command }
        
        if data:
            request_data["data"] = data

        return self.session.post(url, data=json.dumps(request_data))
    
    def get_version(self) -> list[str]:
        """Get the supported api versions of the player"""
        url = "http://" + f"{self.host}:{self.port}" + "/metadata"
        response = self.session.get(url)
        if response.status_code == 200:
            return response.json()['apiVersions']
        
        raise Exception(f"Failed to obtain metadata: {response.text}")

    def get_state(self) -> requests.Response:
        """
        Get the current state of the player
        """
        self._check_token()
        return self.session.get(self.url + "/state")
    
    def get_playlists(self) -> requests.Response:
        """
        Get the playlists of the player
        """
        self._check_token()
        return self.session.get(self.url + "/playlists")
    
    def toggle_playback(self) -> requests.Response:
        """
        Toggle playback
        """
        return self._command("playPause")
    
    def play(self) -> requests.Response:
        """
        Play the current track
        """
        return self._command("play")
    
    def pause(self) -> requests.Response:
        """
        pause the current track
        """
        return self._command("pause")
    
    def volume_up(self) -> requests.Response:
        """
        Increase the volume by 10%
        """
        return self._command("volumeUp")
    
    def volume_down(self) -> requests.Response:
        """
        Decrease the volume by 10%
        """
        return self._command("volumeDown")
    
    def set_volume(self, volume: int) -> requests.Response:
        """
        Set the volume to a specific value
        """
        return self._command("setVolume", volume)
    
    def mute(self) -> requests.Response:
        """
        Mute the player
        """
        return self._command("mute")
    
    def unmute(self) -> requests.Response:
        """
        Unmute the player
        """
        return self._command("unmute")
    
    def seek_to(self, time: int) -> requests.Response:
        """
        Seek to a specific time in the track
        """
        return self._command("seekTo", time)
    
    def next(self) -> requests.Response:
        """
        Play the next track in the queue
        """
        return self._command("next")
    
    def previous(self) -> requests.Response:
        """
        Play the previous track in the queue
        """
        return self._command("previous")
    
    def repeatMode(self, mode: int) -> requests.Response:
        """
        Set the repeat mode of the player

        Args:
            mode (int): 0 - None, 1 - All, 2 - One
        """
        return self._command("repeatMode", mode)
    
    def shuffle(self) -> requests.Response:
        """
        Shuffle the queue
        """
        return self._command("shuffle")
    
    def play_index(self, index: int) -> requests.Response:
        """
        Play a specific track in the queue
        """
        return self._command("playQueueIndex", index)
    
    def toggle_like(self) -> requests.Response:
        """
        Toggle the like status of the current track
        """
        return self._command("toggleLike")
    
    def toggle_dislike(self) -> requests.Response:
        """
        Toggle the dislike status of the current track
        """
        return self._command("toggleDislike")

    def change_video(self, video_id: Optional[str] = None, playlist_id: Optional[str] = None) -> requests.Response:
        """
        Play a specific video or playlist.

        Args:
            video_id: YouTube video ID to play, or None
            playlist_id: YouTube playlist ID to play, or None
        """
        return self._command("changeVideo", {"videoId": video_id, "playlistId": playlist_id})

    def update_endpoint(self, host: str, port: int = 9863) -> None:
        """
        Update the target YTMD host and port. Call this when the server address
        is not known at construction time (e.g. read from user settings).

        Args:
            host: hostname or IP address of the YTMD server
            port: port number (default 9863)
        """
        self.host = host
        self.port = port
        self.url = f"http://{self.host}:{self.port}/api/v1"

    def is_token_valid(self) -> bool:
        """
        Check whether the current token is accepted by YTMD.
        Returns False only on a definitive HTTP 401; network errors are treated
        as still-valid so transient failures don't trigger unnecessary re-auth.
        """
        if not self.token:
            return False
        try:
            resp = self.session.get(self.url + "/state", timeout=5)
            return resp.status_code != 401
        except Exception:
            return True

    def load_token(self, path: str) -> Optional[str]:
        """
        Load a previously saved token from *path* and register it on this
        instance via update_token(). Returns the token string, or None if the
        file does not exist or is empty.

        Args:
            path: file path where the token was persisted by save_token()
        """
        try:
            with open(path, 'r') as f:
                token = f.read().strip()
            if token:
                self.update_token(token)
                return token
        except FileNotFoundError:
            pass
        return None

    def save_token(self, path: str) -> None:
        """
        Persist the current token to *path* so it can be reloaded by
        load_token() after a restart.

        Args:
            path: destination file path
        """
        if not self.token:
            raise ValueError("No token to save — authenticate first")
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, 'w') as f:
            f.write(self.token)

    def clear_token(self, path: str) -> None:
        """
        Clear the in-memory token and remove *path* from disk.
        Use this when a token has been rejected (HTTP 401) to force
        re-authentication on the next connection attempt.

        Args:
            path: file path previously written by save_token()
        """
        self.token = None
        self.session.headers.pop("Authorization", None)
        try:
            os.remove(path)
        except OSError:
            pass

    def fetch_cover_art(self, url: str, timeout: int = 5) -> bytes:
        """
        Fetch raw image bytes from a cover-art URL returned by YTMD's state.
        Uses the SDK's shared HTTP session so connection pooling is reused.
        Encoding (e.g. base64) is left to the caller.

        Args:
            url (str): Full URL of the thumbnail/cover-art image.
            timeout (int): Request timeout in seconds (default 5).

        Returns:
            bytes: Raw image content.

        Raises:
            requests.HTTPError: If the server returns a non-2xx status.
            requests.RequestException: On any network error.
        """
        resp = self.session.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.content