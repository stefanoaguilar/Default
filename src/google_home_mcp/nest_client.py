"""Google Nest Smart Device Management (SDM) API client."""

import os
from typing import Any, Optional

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SDM_BASE = "https://smartdevicemanagement.googleapis.com/v1"
AUTH_BASE = "https://nestservices.google.com/partnerconnections"
SCOPES = ["https://www.googleapis.com/auth/sdm.service"]

THERMOSTAT_MODE_COMMAND = "sdm.devices.commands.ThermostatMode.SetMode"
HEAT_SETPOINT_COMMAND = "sdm.devices.commands.ThermostatTemperatureSetpoint.SetHeat"
COOL_SETPOINT_COMMAND = "sdm.devices.commands.ThermostatTemperatureSetpoint.SetCool"
RANGE_SETPOINT_COMMAND = "sdm.devices.commands.ThermostatTemperatureSetpoint.SetRange"
FAN_TIMER_COMMAND = "sdm.devices.commands.Fan.SetTimer"

TRAIT_TEMPERATURE = "sdm.devices.traits.Temperature"
TRAIT_HUMIDITY = "sdm.devices.traits.Humidity"
TRAIT_THERMOSTAT_MODE = "sdm.devices.traits.ThermostatMode"
TRAIT_THERMOSTAT_SETPOINT = "sdm.devices.traits.ThermostatTemperatureSetpoint"
TRAIT_THERMOSTAT_HVAC = "sdm.devices.traits.ThermostatHvac"
TRAIT_FAN = "sdm.devices.traits.Fan"
TRAIT_CONNECTIVITY = "sdm.devices.traits.Connectivity"
TRAIT_INFO = "sdm.devices.traits.Info"
TRAIT_CAMERA_IMAGE = "sdm.devices.traits.CameraImage"
TRAIT_CAMERA_LIVE_STREAM = "sdm.devices.traits.CameraLiveStream"
TRAIT_DOORBELL_CHIME = "sdm.devices.traits.DoorbellChime"


def _celsius_to_fahrenheit(c: float) -> float:
    return round(c * 9 / 5 + 32, 1)


def _fahrenheit_to_celsius(f: float) -> float:
    return round((f - 32) * 5 / 9, 2)


