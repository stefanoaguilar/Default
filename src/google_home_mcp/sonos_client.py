"""Sonos speaker control via SoCo."""

import asyncio
from functools import partial
from typing import Optional

import soco
from soco import SoCo


def _find_player(name: str) -> SoCo:
    devices = soco.discover() or set()
    for d in devices:
        if d.player_name.lower() == name.lower():
            return d
    raise ValueError(f"Sonos speaker '{name}' not found. Use discover_sonos_speakers first.")


def _discover_sync(timeout: int) -> list[dict]:
    devices = soco.discover(timeout=timeout) or set()
    result = []
    for d in sorted(devices, key=lambda x: x.player_name):
        item: dict = {
            "name": d.player_name,
            "ip": d.ip_address,
            "uid": d.uid,
            "volume": d.volume,
            "muted": d.mute,
            "is_coordinator": d.is_coordinator,
            "group_coordinator": d.group.coordinator.player_name if d.group else None,
            "group_members": [m.player_name for m in d.group.members] if d.group else [],
        }
        try:
            transport = d.get_current_transport_info()
            item["playback_state"] = transport.get("current_transport_state")
        except Exception:
            pass
        try:
            track = d.get_current_track_info()
            item["current_track"] = {
                "title": track.get("title"),
                "artist": track.get("artist"),
                "album": track.get("album"),
                "duration": track.get("duration"),
                "position": track.get("position"),
            }
        except Exception:
            pass
        result.append(item)
    return result


def _get_status_sync(name: str) -> dict:
    d = _find_player(name)
    transport = d.get_current_transport_info()
    track = d.get_current_track_info()
    return {
        "name": d.player_name,
        "ip": d.ip_address,
        "volume": d.volume,
        "muted": d.mute,
        "bass": d.bass,
        "treble": d.treble,
        "playback_state": transport.get("current_transport_state"),
        "is_coordinator": d.is_coordinator,
        "group_coordinator": d.group.coordinator.player_name if d.group else None,
        "group_members": [m.player_name for m in d.group.members] if d.group else [],
        "current_track": {
            "title": track.get("title"),
            "artist": track.get("artist"),
            "album": track.get("album"),
            "album_art": track.get("album_art"),
            "duration": track.get("duration"),
            "position": track.get("position"),
            "playlist_position": track.get("playlist_position"),
        },
    }


def _play_sync(name: str) -> dict:
    _find_player(name).play()
    return {"speaker": name, "status": "playing"}


def _pause_sync(name: str) -> dict:
    _find_player(name).pause()
    return {"speaker": name, "status": "paused"}


def _stop_sync(name: str) -> dict:
    _find_player(name).stop()
    return {"speaker": name, "status": "stopped"}


def _next_sync(name: str) -> dict:
    _find_player(name).next()
    return {"speaker": name, "action": "next_track"}


def _previous_sync(name: str) -> dict:
    _find_player(name).previous()
    return {"speaker": name, "action": "previous_track"}


def _set_volume_sync(name: str, volume: int) -> dict:
    if not 0 <= volume <= 100:
        raise ValueError("Volume must be between 0 and 100")
    _find_player(name).volume = volume
    return {"speaker": name, "volume": volume}


def _set_mute_sync(name: str, muted: bool) -> dict:
    _find_player(name).mute = muted
    return {"speaker": name, "muted": muted}


def _play_uri_sync(name: str, uri: str, title: str) -> dict:
    d = _find_player(name)
    d.play_uri(uri=uri, title=title)
    return {"speaker": name, "uri": uri, "status": "playing"}


def _get_queue_sync(name: str, max_items: int) -> dict:
    d = _find_player(name)
    queue = d.get_queue(max_items=max_items)
    return {
        "speaker": name,
        "queue_length": len(queue),
        "items": [
            {
                "position": i + 1,
                "title": item.title,
                "artist": getattr(item, "creator", None),
                "album": getattr(item, "album", None),
                "uri": item.resources[0].uri if item.resources else None,
            }
            for i, item in enumerate(queue)
        ],
    }


def _clear_queue_sync(name: str) -> dict:
    _find_player(name).clear_queue()
    return {"speaker": name, "queue": "cleared"}


def _play_from_queue_sync(name: str, index: int) -> dict:
    _find_player(name).play_from_queue(index)
    return {"speaker": name, "playing_queue_index": index}


def _join_group_sync(name: str, coordinator_name: str) -> dict:
    player = _find_player(name)
    coordinator = _find_player(coordinator_name)
    player.join(coordinator)
    return {"speaker": name, "joined_group_of": coordinator_name}


def _unjoin_sync(name: str) -> dict:
    _find_player(name).unjoin()
    return {"speaker": name, "status": "unjoined_from_group"}


def _set_bass_sync(name: str, bass: int) -> dict:
    if not -10 <= bass <= 10:
        raise ValueError("Bass must be between -10 and 10")
    _find_player(name).bass = bass
    return {"speaker": name, "bass": bass}


def _set_treble_sync(name: str, treble: int) -> dict:
    if not -10 <= treble <= 10:
        raise ValueError("Treble must be between -10 and 10")
    _find_player(name).treble = treble
    return {"speaker": name, "treble": treble}


def _run(fn, *args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, partial(fn, *args))


async def discover(timeout: int = 5) -> list[dict]:
    return await _run(_discover_sync, timeout)

async def get_status(name: str) -> dict:
    return await _run(_get_status_sync, name)

async def play(name: str) -> dict:
    return await _run(_play_sync, name)

async def pause(name: str) -> dict:
    return await _run(_pause_sync, name)

async def stop(name: str) -> dict:
    return await _run(_stop_sync, name)

async def next_track(name: str) -> dict:
    return await _run(_next_sync, name)

async def previous_track(name: str) -> dict:
    return await _run(_previous_sync, name)

async def set_volume(name: str, volume: int) -> dict:
    return await _run(_set_volume_sync, name, volume)

async def set_mute(name: str, muted: bool) -> dict:
    return await _run(_set_mute_sync, name, muted)

async def play_uri(name: str, uri: str, title: str = "") -> dict:
    return await _run(_play_uri_sync, name, uri, title)

async def get_queue(name: str, max_items: int = 100) -> dict:
    return await _run(_get_queue_sync, name, max_items)

async def clear_queue(name: str) -> dict:
    return await _run(_clear_queue_sync, name)

async def play_from_queue(name: str, index: int) -> dict:
    return await _run(_play_from_queue_sync, name, index)

async def join_group(name: str, coordinator_name: str) -> dict:
    return await _run(_join_group_sync, name, coordinator_name)

async def unjoin(name: str) -> dict:
    return await _run(_unjoin_sync, name)

async def set_bass(name: str, bass: int) -> dict:
    return await _run(_set_bass_sync, name, bass)

async def set_treble(name: str, treble: int) -> dict:
    return await _run(_set_treble_sync, name, treble)
