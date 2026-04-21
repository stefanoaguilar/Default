"""Google Home MCP server."""

import os
from typing import Optional

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

from . import cast_client, nest_client

mcp = FastMCP(
    "Google Home",
    instructions=(
        "Control Google Home speakers, Chromecast devices, and Nest smart home devices. "
        "Speaker/Chromecast tools work on the local network without API keys. "
        "Nest tools require Google credentials configured in the .env file."
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


def main():
    mcp.run()


if __name__ == "__main__":
    main()
