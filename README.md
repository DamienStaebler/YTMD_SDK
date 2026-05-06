# YTMD SDK

Python SDK for controlling [YouTube Music Desktop App (YTMD)](https://ytmdesktop.app/) v2+
via its Companion Server API.

## Requirements

- Python 3.8+
- YTMD v2.0.0 or later (Companion Server must be enabled in YTMD settings)

## Installation

```
pip install ytmd-sdk
```

## Quick Start

```python
from ytmd_sdk import Events, YTMD, Parser
from time import sleep

# Construct the client with your application's identity.
ytmd = YTMD("my-app-id", "My App Name", "1.0.0")

# Authenticate — opens an approval popup in YTMD. The user has ~30 seconds to approve.
token = ytmd.authenticate()

# Persist the token yourself so you don't need to re-authenticate on the next run.
with open("/path/to/token.txt", "w") as f:
    f.write(token)

def on_connect():
    print("Connected to YTMD")

def on_disconnect():
    print("Disconnected from YTMD")

def on_state_update(data):
    parser = Parser(data)
    print(f"Track:    {parser.video_state.title} by {parser.video_state.author}")
    print(f"State:    {parser.player_state.state}")
    print(f"Progress: {parser.player_state.video_progress}s")
    print(f"Volume:   {parser.player_state.volume}")
    print(f"Repeat:   {parser.player_state.repeatMode}")

ytmd.register_event(Events.connect, on_connect)
ytmd.register_event(Events.disconnect, on_disconnect)
ytmd.register_event(Events.state_update, on_state_update)

ytmd.connect()
sleep(60)
```

On subsequent runs, load the saved token and check it is still valid before connecting:

```python
import os

ytmd = YTMD("my-app-id", "My App Name", "1.0.0")

token_path = "/path/to/token.txt"
token = None
if os.path.exists(token_path):
    token = open(token_path).read().strip() or None

if token:
    ytmd.update_token(token)

if not token or not ytmd.is_token_valid():
    token = ytmd.authenticate()
    with open(token_path, "w") as f:
        f.write(token)
```

## API Reference

### YTMD(app_id, app_name, app_version, host="127.0.0.1", port=9863, token=None, logging=False)

Constructs the client. All network calls use a shared `requests.Session` for connection pooling.

| Parameter | Type | Description |
|-----------|------|-------------|
| app_id | str | Unique identifier for your application (e.g. `"my-app"`) |
| app_name | str | Human-readable application name shown in YTMD's approval popup |
| app_version | str | Application version string |
| host | str | YTMD host address (default `"127.0.0.1"`) |
| port | int | YTMD Companion Server port (default `9863`) |
| token | str | Pre-existing token; skips authenticate() if provided |
| logging | bool | Enable python-socketio debug logging (default `False`) |

### Authentication

| Method | Returns | Description |
|--------|---------|-------------|
| `authenticate()` | `str` | Full auth handshake — requests a code, waits for user approval in YTMD (~30s), returns token |
| `update_token(token)` | `None` | Register a token on this instance and set the `Authorization` header |
| `revoke_token()` | `None` | Clear the in-memory token and `Authorization` header; does not touch the filesystem |
| `is_token_valid()` | `bool` | Returns `False` only on a definitive HTTP 401; treats network errors as valid to avoid unnecessary re-auth |

Token persistence (reading and writing token files) is the caller's responsibility.
The SDK provides `update_token()` to register a loaded token and `revoke_token()` to
clear it; file I/O should be implemented in your application layer.

### Connection

| Method | Description |
|--------|-------------|
| `register_event(event, callback)` | Bind a callback to a Socket.IO event (use `Events.*` constants) |
| `connect()` | Open a WebSocket connection to the YTMD realtime namespace |
| `update_endpoint(host, port=9863)` | Change the target host/port after construction (e.g. from user settings) |

### Player Commands

| Method | Description |
|--------|-------------|
| `toggle_playback()` | Play or pause |
| `play()` | Resume playback |
| `pause()` | Pause playback |
| `next()` | Skip to the next track |
| `previous()` | Go back to the previous track |
| `volume_up()` | Increase volume by 10% |
| `volume_down()` | Decrease volume by 10% |
| `set_volume(volume)` | Set volume (0-100) |
| `mute()` | Mute the player |
| `unmute()` | Unmute the player |
| `seek_to(time)` | Seek to a position in seconds |
| `shuffle()` | Toggle shuffle |
| `repeat_mode(mode)` | Set repeat mode: `0` = None, `1` = All, `2` = One |
| `play_index(index)` | Play a specific item in the queue by index |
| `toggle_like()` | Toggle the like status of the current track |
| `toggle_dislike()` | Toggle the dislike status of the current track |
| `change_video(video_id=None, playlist_id=None)` | Play a specific YouTube video or playlist by ID |

### State and Playlists

| Method | Returns | Description |
|--------|---------|-------------|
| `get_state()` | `Response` | Current player and video state as a JSON response |
| `get_playlists()` | `Response` | User's playlists as a JSON response |
| `get_version()` | `list[str]` | API versions supported by the connected YTMD instance |

### Cover Art

| Method | Returns | Description |
|--------|---------|-------------|
| `fetch_cover_art(url, timeout=5)` | `bytes` | Fetch raw image bytes from a thumbnail URL provided in the state update. Encoding (e.g. base64) is left to the caller. Raises `requests.HTTPError` on non-2xx responses. |

### Events

Use the `Events` class constants when calling `register_event()`:

| Constant | Socket.IO Event | Fired when |
|----------|----------------|------------|
| `Events.connect` | `connect` | WebSocket connection established |
| `Events.disconnect` | `disconnect` | WebSocket connection lost |
| `Events.connect_error` | `connect_error` | Connection attempt failed |
| `Events.error` | `error` | Server-side error |
| `Events.state_update` | `state-update` | Player state changes (track, volume, position, etc.) |
| `Events.playlist_created` | `playlist-created` | A new playlist was created |
| `Events.playlist_deleted` | `playlist-deleted` | A playlist was deleted |

### Parser

`Parser(data)` wraps the raw JSON dict received from a `state-update` event into typed objects.

```python
parser = Parser(data)

# PlayerState fields
parser.player_state.state            # "Playing", "Paused", "Buffering", or "Unknown"
parser.player_state.video_progress   # float, seconds elapsed
parser.player_state.volume           # int, 0-100
parser.player_state.muted            # bool
parser.player_state.adPlaying        # bool
parser.player_state.repeatMode       # "None", "All", "One", or "Unknown"
parser.player_state.auto_play        # bool
parser.player_state.isGenerating     # bool
parser.player_state.isInfinite       # bool
parser.player_state.selectedItemIndex  # int, index of the active item in the queue
parser.player_state.queue            # list[queueItem]

# VideoState fields
parser.video_state.id                # str, YouTube video ID
parser.video_state.title             # str
parser.video_state.author            # str, channel/artist name
parser.video_state.album             # str
parser.video_state.album_id          # str
parser.video_state.channel_id        # str
parser.video_state.like_status       # str: "Like", "Dislike", "Indifferent", or "Unknown"
parser.video_state.duration_seconds  # int
parser.video_state.thumbnails        # list[Thumbnail], ordered smallest to largest
```

Each `Thumbnail` has `.url` (str), `.width` (int), and `.height` (int).
The last item in `thumbnails` is always the highest-resolution image available.

## Change Log

### 1.2.1

**Token persistence moved to the application layer**

`save_token(path)`, `load_token(path)`, and `clear_token(path)` have been removed from
the `YTMD` class. Token file I/O is an application-level concern and does not belong in
a generic client library.

Callers are responsible for reading and writing the token file. Use `update_token(token)`
to register a loaded token on the SDK instance, and `revoke_token()` to clear it when a
token is rejected.

- `revoke_token()` replaces `clear_token(path)` for the in-memory side: it sets
  `self.token = None` and removes the `Authorization` header from the session. It does
  not touch the filesystem.

See the Quick Start section for a complete token persistence pattern.

### 1.2.0

**Token lifecycle management** _(removed in 1.2.1 — see above)_

The following methods were added in 1.2.0 and removed in 1.2.1 when token persistence
was moved to the application layer:

- `save_token(path)`, `load_token(path)`, `clear_token(path)`

Still present from this release:

- `is_token_valid()` makes a lightweight `GET /state` call to verify the current token
  is accepted by YTMD. It returns `False` only on a definitive HTTP 401; transient network
  failures return `True` so a temporary connection drop does not force unnecessary
  re-authentication.

**Cover art retrieval**

- `fetch_cover_art(url, timeout=5)` fetches raw image bytes from any thumbnail URL
  provided in the `state-update` payload. The SDK's shared HTTP session is reused for
  connection pooling. Encoding (e.g. converting to base64 for embedding in a UI) is
  intentionally left to the caller so the SDK remains format-agnostic. Raises
  `requests.HTTPError` on non-2xx responses and `requests.RequestException` on network
  failures.

  _Note_: YTMD does provide the asset URI so you can simply use the URI for retrieving cover art, pulling it as a byte array may improve performance in some applications.

**Video and playlist control**

- `change_video(video_id=None, playlist_id=None)` sends a `changeVideo` command to YTMD,
  allowing the caller to start a specific YouTube video or playlist by ID. Either argument
  may be `None` if not needed.

**Runtime endpoint reconfiguration**

- `update_endpoint(host, port=9863)` allows the target YTMD host and port to be changed
  after the client is constructed. This is useful when the server address is read from
  user-facing settings at runtime rather than being fixed at startup.

**Parser: VideoState thumbnails**

The `VideoState` object now exposes a `thumbnails` field containing a list of `Thumbnail`
objects parsed from the YTMD state payload. Each `Thumbnail` carries a `.url`, `.width`,
and `.height`. The thumbnails are ordered from smallest to largest, so `thumbnails[-1]`
is always the highest-resolution image available and is the recommended source for
cover art display.

### 1.0.0

Initial release. Covered basic connection, authentication handshake,
core playback commands, and the `Parser` class for `PlayerState` and `VideoState`.

## Bugs and Suggestions

If you have any bugs or suggestions, feel free to open an issue or a pull request.