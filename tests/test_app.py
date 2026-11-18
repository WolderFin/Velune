import asyncio
import io
import json
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timezone, timedelta
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace as Obj
from unittest.mock import AsyncMock, patch
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import HTTPError

import app


def session(source, playing=True, thumbnail=None, title="Track", artist="Artist", album="Album"):
    s = Obj(source_app_user_model_id=source)
    s.get_playback_info = lambda: Obj(playback_status=Obj(name="PLAYING" if playing else "PAUSED"))
    s.get_timeline_properties = lambda: Obj(position=timedelta(seconds=10), end_time=timedelta(seconds=100), last_updated_time=datetime.now(timezone.utc))
    s.try_get_media_properties_async = AsyncMock(return_value=Obj(title=title, artist=artist, album_title=album, thumbnail=thumbnail))
    return s


class OverlayTests(unittest.TestCase):
    def setUp(self):
        app.STATE.update(app.empty_state())
        app.COVERS.clear()
        app.SOURCE_STATES.clear()
        app.EXTERNAL_STATES.clear()
        app.SOURCES.clear()

    def test_selection_excludes_other_players_and_prefers_playing(self):
        browser, paused, playing = session("chrome.exe"), session("Yandex.Music", False), session("Yandex.Player")
        manager = Obj(get_sessions=lambda: [browser, paused, playing])
        self.assertIs(app.choose_session(manager), playing)
        self.assertIs(app.choose_session(manager, "CHROME.EXE"), browser)
        self.assertIs(app.choose_session(Obj(get_sessions=lambda: [browser])), browser)

    def test_automatic_selection_falls_back_to_playing_browser(self):
        paused = session("Yandex.Music", False)
        browser = session("browser.exe", True)
        manager = Obj(get_sessions=lambda: [paused, browser])
        self.assertIs(app.choose_session(manager), browser)

    def test_empty_session_clears_every_field(self):
        app.STATE.update(title="Old", source="Old", cover="Old", playing=True)
        state = asyncio.run(app.read_state(Obj(get_sessions=lambda: [])))
        self.assertEqual(state["source"], "")
        self.assertEqual(state["cover"], "")
        self.assertFalse(state["playing"])
        self.assertTrue(state["available"])

    def test_media_text_preserves_emoji_and_repairs_utf16_surrogates(self):
        self.assertEqual(app.clean_text("LAVA 🔺 \ue001"), "LAVA 🔺 \ue001")
        self.assertEqual(app.clean_text("rocket \ud83d\ude80"), "rocket 🚀")
        self.assertEqual(app.clean_text("broken \ud83d"), "broken \ufffd")
        state = asyncio.run(app.read_state(Obj(get_sessions=lambda: [
            session("browser.exe", title="Song 🔥 \ue001", artist="Artist \ud83d")
        ])))
        self.assertEqual(state["title"], "Song 🔥 \ue001")
        self.assertEqual(state["artist"], "Artist \ufffd")
        state["artist"].encode("utf-8")

    def test_safe_log_handles_console_without_emoji_support(self):
        output = io.BytesIO()
        console = io.TextIOWrapper(output, encoding="cp1251", errors="strict")
        with patch.object(sys, "stdout", console):
            app.safe_log("[TRACK]", "Song 🔥")
            console.flush()
        self.assertIn(b"\\U0001f525", output.getvalue())

    def test_json_bytes_cannot_be_broken_by_provider_unicode(self):
        payload = json.loads(app.json_bytes({"title": "Broken \ud83d"}))
        self.assertEqual(payload["title"], "Broken ?")

    def test_streamerbot_message_formats_track_and_empty_state(self):
        self.assertEqual(app.streamerbot_message({"title": "Track", "artist": "Artist"}),
                         "Сейчас играет: Artist — Track")
        self.assertEqual(app.streamerbot_message({"title": "Track", "artist": ""}),
                         "Сейчас играет: Track")
        self.assertEqual(app.streamerbot_message(app.empty_state()),
                         "Сейчас ничего не играет.")

    def test_cover_identity_and_missing_thumbnail(self):
        old = app.cover_url(b"\x89PNG old")
        self.assertEqual(old, app.cover_url(b"\x89PNG old"))
        self.assertEqual(len(app.COVERS), 1)
        app.STATE["cover"] = old
        state = asyncio.run(app.read_state(Obj(get_sessions=lambda: [session("Yandex.Music")])))
        self.assertEqual(state["cover"], "")
        for i in range(40):
            app.cover_url(b"\x89PNG" + bytes([i]))
        self.assertEqual(len(app.COVERS), 32)

    def test_source_snapshots_are_independent(self):
        app.SOURCE_STATES["Brave"] = {**app.empty_state(), "title": "Browser", "source": "Brave", "available": True, "updated_at": time.time()}
        app.STATE.update(title="Yandex", available=True, updated_at=time.time())
        self.assertEqual(app.snapshot("Brave")["title"], "Browser")
        self.assertEqual(app.snapshot()["title"], "Yandex")
        self.assertFalse(app.snapshot("Missing")["available"])

    def test_poll_failure_clears_state(self):
        app.STATE.update(title="Old", playing=True, updated_at=time.time(), available=True)
        stop = threading.Event()
        async def fail(*args):
            stop.set()
            raise RuntimeError("test failure")
        with patch.object(app.MediaManager, "request_async", new=AsyncMock(return_value=object())), patch.object(app, "read_state", new=fail):
            asyncio.run(app.poll(None, stop))
        self.assertEqual(app.snapshot(), app.empty_state())

    def test_http_cover_and_stale_health(self):
        url = app.cover_url(b"\x89PNG test")
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(base + "/api/sources") as response:
                self.assertEqual(json.load(response)["sources"], [])
            app.SOURCE_STATES["Browser with spaces"] = {**app.empty_state(), "title": "Other", "available": True, "updated_at": time.time()}
            with urlopen(base + "/api/current?source=Browser%20with%20spaces") as response:
                self.assertEqual(json.load(response)["title"], "Other")
            with urlopen(base + "/api/streamerbot?source=Browser%20with%20spaces") as response:
                self.assertEqual(response.headers["Content-Type"], "text/plain; charset=utf-8")
                self.assertEqual(response.read().decode(), "Сейчас играет: Other")
            with urlopen(base + "/api/streamerbot?source=Browser%20with%20spaces&format=json") as response:
                self.assertEqual(json.load(response)["message"], "Сейчас играет: Other")
            with urlopen(base + "/overlay?theme=neko") as response:
                self.assertIn(b"widget.css", response.read())
            with urlopen(base + "/pixel.ttf") as response:
                self.assertGreater(len(response.read()), 1000)
            with urlopen(base + url) as response:
                self.assertEqual(response.read(), b"\x89PNG test")
                self.assertEqual(response.headers["Content-Type"], "image/png")
            with self.assertRaises(HTTPError) as failure:
                urlopen(base + "/health")
            self.assertEqual(failure.exception.code, 503)
            failure.exception.close()
            app.STATE.update(updated_at=time.time(), available=True)
            with urlopen(base + "/health") as response:
                self.assertTrue(json.load(response)["ok"])
            app.STATE.update(title="Old", playing=True, updated_at=time.time() - 10)
            with urlopen(base + "/api/current") as response:
                self.assertEqual(json.load(response)["title"], "")
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_browser_bridge_supplies_playing_track(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            payload = json.dumps({"source": "browser:vk.com", "title": "VK Track",
                                  "artist": "Artist", "playing": True}).encode()
            request = Request(f"http://127.0.0.1:{server.server_port}/api/browser-track",
                              data=payload, method="POST",
                              headers={"Content-Type": "application/json",
                                       "Origin": "chrome-extension://test"})
            with urlopen(request) as response:
                self.assertTrue(json.load(response)["ok"])
            self.assertEqual(app.snapshot()["title"], "VK Track")
            self.assertEqual(app.snapshot("browser:vk.com")["artist"], "Artist")
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_custom_css_api_persists_and_resets_styles(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(
                app, "CUSTOM_CSS_PATH", Path(folder) / "custom.css"):
            server = ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                css = ".title { color: hotpink; }"
                request = Request(base + "/api/custom-css", data=css.encode(), method="POST",
                                  headers={"Content-Type": "text/css; charset=utf-8"})
                with urlopen(request) as response:
                    self.assertTrue(json.load(response)["ok"])
                with urlopen(base + "/api/custom-css") as response:
                    self.assertEqual(response.headers["Content-Type"], "text/css; charset=utf-8")
                    self.assertEqual(response.read().decode(), css)
                request = Request(base + "/api/custom-css", data=b"", method="POST",
                                  headers={"Content-Type": "text/css; charset=utf-8"})
                with urlopen(request) as response:
                    self.assertTrue(json.load(response)["ok"])
                self.assertEqual(app.read_custom_css(), "")
            finally:
                server.shutdown()
                server.server_close()
                worker.join()


if __name__ == "__main__":
    unittest.main()
