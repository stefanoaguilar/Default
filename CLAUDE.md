# Claude Instructions

## Smart Home Control

Always use the available MCP tools to control smart home devices. Never suggest manual app usage or ask the user to control devices themselves when a tool exists.

### Google Home / Chromecast
Use the Google Home MCP tools for all Chromecast and Google Home speaker interactions:
- `discover_speakers` — find devices before controlling them if name is unknown
- `get_speaker_status`, `play_media_on_speaker`, `pause_speaker`, `resume_speaker`, `stop_speaker`
- `set_speaker_volume`, `mute_speaker`, `quit_speaker_app`

### Sonos
Use the Sonos MCP tools for all Sonos speaker interactions:
- `discover_sonos_speakers` — find speakers before controlling them if name is unknown
- `get_sonos_status`, `play_sonos`, `pause_sonos`, `stop_sonos`
- `next_track_sonos`, `previous_track_sonos`
- `set_sonos_volume`, `mute_sonos`, `set_sonos_bass`, `set_sonos_treble`
- `play_uri_on_sonos` for radio streams and podcast URLs
- `get_sonos_queue`, `clear_sonos_queue`, `play_sonos_from_queue`
- `join_sonos_group`, `unjoin_sonos` for multi-room audio

### Philips Hue
Use the Hue MCP tools for all light control:
- `list_hue_lights`, `list_hue_groups`, `list_hue_scenes`
- `turn_on_hue_light` / `turn_off_hue_light` (individual lights)
- `turn_on_hue_group` / `turn_off_hue_group` (rooms/zones)
- `set_hue_brightness`, `set_hue_color_rgb`, `set_hue_color_temperature`
- `activate_hue_scene` for named scenes like "Relax" or "Energize"

### Nest
Use the Nest MCP tools for thermostat and camera control:
- `list_nest_devices`, `get_nest_device`
- `set_thermostat_mode`, `set_heat_temperature`, `set_cool_temperature`
- `turn_on_fan`, `turn_off_fan`

## General Rules

- If a device name is ambiguous, run the relevant discover tool first and confirm with the user.
- Prefer group/room control over individual lights when the user refers to a room by name.
- For Sonos multi-room requests, use `join_sonos_group` to sync speakers before playing.
- Temperature values for Nest are in Fahrenheit unless the user specifies otherwise.
- Hue color temperature: 2700 K = warm white, 4000 K = neutral, 6500 K = cool daylight.
