"""Chromecast / Google Home speaker control via pychromecast."""

import asyncio
import time
from functools import partial
from typing import Optional

import pychromecast
from pychromecast import CastBrowser, SimpleCastListener


def _discover_sync(timeout: int) -> list[dict]:
    discovered: dict[str, pychromecast.Chromecast] = {}

    class Listener(SimpleCastListener):
        def add_cast(self, uuid, _service):
            cast = CastBrowser.devices.get(uuid)
            if cast:
                discovered[str(uuid)] = cast

    services, browser = pychromecast.discovery.discover_chromecasts(timeout=timeout)
    browser.stop_discovery()

    chromecasts, browser = pychromecast.get_chromecasts(timeout=timeout)
    browser.stop_discovery()

    result = []
    for cc in chromecasts:
        result.append({
            "name": cc.name,
            "model": cc.model_name,
            "host": cc.socket_client.host,
            "port": cc.socket_client.port,
            "uuid": str(cc.uuid),
            "cast_type": cc.cast_type,
        })
    return result


async def discover_devices(timeout: int = 5) -> list[dict]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_discover_sync, timeout))


def _get_cast(name: str, timeout: int = 5) -> pychromecast.Chromecast:
    chromecasts, browser = pychromecast.get_chromecasts(timeout=timeout)
    browser.stop_discovery()
    for cc in chromecasts:
        if cc.name.lower() == name.lower():
            cc.wait()
            return cc
    raise ValueError(f"Speaker '{name}' not found on the network")


def _status_sync(name: str) -> dict:
    cc = _get_cast(name)
    cs = cc.status
    ms = cc.media_controller.status
    return {
        "name": cc.name,
        "is_active_input": cs.is_active_input if cs else None,
        "is_stand_by": cs.is_stand_by if cs else None,
        "volume_level": round(cs.volume_level, 2) if cs else None,
        "volume_muted": cs.volume_muted if cs else None,
        "display_name": cs.display_name if cs else None,
        "media": {
            "state": ms.player_state if ms else None,
            "title": ms.title if ms else None,
            "artist": ms.artist if ms else None,
            "album": ms.album_name if ms else None,
            "content_id": ms.content_id if ms else None,
            "duration": ms.duration if ms else None,
            "current_time": ms.current_time if ms else None,
        } if ms else None,
    }


def _play_media_sync(name: str, url: str, content_type: str, title: Optional[str]) -> dict:
    cc = _get_cast(name)
    mc = cc.media_controller
    mc.play_media(url, content_type, title=title)
    mc.block_until_active()
    return {"status": "playing", "url": url, "speaker": name}


def _pause_sync(name: str) -> dict:
    cc = _get_cast(name)
    cc.media_controller.pause()
    return {"status": "paused", "speaker": name}


def _play_sync(name: str) -> dict:
    cc = _get_cast(name)
    cc.media_controller.play()
    return {"status": "playing", "speaker": name}


def _stop_sync(name: str) -> dict:
    cc = _get_cast(name)
    cc.media_controller.stop()
    return {"status": "stopped", "speaker": name}


def _set_volume_sync(name: str, level: float) -> dict:
    if not 0.0 <= level <= 1.0:
        raise ValueError("Volume must be between 0.0 and 1.0")
    cc = _get_cast(name)
    cc.set_volume(level)
    return {"speaker": name, "volume": level}


def _set_mute_sync(name: str, muted: bool) -> dict:
    cc = _get_cast(name)
    cc.set_volume_muted(muted)
    return {"speaker": name, "muted": muted}


def _quit_app_sync(name: str) -> dict:
    cc = _get_cast(name)
    cc.quit_app()
    return {"speaker": name, "status": "app_quit"}


async def get_status(name: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_status_sync, name))


async def play_media(name: str, url: str, content_type: str, title: Optional[str] = None) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_play_media_sync, name, url, content_type, title))


async def pause(name: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_pause_sync, name))


async def play(name: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_play_sync, name))


async def stop(name: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_stop_sync, name))


async def set_volume(name: str, level: float) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_set_volume_sync, name, level))


async def set_mute(name: str, muted: bool) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_set_mute_sync, name, muted))


async def quit_app(name: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, partial(_quit_app_sync, name))
