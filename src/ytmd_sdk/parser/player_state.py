from .converters import state_converter, repeatMode_converter
from .queue import queueItem
from typing import Annotated

class PlayerState(object):
    state: str = "Unknown"
    """player state"""
    video_progress: float = 0.0
    """video progress"""
    volume: int = 0
    """volume"""
    muted: bool = False
    """muted"""
    adPlaying: bool = False
    """ad playing"""
    queue: list[queueItem] = []
    """queue"""
    auto_play: bool = False
    """auto play"""
    isGenerating: bool = False
    """is generating"""
    isInfinite: bool = False
    """is infinite"""
    repeatMode: str = "Unknown"
    """repeat mode"""
    selectedItemIndex: int = 0
    """selected item index"""

    def __init__(self, data) -> None:
        self.state = state_converter.get(data.get("trackState", -1), "Unknown")
        self.video_progress = data.get("videoProgress", 0.0)
        self.volume = data.get("volume", 0)
        self.muted = data.get("muted", False)
        self.adPlaying = data.get("adPlaying", False)
        self.auto_play = data.get("queue", {}).get("autoplay", False)
        self.queue = [queueItem(item) for item in data.get("queue", {}).get("items", [])]
        self.isGenerating = data.get("isGenerating", False)
        self.isInfinite = data.get("isInfinite", False)
        self.repeatMode = repeatMode_converter.get(data.get("queue", {}).get("repeatMode", -1), "Unknown")
        self.selectedItemIndex = data.get("queue", {}).get("selectedItemIndex", 0)

    def __str__(self) -> str:
        return str({
                "State": self.state,
                "Video Progress": self.video_progress,
                "Volume": self.volume,
                "Muted": self.muted,
                "Ad Playing": self.adPlaying,
                "Auto Play": self.auto_play,
                "Queue": self.queue,
                "Is Generating": self.isGenerating,
                "Is Infinite": self.isInfinite,
                "Repeat Mode": self.repeatMode,
                "Selected Item Index": self.selectedItemIndex
              })