class NestClient:
    def __init__(self):
        self.project_id = os.getenv("NEST_PROJECT_ID", "")
        self.credentials = self._load_credentials()

    def _load_credentials(self) -> Optional[Credentials]:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        access_token = os.getenv("GOOGLE_ACCESS_TOKEN")
        refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

        if not (client_id and client_secret):
            return None

        creds = Credentials(
            token=access_token or None,
            refresh_token=refresh_token or None,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds

    def _check_config(self):
        if not self.project_id:
            raise RuntimeError(
                "NEST_PROJECT_ID not set. Create a project at https://console.nest.google.com/device-access"
            )
        if not self.credentials:
            raise RuntimeError(
                "Google credentials not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env"
            )

    def _headers(self) -> dict:
        if self.credentials and self.credentials.expired and self.credentials.refresh_token:
            self.credentials.refresh(Request())
        return {"Authorization": f"Bearer {self.credentials.token}"}

    def _get(self, path: str) -> Any:
        self._check_config()
        url = f"{SDM_BASE}/enterprises/{self.project_id}{path}"
        with httpx.Client() as client:
            resp = client.get(url, headers=self._headers())
            resp.raise_for_status()
            return resp.json()

    def _post(self, path: str, body: dict) -> Any:
        self._check_config()
        url = f"{SDM_BASE}/enterprises/{self.project_id}{path}"
        with httpx.Client() as client:
            resp = client.post(url, headers=self._headers(), json=body)
            resp.raise_for_status()
            return resp.json()

    def _format_device(self, device: dict) -> dict:
        traits = device.get("traits", {})
        device_id = device["name"].split("/")[-1]
        display_name = traits.get(TRAIT_INFO, {}).get("customName", device_id)
        device_type = device.get("type", "").split(".")[-1].lower()

        result: dict = {
            "id": device_id,
            "name": display_name,
            "type": device_type,
            "connectivity": traits.get(TRAIT_CONNECTIVITY, {}).get("status"),
        }

        if TRAIT_TEMPERATURE in traits:
            temp_c = traits[TRAIT_TEMPERATURE]["ambientTemperatureCelsius"]
            result["temperature_c"] = temp_c
            result["temperature_f"] = _celsius_to_fahrenheit(temp_c)

        if TRAIT_HUMIDITY in traits:
            result["humidity_percent"] = traits[TRAIT_HUMIDITY]["ambientHumidityPercent"]

        if TRAIT_THERMOSTAT_MODE in traits:
            result["thermostat_mode"] = traits[TRAIT_THERMOSTAT_MODE]["mode"]
            result["available_modes"] = traits[TRAIT_THERMOSTAT_MODE].get("availableModes", [])

        if TRAIT_THERMOSTAT_SETPOINT in traits:
            sp = traits[TRAIT_THERMOSTAT_SETPOINT]
            if "heatCelsius" in sp:
                result["heat_setpoint_c"] = sp["heatCelsius"]
                result["heat_setpoint_f"] = _celsius_to_fahrenheit(sp["heatCelsius"])
            if "coolCelsius" in sp:
                result["cool_setpoint_c"] = sp["coolCelsius"]
                result["cool_setpoint_f"] = _celsius_to_fahrenheit(sp["coolCelsius"])

        if TRAIT_THERMOSTAT_HVAC in traits:
            result["hvac_status"] = traits[TRAIT_THERMOSTAT_HVAC]["status"]

        if TRAIT_FAN in traits:
            fan = traits[TRAIT_FAN]
            result["fan_timer_active"] = fan.get("timerMode") == "ON"
            result["fan_timer_timeout"] = fan.get("timerTimeout")

        if TRAIT_CAMERA_IMAGE in traits:
            result["supports_camera_image"] = True

        if TRAIT_CAMERA_LIVE_STREAM in traits:
            result["supported_protocols"] = traits[TRAIT_CAMERA_LIVE_STREAM].get(
                "supportedProtocols", []
            )

        if TRAIT_DOORBELL_CHIME in traits:
            result["is_doorbell"] = True

        return result

    def list_devices(self) -> list[dict]:
        data = self._get("/devices")
        return [self._format_device(d) for d in data.get("devices", [])]

    def get_device(self, device_id: str) -> dict:
        data = self._get(f"/devices/{device_id}")
        return self._format_device(data)

    def list_rooms(self) -> list[dict]:
        data = self._get("/structures")
        rooms = []
        for structure in data.get("structures", []):
            struct_id = structure["name"].split("/")[-1]
            rooms_data = self._get(f"/structures/{struct_id}/rooms")
            for room in rooms_data.get("rooms", []):
                rooms.append({
                    "id": room["name"].split("/")[-1],
                    "structure_id": struct_id,
                    "name": room.get("traits", {})
                    .get("sdm.structures.traits.RoomInfo", {})
                    .get("customName", "Unknown"),
                })
        return rooms

    def set_thermostat_mode(self, device_id: str, mode: str) -> dict:
        valid = ["HEAT", "COOL", "HEATCOOL", "OFF"]
        if mode.upper() not in valid:
            raise ValueError(f"Mode must be one of {valid}")
        result = self._post(
            f"/devices/{device_id}:executeCommand",
            {"command": THERMOSTAT_MODE_COMMAND, "params": {"mode": mode.upper()}},
        )
        return {"device_id": device_id, "mode": mode.upper(), "result": result}

    def set_heat_temperature(self, device_id: str, temperature_f: float) -> dict:
        temp_c = _fahrenheit_to_celsius(temperature_f)
        result = self._post(
            f"/devices/{device_id}:executeCommand",
            {"command": HEAT_SETPOINT_COMMAND, "params": {"heatCelsius": temp_c}},
        )
        return {"device_id": device_id, "heat_setpoint_f": temperature_f, "heat_setpoint_c": temp_c}

    def set_cool_temperature(self, device_id: str, temperature_f: float) -> dict:
        temp_c = _fahrenheit_to_celsius(temperature_f)
        result = self._post(
            f"/devices/{device_id}:executeCommand",
            {"command": COOL_SETPOINT_COMMAND, "params": {"coolCelsius": temp_c}},
        )
        return {"device_id": device_id, "cool_setpoint_f": temperature_f, "cool_setpoint_c": temp_c}

    def set_temperature_range(
        self, device_id: str, heat_f: float, cool_f: float
    ) -> dict:
        if heat_f >= cool_f:
            raise ValueError("Heat setpoint must be less than cool setpoint")
        heat_c = _fahrenheit_to_celsius(heat_f)
        cool_c = _fahrenheit_to_celsius(cool_f)
        result = self._post(
            f"/devices/{device_id}:executeCommand",
            {
                "command": RANGE_SETPOINT_COMMAND,
                "params": {"heatCelsius": heat_c, "coolCelsius": cool_c},
            },
        )
        return {
            "device_id": device_id,
            "heat_setpoint_f": heat_f,
            "cool_setpoint_f": cool_f,
        }

    def set_fan_timer(self, device_id: str, duration_seconds: int) -> dict:
        if duration_seconds <= 0:
            raise ValueError("Duration must be positive")
        result = self._post(
            f"/devices/{device_id}:executeCommand",
            {
                "command": FAN_TIMER_COMMAND,
                "params": {"timerMode": "ON", "duration": f"{duration_seconds}s"},
            },
        )
        return {"device_id": device_id, "fan_timer_seconds": duration_seconds}

    def turn_off_fan(self, device_id: str) -> dict:
        result = self._post(
            f"/devices/{device_id}:executeCommand",
            {"command": FAN_TIMER_COMMAND, "params": {"timerMode": "OFF"}},
        )
        return {"device_id": device_id, "fan_timer_active": False}

    def generate_camera_stream(self, device_id: str, protocol: str = "WEB_RTC") -> dict:
        result = self._post(
            f"/devices/{device_id}:executeCommand",
            {
                "command": "sdm.devices.commands.CameraLiveStream.GenerateWebRtcStream",
                "params": {"offerSdp": ""},
            },
        )
        return {"device_id": device_id, "stream": result}


def run_auth_flow() -> dict:
    """Run the OAuth2 flow to get credentials. Prints tokens to stdout."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    project_id = os.getenv("NEST_PROJECT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")

    if not (client_id and client_secret and project_id):
        raise RuntimeError("GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and NEST_PROJECT_ID must be set")

    auth_url = (
        f"{AUTH_BASE}/{project_id}/auth"
        f"?redirect_uri={redirect_uri}"
        f"&access_type=offline"
        f"&prompt=consent"
        f"&client_id={client_id}"
        f"&response_type=code"
        f"&scope=https://www.googleapis.com/auth/sdm.service"
    )

    return {
        "message": "Visit this URL to authorize the application",
        "auth_url": auth_url,
        "instructions": [
            "1. Visit the auth_url above",
            "2. Sign in and grant permissions",
            "3. Copy the authorization code",
            "4. Use the exchange_auth_code tool with the code to get tokens",
        ],
    }


def exchange_auth_code(code: str) -> dict:
    """Exchange authorization code for access and refresh tokens."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")

    with httpx.Client() as client:
        resp = client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        resp.raise_for_status()
        tokens = resp.json()

    return {
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "instructions": "Add these tokens to your .env file as GOOGLE_ACCESS_TOKEN and GOOGLE_REFRESH_TOKEN",
    }
