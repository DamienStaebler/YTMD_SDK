import unittest
from ytmd_sdk import Parser
from ytmd_sdk.parser.queue import queueItem
from ytmd_sdk.parser.thumbnail import Thumbnail

class TestParser(unittest.TestCase):
    
    def test_parser(self):
        data = {}
        parser = Parser(data)
        self.assertEqual(parser.player_state.state, "Unknown")
        self.assertEqual(parser.player_state.video_progress, 0.0)
        self.assertEqual(parser.player_state.volume, 0)
        self.assertEqual(parser.player_state.muted, False)
        self.assertEqual(parser.player_state.adPlaying, False)
        self.assertEqual(parser.player_state.auto_play, False)
        self.assertEqual(parser.player_state.isGenerating, False)
        self.assertEqual(parser.player_state.isInfinite, False)
        self.assertEqual(parser.player_state.repeatMode, "Unknown")
        self.assertEqual(parser.player_state.selectedItemIndex, 0)
        self.assertEqual(parser.player_state.queue, [])

        self.assertEqual(parser.video_state.author, "")
        self.assertEqual(parser.video_state.channel_id, "")
        self.assertEqual(parser.video_state.title, "")
        self.assertEqual(parser.video_state.album, "")
        self.assertEqual(parser.video_state.album_id, "")
        self.assertEqual(parser.video_state.like_status, "Unknown")
        self.assertEqual(parser.video_state.duration_seconds, 0)
        self.assertEqual(parser.video_state.thumbnails, [])
        self.assertEqual(parser.video_state.id, "")

    def test_player_state(self):
        data = {
            "player": {
                "trackState": 1,
                "videoProgress": 13.2,
                "volume": 100,
                "muted": False,
                "adPlaying": True,
                "queue": {},
            }
        }
        parser = Parser(data)
        self.assertEqual(parser.player_state.state, "Playing")
        self.assertEqual(parser.player_state.video_progress, 13.2)
        self.assertEqual(parser.player_state.volume, 100)
        self.assertEqual(parser.player_state.muted, False)
        self.assertEqual(parser.player_state.adPlaying, True)
        self.assertEqual(parser.player_state.auto_play, False)
        self.assertEqual(parser.player_state.isGenerating, False)
        self.assertEqual(parser.player_state.isInfinite, False)
        self.assertEqual(parser.player_state.repeatMode, "Unknown")
        self.assertEqual(parser.player_state.selectedItemIndex, 0)
        self.assertEqual(parser.player_state.queue, [])

    def test_player_state_queue(self):
        data = {
            "player": {
                "queue": {
                    "autoplay": True,
                    "repeatMode": 1,
                    "selectedItemIndex": 2,
                    "items": [
                        {
                            "thumbnails": [{"url": "url1", "width": 100, "height": 100},
                                           {"url": "url2", "width": 200, "height": 200},
                                           {"url": "url3", "width": 300, "height": 300}],
                            "title": "title",
                            "author": "author",
                            "duration": "3:30",
                            "selected": True,
                            "videoId": "videoId",
                            "counterparts": None
                        },
                        {
                            "thumbnails": [{"url": "url4", "width": 100, "height": 100},
                                           {"url": "url5", "width": 200, "height": 200},
                                           {"url": "url6", "width": 300, "height": 300}],
                            "title": "title",
                            "author": "author",
                            "duration": "1:30",
                            "selected": False,
                            "videoId": "videoId",
                            "counterparts": None
                        }
                    ]
                }
            }
        }
        parser = Parser(data)
        self.assertEqual(parser.player_state.auto_play, True)
        # repeatMode and selectedItemIndex live in player.queue, not player
        self.assertEqual(parser.player_state.repeatMode, "All")
        self.assertEqual(parser.player_state.selectedItemIndex, 2)
        self.assertEqual(len(parser.player_state.queue), 2)
        self.assertIsInstance(parser.player_state.queue[0], queueItem)
        self.assertIsInstance(parser.player_state.queue[1], queueItem)

        self.assertIsInstance(parser.player_state.queue[0].thumbnails[0], Thumbnail)
        self.assertEqual(len(parser.player_state.queue[0].thumbnails), 3)

        self.assertEqual(parser.player_state.queue[0].thumbnails[0].url, "url1")
        self.assertEqual(parser.player_state.queue[0].thumbnails[0].width, 100)
        self.assertEqual(parser.player_state.queue[0].thumbnails[0].height, 100)
        self.assertEqual(parser.player_state.queue[0].title, "title")
        self.assertEqual(parser.player_state.queue[0].author, "author")
        self.assertEqual(parser.player_state.queue[0].duration, "3:30")
        self.assertEqual(parser.player_state.queue[0].selected, True)
        self.assertEqual(parser.player_state.queue[0].videoId, "videoId")
        self.assertEqual(parser.player_state.queue[0].counterparts, None)

    def test_video_state(self):
        data = {
            "video": {
                "author": "author",
                "channelId": "channelId",
                "title": "title",
                "album": "album",
                "albumId": "albumId",
                "likeStatus": 2,
                "thumbnails": [],
                "durationSeconds": 211,
                "id": "id"
            }
        }
        parser = Parser(data)
        self.assertEqual(parser.video_state.author, "author")
        self.assertEqual(parser.video_state.channel_id, "channelId")
        self.assertEqual(parser.video_state.title, "title")
        self.assertEqual(parser.video_state.album, "album")
        self.assertEqual(parser.video_state.album_id, "albumId")
        self.assertEqual(parser.video_state.like_status, "Like")
        self.assertEqual(parser.video_state.duration_seconds, 211)
        self.assertEqual(parser.video_state.thumbnails, [])
        self.assertEqual(parser.video_state.id, "id")

    def test_video_state_thumbnails(self):
        data = {
            "video": {
                "thumbnails": [{"url": "url1", "width": 100, "height": 100},
                               {"url": "url2", "width": 200, "height": 200},
                               {"url": "url3", "width": 300, "height": 300}],
            }
        }
        parser = Parser(data)
        self.assertEqual(len(parser.video_state.thumbnails), 3)
        self.assertIsInstance(parser.video_state.thumbnails[0], Thumbnail)
        self.assertIsInstance(parser.video_state.thumbnails[1], Thumbnail)
        self.assertIsInstance(parser.video_state.thumbnails[2], Thumbnail)

        self.assertEqual(parser.video_state.thumbnails[0].url, "url1")
        self.assertEqual(parser.video_state.thumbnails[0].width, 100)
        self.assertEqual(parser.video_state.thumbnails[0].height, 100)

        self.assertEqual(parser.video_state.thumbnails[1].url, "url2")
        self.assertEqual(parser.video_state.thumbnails[1].width, 200)
        self.assertEqual(parser.video_state.thumbnails[1].height, 200)

        self.assertEqual(parser.video_state.thumbnails[2].url, "url3")
        self.assertEqual(parser.video_state.thumbnails[2].width, 300)
        self.assertEqual(parser.video_state.thumbnails[2].height, 300)

if __name__ == '__main__':
    unittest.main()