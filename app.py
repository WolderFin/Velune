import argparse
import asyncio
import hashlib
import json
import os
import threading
import time
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit, parse_qs

from winrt.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winrt.windows.storage.streams import DataReader

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
STALE_AFTER = 5
LOCK = threading.Lock()
COVERS = OrderedDict()
SOURCE_STATES = {}
SOURCES = []
DEFAULT_SOURCE = None


def empty_state():
    return dict(title="", artist="", album="", cover="", position=0,
                duration=0, playing=False, source="", updated_at=0, available=False)


STATE = empty_state()


async def thumb(ref):
    if not ref:
        return None
    stream = reader = None
    try:
        stream = await ref.open_read_async()
        size = int(stream.size)
        if not size or size > 10 * 1024 * 1024:
            return None
        reader = DataReader(stream)
        loaded = await reader.load_async(size)
        if loaded != size:
            return None
        data = bytearray(size)
        reader.read_bytes(data)
        return bytes(data)
    except Exception:
        return None
    finally:
        if reader is not None:
            reader.close()
        elif stream is not None:
            stream.close()


def cover_url(data):
    if not data:
        return ""
    if data.startswith(b"\xff\xd8\xff"):
        mime = "image/jpeg"
    elif data.startswith(b"\x89PNG"):
        mime = "image/png"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        mime = "image/webp"
    else:
        return ""
    key = hashlib.sha256(data).hexdigest()
    with LOCK:
        COVERS[key] = (data, mime)
        COVERS.move_to_end(key)
        while len(COVERS) > 32:
            COVERS.popitem(last=False)
    return "/covers/" + key


def is_playing(session):
    status = session.get_playback_info().playback_status
    return getattr(status, "name", str(status)).upper() == "PLAYING"


def choose_session(manager, source=None):
    sessions = list(manager.get_sessions())
    matches = [s for s in sessions if
               (source.casefold() in s.source_app_user_model_id.casefold() if source
                else "yandex" in s.source_app_user_model_id.casefold())]
    return next((s for s in matches if is_playing(s)), matches[0] if matches else None)


async def read_state(manager, source=None):
    session = choose_session(manager, source)
    if session is None:
        return {**empty_state(), "updated_at": time.time(), "available": True}
    props = await session.try_get_media_properties_async()
    timeline = session.get_timeline_properties()
    playing = is_playing(session)
    position = max(0, timeline.position.total_seconds())
    duration = max(0, timeline.end_time.total_seconds())
    if playing:
        updated = timeline.last_updated_time
        if hasattr(updated, "timestamp"):
            position += max(0, time.time() - updated.timestamp())
        elif hasattr(updated, "universal_time"):
            position += max(0, time.time() - (updated.universal_time / 10_000_000 - 11644473600))
    if duration:
        position = min(position, duration)
    return dict(title=props.title or "", artist=props.artist or "",
                album=props.album_title or "", cover=cover_url(await thumb(props.thumbnail)),
                position=position, duration=duration, playing=playing,
                source=session.source_app_user_model_id, updated_at=time.time(), available=True)


async def poll(source, stop):
    manager = None
    last = None
    while not stop.is_set():
        try:
            if manager is None:
                manager = await MediaManager.request_async()
            current = await asyncio.wait_for(read_state(manager, source), timeout=3)
            sessions = list(manager.get_sessions())
            grouped = {}
            for session in sessions:
                grouped.setdefault(session.source_app_user_model_id, []).append(session)
            async def read_source(source_id, items):
                try:
                    state = await asyncio.wait_for(read_state(SimpleNamespace(get_sessions=lambda: items), source_id), 3)
                except Exception:
                    state = empty_state()
                return source_id, state
            results = await asyncio.gather(*(read_source(key, items) for key, items in grouped.items()))
            states = dict(results)
            sources = [dict(id=key, title=value["title"], artist=value["artist"], playing=value["playing"]) for key, value in results]
            with LOCK:
                STATE.update(current)
                SOURCE_STATES.clear()
                SOURCE_STATES.update(states)
                SOURCES[:] = sources
            key = (current["source"], current["title"], current["artist"], current["album"])
            if key != last and current["title"]:
                print(f"[TRACK] {current['artist']} — {current['title']}")
            last = key
        except Exception as error:
            manager = None
            with LOCK:
                STATE.update(empty_state())
                SOURCE_STATES.clear()
                SOURCES.clear()
            print("[ERROR]", repr(error))
        await asyncio.sleep(1)


