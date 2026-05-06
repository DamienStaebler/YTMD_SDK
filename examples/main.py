from ytmd_sdk import Events, YTMD, Parser
import time

ytmd = YTMD("touchportalytmd", "TouchPortalYTMD", "1.0.0")

key = ytmd.authenticate()
print(f"Key: {key}")
# ytmd.update_token("token")

def on_connect():
    print("Connected to YTMD")

def on_disconnect():
    print("Disconnected from YTMD")

def on_error(data):
    print("Error from YTMD: " + data)

def on_state_update(data):
    parser = Parser(data)
    print(f"Player: {parser.player_state}")
    print(f"Player State: {parser.player_state.state}")
    print(f"Player video progress: {parser.player_state.video_progress}")
    print(f"Player volume: {parser.player_state.volume}")
    print(f"Player muted: {parser.player_state.muted}")
    print(f"Player ad playing: {parser.player_state.adPlaying}")
    print(f"Player auto play: {parser.player_state.auto_play}")
    print(f"Player is generating: {parser.player_state.isGenerating}")
    print(f"Player is infinite: {parser.player_state.isInfinite}")
    print(f"Player repeat mode: {parser.player_state.repeatMode}")
    print(f"Player selected item index: {parser.player_state.selectedItemIndex}")
    print(f"Player queue: {parser.player_state.queue}")

ytmd.register_event(Events.connect, on_connect)
ytmd.register_event(Events.disconnect, on_disconnect)
ytmd.register_event(Events.error, on_error)
ytmd.register_event(Events.state_update, on_state_update)

ytmd.connect()
time.sleep(60)