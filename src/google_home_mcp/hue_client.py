"""Philips Hue light control via phue."""

import asyncio
import colorsys
import os
from functools import partial
from typing import Optional

import httpx
from phue import Bridge, PhueRegistrationException


def _get_bridge() -> Bridge:
    ip = os.getenv("HUE_BRIDGE_IP")
    if not ip:
        raise RuntimeError(
            "HUE_BRIDGE_IP not set. Run discover_hue_bridge to find the bridge IP, "
            "then set it in your .env file."
        )
    return Bridge(ip)


def _rgb_to_hue_params(r: int, g: int, b: int) -> dict:
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return {
        "hue": int(h * 65535),
        "sat": int(s * 254),
        "bri": max(1, int(v * 254)),
    }


def _kelvin_to_mireds(kelvin: int) -> int:
    return max(153, min(500, int(1_000_000 / kelvin)))


def _format_light(light) -> dict:
    state = light.state
    result: dict = {
        "id": light.light_id,
        "name": light.name,
        "type": light.type,
        "model": light.modelid,
        "on": state.get("on"),
        "reachable": state.get("reachable"),
        "brightness_pct": round(state["bri"] / 254 * 100) if "bri" in state else None,
    }
    if "ct" in state and state.get("colormode") == "ct":
        result["color_temp_kelvin"] = int(1_000_000 / state["ct"]) if state["ct"] else None
        result["color_temp_mireds"] = state["ct"]
    if "hue" in state and state.get("colormode") == "hs":
        result["hue"] = state["hue"]
        result["saturation"] = state["sat"]
    if "xy" in state:
        result["xy"] = state["xy"]
    result["colormode"] = state.get("colormode")
    return result


def _format_group(group) -> dict:
    return {
        "id": group.group_id,
        "name": group.name,
        "type": group.type,
        "on": group.action.get("on"),
        "brightness_pct": round(group.action["bri"] / 254 * 100) if "bri" in group.action else None,
        "lights": [int(lid) for lid in group.lights],
    }


def _format_scene(scene) -> dict:
    return {
        "id": scene.scene_id,
        "name": scene.name,
        "group": scene.group,
        "lights": [int(lid) for lid in (scene.lights or [])],
    }


# ── Discovery ─────────────────────────────────────────────────────────────────

def _discover_bridges_sync() -> list[dict]:
    with httpx.Client(timeout=5) as client:
        resp = client.get("https://discovery.meethue.com/")
        resp.raise_for_status()
        return [{"id": b["id"], "ip": b["internalipaddress"]} for b in resp.json()]


# ── Lights ────────────────────────────────────────────────────────────────────

def _list_lights_sync() -> list[dict]:
    b = _get_bridge()
    return [_format_light(light) for light in b.lights]


def _get_light_sync(name_or_id) -> dict:
    b = _get_bridge()
    light = b.get_light_objects("name").get(name_or_id) or b.get_light_objects("id").get(
        int(name_or_id) if str(name_or_id).isdigit() else -1
    )
    if light is None:
        raise ValueError(f"Light '{name_or_id}' not found")
    return _format_light(light)


def _set_light_sync(name_or_id, state: dict) -> dict:
    b = _get_bridge()
    b.set_light(name_or_id, state)
    return {"light": name_or_id, "applied": state}


def _turn_on_light_sync(name_or_id, transition_seconds: float) -> dict:
    b = _get_bridge()
    b.set_light(name_or_id, {"on": True, "transitiontime": int(transition_seconds * 10)})
    return {"light": name_or_id, "on": True}


def _turn_off_light_sync(name_or_id, transition_seconds: float) -> dict:
    b = _get_bridge()
    b.set_light(name_or_id, {"on": True, "bri": 0, "transitiontime": int(transition_seconds * 10)})
    b.set_light(name_or_id, {"on": False, "transitiontime": int(transition_seconds * 10)})
    return {"light": name_or_id, "on": False}


def _set_brightness_sync(name_or_id, percent: float, transition_seconds: float) -> dict:
    if not 0 <= percent <= 100:
        raise ValueError("Brightness must be 0–100")
    bri = max(1, int(percent / 100 * 254))
    b = _get_bridge()
    b.set_light(name_or_id, {"on": True, "bri": bri, "transitiontime": int(transition_seconds * 10)})
    return {"light": name_or_id, "brightness_pct": percent, "bri": bri}


def _set_color_rgb_sync(name_or_id, r: int, g: int, b_val: int, transition_seconds: float) -> dict:
    params = _rgb_to_hue_params(r, g, b_val)
    params["on"] = True
    params["transitiontime"] = int(transition_seconds * 10)
    b = _get_bridge()
    b.set_light(name_or_id, params)
    return {"light": name_or_id, "rgb": [r, g, b_val], **params}


def _set_color_temp_sync(name_or_id, kelvin: int, transition_seconds: float) -> dict:
    if not 2000 <= kelvin <= 6500:
        raise ValueError("Color temperature must be between 2000 K (warm) and 6500 K (cool)")
    ct = _kelvin_to_mireds(kelvin)
    b = _get_bridge()
    b.set_light(name_or_id, {"on": True, "ct": ct, "transitiontime": int(transition_seconds * 10)})
    return {"light": name_or_id, "color_temp_kelvin": kelvin, "color_temp_mireds": ct}


# ── Groups ────────────────────────────────────────────────────────────────────

