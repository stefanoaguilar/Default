"""Google Home MCP server."""

import os
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

from . import cast_client, hue_client, nest_client, sonos_client

mcp = FastMCP(
    "Google Home",
    instructions=(
        "Control Google Home/Chromecast speakers, Sonos speakers, Philips Hue lights, "
        "and Nest smart home devices. Chromecast and Sonos work on the local network "
        "without API keys. Hue requires HUE_BRIDGE_IP in .env. "
        "Nest requires Google credentials in .env."
    ),
)

_nest = nest_client.NestClient()


# ── Speaker / Chromecast tools ────────────────────────────────────────────────

@mcp.tool()
async def discover_speakers(timeout: int = 5) -> dict:
    """
    Discover Google Home speakers and Chromecast devices on the local network.

    Args:
        timeout: Seconds to wait for discovery (default 5)
    """
    try:
        devices = await cast_client.discover_devices(timeout=timeout)
        return {"devices": devices, "count": len(devices)}
    except Exception as e:
        return {"error": str(e), "devices": []}


@mcp.tool()
async def get_speaker_status(name: str) -> dict:
    """
    Get the current playback status and volume of a Google Home speaker or Chromecast.

    Args:
        name: Exact name of the speaker (e.g. "Living Room", "Kitchen Display")
    """
    try:
        return await cast_client.get_status(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get status: {e}"}


@mcp.tool()
async def play_media_on_speaker(
    name: str,
    url: str,
    content_type: str,
    title: Optional[str] = None,
) -> dict:
    """
    Play media on a Google Home speaker or Chromecast.

    Args:
        name: Exact name of the speaker or Chromecast device
        url: Direct URL to the media file (MP3, MP4, HLS, etc.)
        content_type: MIME type such as "audio/mp3", "video/mp4", "application/x-mpegURL"
        title: Optional title to display while playing
    """
    try:
        return await cast_client.play_media(name, url, content_type, title)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to play media: {e}"}


@mcp.tool()
async def pause_speaker(name: str) -> dict:
    """
    Pause playback on a Google Home speaker or Chromecast.

    Args:
        name: Exact name of the speaker
    """
    try:
        return await cast_client.pause(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to pause: {e}"}


@mcp.tool()
async def resume_speaker(name: str) -> dict:
    """
    Resume paused playback on a Google Home speaker or Chromecast.

    Args:
        name: Exact name of the speaker
    """
    try:
        return await cast_client.play(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to resume: {e}"}


@mcp.tool()
async def stop_speaker(name: str) -> dict:
    """
    Stop playback on a Google Home speaker or Chromecast.

    Args:
        name: Exact name of the speaker
    """
    try:
        return await cast_client.stop(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to stop: {e}"}


@mcp.tool()
async def set_speaker_volume(name: str, level: float) -> dict:
    """
    Set the volume level of a Google Home speaker or Chromecast.

    Args:
        name: Exact name of the speaker
        level: Volume level between 0.0 (silent) and 1.0 (max)
    """
    try:
        return await cast_client.set_volume(name, level)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set volume: {e}"}


@mcp.tool()
async def mute_speaker(name: str, muted: bool = True) -> dict:
    """
    Mute or unmute a Google Home speaker or Chromecast.

    Args:
        name: Exact name of the speaker
        muted: True to mute, False to unmute
    """
    try:
        return await cast_client.set_mute(name, muted)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set mute: {e}"}


@mcp.tool()
async def quit_speaker_app(name: str) -> dict:
    """
    Quit the currently running app on a Google Home speaker or Chromecast.

    Args:
        name: Exact name of the speaker
    """
    try:
        return await cast_client.quit_app(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to quit app: {e}"}


# ── Nest auth tools ───────────────────────────────────────────────────────────

@mcp.tool()
async def get_nest_auth_url() -> dict:
    """
    Generate the Google OAuth2 authorization URL for Nest device access.
    Use this to start the authentication flow when GOOGLE_ACCESS_TOKEN is not set.
    """
    try:
        return nest_client.run_auth_flow()
    except RuntimeError as e:
        return {"error": str(e)}


@mcp.tool()
async def exchange_nest_auth_code(code: str) -> dict:
    """
    Exchange a Google OAuth2 authorization code for access and refresh tokens.

    Args:
        code: The authorization code received after visiting the auth URL
    """
    try:
        return nest_client.exchange_auth_code(code)
    except Exception as e:
        return {"error": f"Failed to exchange code: {e}"}


# ── Nest device tools ─────────────────────────────────────────────────────────

@mcp.tool()
async def list_nest_devices() -> dict:
    """
    List all Nest devices (thermostats, cameras, doorbells) in the account.
    Requires Google credentials configured in .env.
    """
    try:
        devices = _nest.list_devices()
        return {"devices": devices, "count": len(devices)}
    except RuntimeError as e:
        return {"error": str(e), "hint": "Run get_nest_auth_url to start authentication"}
    except Exception as e:
        return {"error": f"Failed to list devices: {e}"}


@mcp.tool()
async def get_nest_device(device_id: str) -> dict:
    """
    Get the current state of a specific Nest device.

    Args:
        device_id: Device ID from list_nest_devices
    """
    try:
        return _nest.get_device(device_id)
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get device: {e}"}


@mcp.tool()
async def list_nest_rooms() -> dict:
    """
    List all rooms/structures in the Google Nest account.
    """
    try:
        rooms = _nest.list_rooms()
        return {"rooms": rooms, "count": len(rooms)}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to list rooms: {e}"}


@mcp.tool()
async def set_thermostat_mode(device_id: str, mode: str) -> dict:
    """
    Set the operating mode of a Nest thermostat.

    Args:
        device_id: Device ID from list_nest_devices
        mode: One of HEAT, COOL, HEATCOOL, or OFF
    """
    try:
        return _nest.set_thermostat_mode(device_id, mode)
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set mode: {e}"}


@mcp.tool()
async def set_heat_temperature(device_id: str, temperature_f: float) -> dict:
    """
    Set the heat setpoint temperature on a Nest thermostat (in Fahrenheit).

    Args:
        device_id: Device ID from list_nest_devices
        temperature_f: Target heat temperature in Fahrenheit
    """
    try:
        return _nest.set_heat_temperature(device_id, temperature_f)
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set heat temperature: {e}"}


@mcp.tool()
async def set_cool_temperature(device_id: str, temperature_f: float) -> dict:
    """
    Set the cool setpoint temperature on a Nest thermostat (in Fahrenheit).

    Args:
        device_id: Device ID from list_nest_devices
        temperature_f: Target cool temperature in Fahrenheit
    """
    try:
        return _nest.set_cool_temperature(device_id, temperature_f)
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set cool temperature: {e}"}


@mcp.tool()
async def set_temperature_range(
    device_id: str, heat_f: float, cool_f: float
) -> dict:
    """
    Set both heat and cool setpoints on a Nest thermostat in HEATCOOL mode.

    Args:
        device_id: Device ID from list_nest_devices
        heat_f: Heat setpoint in Fahrenheit (must be lower than cool_f)
        cool_f: Cool setpoint in Fahrenheit (must be higher than heat_f)
    """
    try:
        return _nest.set_temperature_range(device_id, heat_f, cool_f)
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set temperature range: {e}"}


@mcp.tool()
async def turn_on_fan(device_id: str, duration_minutes: int = 15) -> dict:
    """
    Turn on the fan on a Nest thermostat for a set duration.

    Args:
        device_id: Device ID from list_nest_devices
        duration_minutes: How long to run the fan (default 15 minutes)
    """
    try:
        return _nest.set_fan_timer(device_id, duration_minutes * 60)
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to turn on fan: {e}"}


@mcp.tool()
async def turn_off_fan(device_id: str) -> dict:
    """
    Turn off the fan on a Nest thermostat.

    Args:
        device_id: Device ID from list_nest_devices
    """
    try:
        return _nest.turn_off_fan(device_id)
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to turn off fan: {e}"}


# ── Sonos tools ───────────────────────────────────────────────────────────────

@mcp.tool()
async def discover_sonos_speakers(timeout: int = 5) -> dict:
    """
    Discover all Sonos speakers on the local network.

    Args:
        timeout: Seconds to wait for discovery (default 5)
    """
    try:
        devices = await sonos_client.discover(timeout=timeout)
        return {"speakers": devices, "count": len(devices)}
    except Exception as e:
        return {"error": str(e), "speakers": []}


@mcp.tool()
async def get_sonos_status(name: str) -> dict:
    """
    Get the current playback state, volume, and track info for a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker (e.g. "Living Room")
    """
    try:
        return await sonos_client.get_status(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get status: {e}"}


@mcp.tool()
async def play_sonos(name: str) -> dict:
    """
    Resume or start playback on a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
    """
    try:
        return await sonos_client.play(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to play: {e}"}


@mcp.tool()
async def pause_sonos(name: str) -> dict:
    """
    Pause playback on a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
    """
    try:
        return await sonos_client.pause(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to pause: {e}"}


@mcp.tool()
async def stop_sonos(name: str) -> dict:
    """
    Stop playback on a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
    """
    try:
        return await sonos_client.stop(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to stop: {e}"}


@mcp.tool()
async def next_track_sonos(name: str) -> dict:
    """
    Skip to the next track on a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
    """
    try:
        return await sonos_client.next_track(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to skip track: {e}"}


@mcp.tool()
async def previous_track_sonos(name: str) -> dict:
    """
    Go back to the previous track on a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
    """
    try:
        return await sonos_client.previous_track(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to go to previous track: {e}"}


@mcp.tool()
async def set_sonos_volume(name: str, volume: int) -> dict:
    """
    Set the volume of a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
        volume: Volume level 0–100
    """
    try:
        return await sonos_client.set_volume(name, volume)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set volume: {e}"}


@mcp.tool()
async def mute_sonos(name: str, muted: bool = True) -> dict:
    """
    Mute or unmute a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
        muted: True to mute, False to unmute
    """
    try:
        return await sonos_client.set_mute(name, muted)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set mute: {e}"}


@mcp.tool()
async def play_uri_on_sonos(name: str, uri: str, title: str = "") -> dict:
    """
    Play an audio stream URI on a Sonos speaker (radio, podcast, file URL, etc.).

    Args:
        name: Exact name of the Sonos speaker
        uri: Audio stream URI (http/https URL or Sonos URI)
        title: Optional display title
    """
    try:
        return await sonos_client.play_uri(name, uri, title)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to play URI: {e}"}


@mcp.tool()
async def get_sonos_queue(name: str, max_items: int = 50) -> dict:
    """
    Get the current play queue of a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
        max_items: Maximum number of queue items to return (default 50)
    """
    try:
        return await sonos_client.get_queue(name, max_items)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get queue: {e}"}


@mcp.tool()
async def clear_sonos_queue(name: str) -> dict:
    """
    Clear the play queue on a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
    """
    try:
        return await sonos_client.clear_queue(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to clear queue: {e}"}


@mcp.tool()
async def play_sonos_from_queue(name: str, index: int) -> dict:
    """
    Play a specific track from the queue on a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
        index: Zero-based index of the track in the queue
    """
    try:
        return await sonos_client.play_from_queue(name, index)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to play from queue: {e}"}


@mcp.tool()
async def join_sonos_group(name: str, coordinator_name: str) -> dict:
    """
    Add a Sonos speaker to another speaker's group for synchronized playback.

    Args:
        name: Name of the speaker to add to the group
        coordinator_name: Name of the group coordinator (the speaker already playing)
    """
    try:
        return await sonos_client.join_group(name, coordinator_name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to join group: {e}"}


@mcp.tool()
async def unjoin_sonos(name: str) -> dict:
    """
    Remove a Sonos speaker from its current group so it plays independently.

    Args:
        name: Exact name of the Sonos speaker
    """
    try:
        return await sonos_client.unjoin(name)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to unjoin: {e}"}


@mcp.tool()
async def set_sonos_bass(name: str, bass: int) -> dict:
    """
    Set the bass level of a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
        bass: Bass level from -10 to +10 (0 is neutral)
    """
    try:
        return await sonos_client.set_bass(name, bass)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set bass: {e}"}


@mcp.tool()
async def set_sonos_treble(name: str, treble: int) -> dict:
    """
    Set the treble level of a Sonos speaker.

    Args:
        name: Exact name of the Sonos speaker
        treble: Treble level from -10 to +10 (0 is neutral)
    """
    try:
        return await sonos_client.set_treble(name, treble)
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set treble: {e}"}


# ── Philips Hue tools ─────────────────────────────────────────────────────────

@mcp.tool()
async def discover_hue_bridge() -> dict:
    """
    Discover Philips Hue bridges on the local network.
    Returns the IP address(es) to use for HUE_BRIDGE_IP in .env.
    """
    try:
        bridges = await hue_client.discover_bridges()
        return {"bridges": bridges, "count": len(bridges)}
    except Exception as e:
        return {"error": f"Discovery failed: {e}"}


@mcp.tool()
async def connect_hue_bridge(ip: str) -> dict:
    """
    Connect to a Philips Hue bridge for the first time.
    Press the button on the bridge before calling this tool.

    Args:
        ip: IP address of the Hue bridge (from discover_hue_bridge)
    """
    try:
        return await hue_client.connect_bridge(ip)
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
async def list_hue_lights() -> dict:
    """
    List all Philips Hue lights with their current state.
    Requires HUE_BRIDGE_IP set in .env.
    """
    try:
        lights = await hue_client.list_lights()
        return {"lights": lights, "count": len(lights)}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to list lights: {e}"}


@mcp.tool()
async def get_hue_light(name_or_id: str) -> dict:
    """
    Get the current state of a specific Philips Hue light.

    Args:
        name_or_id: Light name (e.g. "Bedroom 1") or numeric ID
    """
    try:
        return await hue_client.get_light(name_or_id)
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to get light: {e}"}


@mcp.tool()
async def turn_on_hue_light(name_or_id: str, transition_seconds: float = 0.4) -> dict:
    """
    Turn on a Philips Hue light.

    Args:
        name_or_id: Light name or numeric ID
        transition_seconds: Fade-in duration in seconds (default 0.4)
    """
    try:
        return await hue_client.turn_on_light(name_or_id, transition_seconds)
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to turn on light: {e}"}


@mcp.tool()
async def turn_off_hue_light(name_or_id: str, transition_seconds: float = 0.4) -> dict:
    """
    Turn off a Philips Hue light.

    Args:
        name_or_id: Light name or numeric ID
        transition_seconds: Fade-out duration in seconds (default 0.4)
    """
    try:
        return await hue_client.turn_off_light(name_or_id, transition_seconds)
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to turn off light: {e}"}


@mcp.tool()
async def set_hue_brightness(
    name_or_id: str, brightness_pct: float, transition_seconds: float = 0.4
) -> dict:
    """
    Set the brightness of a Philips Hue light.

    Args:
        name_or_id: Light name or numeric ID
        brightness_pct: Brightness percentage 0–100
        transition_seconds: Transition duration in seconds (default 0.4)
    """
    try:
        return await hue_client.set_brightness(name_or_id, brightness_pct, transition_seconds)
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set brightness: {e}"}


@mcp.tool()
async def set_hue_color_rgb(
    name_or_id: str,
    red: int,
    green: int,
    blue: int,
    transition_seconds: float = 0.4,
) -> dict:
    """
    Set the color of a Philips Hue light using RGB values.

    Args:
        name_or_id: Light name or numeric ID
        red: Red channel 0–255
        green: Green channel 0–255
        blue: Blue channel 0–255
        transition_seconds: Transition duration in seconds (default 0.4)
    """
    try:
        return await hue_client.set_color_rgb(name_or_id, red, green, blue, transition_seconds)
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set color: {e}"}


@mcp.tool()
async def set_hue_color_temperature(
    name_or_id: str, kelvin: int, transition_seconds: float = 0.4
) -> dict:
    """
    Set the color temperature of a Philips Hue light.

    Args:
        name_or_id: Light name or numeric ID
        kelvin: Color temperature in Kelvin. 2700 = warm white, 4000 = neutral, 6500 = cool daylight
        transition_seconds: Transition duration in seconds (default 0.4)
    """
    try:
        return await hue_client.set_color_temp(name_or_id, kelvin, transition_seconds)
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set color temperature: {e}"}


@mcp.tool()
async def list_hue_groups() -> dict:
    """
    List all Philips Hue light groups (rooms and zones).
    """
    try:
        groups = await hue_client.list_groups()
        return {"groups": groups, "count": len(groups)}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to list groups: {e}"}


@mcp.tool()
async def turn_on_hue_group(
    name_or_id: str,
    brightness_pct: Optional[float] = None,
    transition_seconds: float = 0.4,
) -> dict:
    """
    Turn on all lights in a Philips Hue group (room or zone).

    Args:
        name_or_id: Group name (e.g. "Living Room") or numeric ID
        brightness_pct: Optional brightness 0–100 to set when turning on
        transition_seconds: Transition duration in seconds (default 0.4)
    """
    try:
        return await hue_client.turn_on_group(name_or_id, brightness_pct, transition_seconds)
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to turn on group: {e}"}


@mcp.tool()
async def turn_off_hue_group(name_or_id: str, transition_seconds: float = 0.4) -> dict:
    """
    Turn off all lights in a Philips Hue group (room or zone).

    Args:
        name_or_id: Group name (e.g. "Living Room") or numeric ID
        transition_seconds: Transition duration in seconds (default 0.4)
    """
    try:
        return await hue_client.turn_off_group(name_or_id, transition_seconds)
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to turn off group: {e}"}


@mcp.tool()
async def set_hue_group_color_temperature(
    name_or_id: str, kelvin: int, transition_seconds: float = 0.4
) -> dict:
    """
    Set the color temperature for all lights in a Philips Hue group.

    Args:
        name_or_id: Group name or numeric ID
        kelvin: Color temperature in Kelvin (2700–6500)
        transition_seconds: Transition duration in seconds (default 0.4)
    """
    try:
        return await hue_client.set_group_color_temp(name_or_id, kelvin, transition_seconds)
    except (RuntimeError, ValueError) as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set group color temperature: {e}"}


@mcp.tool()
async def set_hue_group_color_rgb(
    name_or_id: str,
    red: int,
    green: int,
    blue: int,
    transition_seconds: float = 0.4,
) -> dict:
    """
    Set the color for all lights in a Philips Hue group using RGB values.

    Args:
        name_or_id: Group name or numeric ID
        red: Red channel 0–255
        green: Green channel 0–255
        blue: Blue channel 0–255
        transition_seconds: Transition duration in seconds (default 0.4)
    """
    try:
        return await hue_client.set_group_color_rgb(name_or_id, red, green, blue, transition_seconds)
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to set group color: {e}"}


@mcp.tool()
async def list_hue_scenes() -> dict:
    """
    List all saved Philips Hue scenes.
    """
    try:
        scenes = await hue_client.list_scenes()
        return {"scenes": scenes, "count": len(scenes)}
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to list scenes: {e}"}


@mcp.tool()
async def activate_hue_scene(group_name: str, scene_name: str) -> dict:
    """
    Activate a saved Philips Hue scene in a room or zone.

    Args:
        group_name: Name of the room/group (e.g. "Living Room")
        scene_name: Name of the scene (e.g. "Relax", "Energize", "Reading")
    """
    try:
        return await hue_client.activate_scene(group_name, scene_name)
    except RuntimeError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to activate scene: {e}"}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