def snapshot(source=None):
    with LOCK:
        result = dict(SOURCE_STATES.get(source, empty_state()) if source else STATE)
    if time.time() - result["updated_at"] > STALE_AFTER:
        return empty_state()
    return result


class Handler(BaseHTTPRequestHandler):
    def send(self, data, mime, status=200):
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlsplit(self.path)
        path = url.path
        pages = {"/": ("index.html", "text/html; charset=utf-8"),
                 "/overlay": ("overlay.html", "text/html; charset=utf-8"),
                 "/widget.css": ("widget.css", "text/css; charset=utf-8"),
                 "/velune.png": ("velune.png", "image/png"),
                 "/velune.ico": ("velune.ico", "image/x-icon"),
                 "/wolderfin-logo.svg": ("wolderfin-logo.svg", "image/svg+xml"),
                 "/pixel.ttf": ("pixel.ttf", "font/ttf")}
        if path in pages:
            filename, mime = pages[path]
            return self.send((STATIC / filename).read_bytes(), mime)
        if path == "/api/sources":
            with LOCK:
                sources = list(SOURCES)
            return self.send(json.dumps({"sources": sources, "available": snapshot()["available"], "default_source": DEFAULT_SOURCE}, ensure_ascii=False).encode(), "application/json; charset=utf-8")
        if path == "/api/current":
            return self.send(json.dumps(snapshot(parse_qs(url.query).get("source", [None])[0]), ensure_ascii=False).encode(), "application/json; charset=utf-8")
        if path.startswith("/covers/"):
            with LOCK:
                image = COVERS.get(path.removeprefix("/covers/"))
            if image:
                return self.send(*image)
        if path == "/health":
            healthy = snapshot()["available"]
            return self.send(json.dumps({"ok": healthy}).encode(), "application/json", 200 if healthy else 503)
        self.send(b"", "text/plain", 404)

    def log_message(self, *args):
        pass


async def list_sources():
    manager = await MediaManager.request_async()
    for session in manager.get_sessions():
        props = await session.try_get_media_properties_async()
        print(f"{session.source_app_user_model_id}: {props.artist} — {props.title}")


def main():
    global DEFAULT_SOURCE
    parser = argparse.ArgumentParser(description="Windows media overlay for OBS")
    parser.add_argument("--headless", action="store_true", help="Run only the OBS server without a settings window")
    parser.add_argument("--source", help="Match a media session source ID (case insensitive)")
    parser.add_argument("--list-sources", action="store_true", help="List active media session sources and exit")
    args = parser.parse_args()
    if args.list_sources:
        asyncio.run(list_sources())
        return
    DEFAULT_SOURCE = args.source
    stop = threading.Event()
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    except OSError as error:
        if args.headless:
            raise
        show_error("Не удалось запустить Velune. Возможно, программа уже открыта или порт 8765 занят.\n\n" + str(error))
        return 1
    worker = threading.Thread(target=lambda: asyncio.run(poll(args.source, stop)), daemon=True)
    http_worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    http_worker.start()
    background = None
    try:
        if args.headless:
            print("Velune OBS server: http://127.0.0.1:8765")
            while not stop.wait(1):
                pass
        else:
            import webview
            import ctypes
            app_id = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
            app_id.argtypes = [ctypes.c_wchar_p]
            app_id("WolderFin.Velune")
            storage = Path(os.environ.get("LOCALAPPDATA", str(ROOT))) / "MusicStudio" / "WebView"
            storage.mkdir(parents=True, exist_ok=True)
            from background import BackgroundController, DesktopAPI
            background = BackgroundController(STATIC / "velune.png")
            window = webview.create_window("Velune — настройки OBS", "http://127.0.0.1:8765/",
                                  width=1200, height=900, min_size=(800, 650),
                                  background_color="#101114", text_select=True, js_api=DesktopAPI(background))
            background.attach(window)
            webview.start(background.start, gui="edgechromium", private_mode=False, storage_path=str(storage),
                          icon=str(STATIC / "velune.ico"))
    except KeyboardInterrupt:
        pass
    except Exception as error:
        if args.headless:
            raise
        show_error("Не удалось открыть окно Velune. Установите Microsoft Edge WebView2 Runtime.\n\n" + str(error))
        return 1
    finally:
        if background:
            background.stop()
        stop.set()
        server.shutdown()
        server.server_close()
        http_worker.join(timeout=2)
        worker.join(timeout=7)
    return 0


def show_error(message):
    import ctypes
    ctypes.windll.user32.MessageBoxW(None, message, "Velune", 0x10)


if __name__ == "__main__":
    raise SystemExit(main())