def _list_groups_sync() -> list[dict]:
    b = _get_bridge()
    return [_format_group(g) for g in b.groups]


def _set_group_sync(name_or_id, state: dict) -> dict:
    b = _get_bridge()
    b.set_group(name_or_id, state)
    return {"group": name_or_id, "applied": state}


def _turn_on_group_sync(name_or_id, brightness_pct: Optional[float], transition_seconds: float) -> dict:
    state: dict = {"on": True, "transitiontime": int(transition_seconds * 10)}
    if brightness_pct is not None:
        state["bri"] = max(1, int(brightness_pct / 100 * 254))
    b = _get_bridge()
    b.set_group(name_or_id, state)
    return {"group": name_or_id, "on": True, "brightness_pct": brightness_pct}


def _turn_off_group_sync(name_or_id, transition_seconds: float) -> dict:
    b = _get_bridge()
    b.set_group(name_or_id, {"on": False, "transitiontime": int(transition_seconds * 10)})
    return {"group": name_or_id, "on": False}


def _set_group_color_temp_sync(name_or_id, kelvin: int, transition_seconds: float) -> dict:
    if not 2000 <= kelvin <= 6500:
        raise ValueError("Color temperature must be between 2000 K and 6500 K")
    ct = _kelvin_to_mireds(kelvin)
    b = _get_bridge()
    b.set_group(name_or_id, {"on": True, "ct": ct, "transitiontime": int(transition_seconds * 10)})
    return {"group": name_or_id, "color_temp_kelvin": kelvin, "color_temp_mireds": ct}


def _set_group_color_rgb_sync(name_or_id, r: int, g: int, b_val: int, transition_seconds: float) -> dict:
    params = _rgb_to_hue_params(r, g, b_val)
    params["on"] = True
    params["transitiontime"] = int(transition_seconds * 10)
    b = _get_bridge()
    b.set_group(name_or_id, params)
    return {"group": name_or_id, "rgb": [r, g, b_val]}


# ── Scenes ────────────────────────────────────────────────────────────────────

def _list_scenes_sync() -> list[dict]:
    b = _get_bridge()
    return [_format_scene(s) for s in b.scenes]


def _activate_scene_sync(group_name: str, scene_name: str) -> dict:
    b = _get_bridge()
    b.run_scene(group_name=group_name, scene_name=scene_name)
    return {"group": group_name, "scene": scene_name, "activated": True}


# ── Bridge setup ──────────────────────────────────────────────────────────────

def _connect_bridge_sync(ip: str) -> dict:
    try:
        b = Bridge(ip)
        b.connect()
        return {
            "connected": True,
            "ip": ip,
            "message": "Bridge connected. Credentials saved to ~/.python_hue",
            "next_step": f"Add HUE_BRIDGE_IP={ip} to your .env file",
        }
    except PhueRegistrationException:
        return {
            "connected": False,
            "error": "Press the button on the Hue bridge first, then retry within 30 seconds",
        }


# ── Async wrappers ────────────────────────────────────────────────────────────

def _run(fn, *args):
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, partial(fn, *args))


async def discover_bridges() -> list[dict]:
    return await _run(_discover_bridges_sync)

async def connect_bridge(ip: str) -> dict:
    return await _run(_connect_bridge_sync, ip)

async def list_lights() -> list[dict]:
    return await _run(_list_lights_sync)

async def get_light(name_or_id) -> dict:
    return await _run(_get_light_sync, name_or_id)

async def turn_on_light(name_or_id, transition_seconds: float = 0.4) -> dict:
    return await _run(_turn_on_light_sync, name_or_id, transition_seconds)

async def turn_off_light(name_or_id, transition_seconds: float = 0.4) -> dict:
    return await _run(_turn_off_light_sync, name_or_id, transition_seconds)

async def set_brightness(name_or_id, percent: float, transition_seconds: float = 0.4) -> dict:
    return await _run(_set_brightness_sync, name_or_id, percent, transition_seconds)

async def set_color_rgb(name_or_id, r: int, g: int, b: int, transition_seconds: float = 0.4) -> dict:
    return await _run(_set_color_rgb_sync, name_or_id, r, g, b, transition_seconds)

async def set_color_temp(name_or_id, kelvin: int, transition_seconds: float = 0.4) -> dict:
    return await _run(_set_color_temp_sync, name_or_id, kelvin, transition_seconds)

async def list_groups() -> list[dict]:
    return await _run(_list_groups_sync)

async def turn_on_group(name_or_id, brightness_pct: Optional[float] = None, transition_seconds: float = 0.4) -> dict:
    return await _run(_turn_on_group_sync, name_or_id, brightness_pct, transition_seconds)

async def turn_off_group(name_or_id, transition_seconds: float = 0.4) -> dict:
    return await _run(_turn_off_group_sync, name_or_id, transition_seconds)

async def set_group_color_temp(name_or_id, kelvin: int, transition_seconds: float = 0.4) -> dict:
    return await _run(_set_group_color_temp_sync, name_or_id, kelvin, transition_seconds)

async def set_group_color_rgb(name_or_id, r: int, g: int, b: int, transition_seconds: float = 0.4) -> dict:
    return await _run(_set_group_color_rgb_sync, name_or_id, r, g, b, transition_seconds)

async def list_scenes() -> list[dict]:
    return await _run(_list_scenes_sync)

async def activate_scene(group_name: str, scene_name: str) -> dict:
    return await _run(_activate_scene_sync, group_name, scene_name)
