"""
OpenWeatherMap weather data provider for Pulse.
Requires a free API key from https://openweathermap.org/api
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

WEATHER_BASE = "https://api.openweathermap.org/data/2.5"

WEATHER_ICONS: Dict[str, str] = {
    "01d": "☀️",  "01n": "🌙",
    "02d": "⛅",  "02n": "☁️",
    "03d": "☁️",  "03n": "☁️",
    "04d": "☁️",  "04n": "☁️",
    "09d": "🌧️", "09n": "🌧️",
    "10d": "🌦️", "10n": "🌧️",
    "11d": "⛈️", "11n": "⛈️",
    "13d": "❄️",  "13n": "❄️",
    "50d": "🌫️", "50n": "🌫️",
}

WIND_DIRECTIONS = [
    "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
    "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
]


def _wind_dir(degrees: float) -> str:
    idx = round(degrees / 22.5) % 16
    return WIND_DIRECTIONS[idx]


async def fetch_weather(
    api_key: str,
    location: str,
    units: str = "imperial",
) -> Optional[Dict[str, Any]]:
    """Fetch current weather conditions."""
    if not api_key or not location:
        return {"error": "no_key"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{WEATHER_BASE}/weather",
                params={"q": location, "appid": api_key, "units": units},
            )
            resp.raise_for_status()
            d = resp.json()

        icon_code = d["weather"][0]["icon"]
        unit_sym = "°F" if units == "imperial" else "°C"
        wind_unit = "mph" if units == "imperial" else "m/s"

        return {
            "temp": round(d["main"]["temp"]),
            "feels_like": round(d["main"]["feels_like"]),
            "temp_min": round(d["main"]["temp_min"]),
            "temp_max": round(d["main"]["temp_max"]),
            "humidity": d["main"]["humidity"],
            "description": d["weather"][0]["description"].title(),
            "icon": WEATHER_ICONS.get(icon_code, "🌡️"),
            "icon_code": icon_code,
            "wind_speed": round(d["wind"].get("speed", 0)),
            "wind_deg": d["wind"].get("deg", 0),
            "wind_dir": _wind_dir(d["wind"].get("deg", 0)),
            "wind_unit": wind_unit,
            "location": f"{d['name']}, {d['sys']['country']}",
            "unit_sym": unit_sym,
            "visibility_km": d.get("visibility", 0) // 1000,
            "pressure": d["main"]["pressure"],
            "cloudiness": d["clouds"]["all"],
            "sunrise": datetime.fromtimestamp(d["sys"]["sunrise"]).strftime("%H:%M"),
            "sunset": datetime.fromtimestamp(d["sys"]["sunset"]).strftime("%H:%M"),
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            return {"error": "invalid_key"}
        if e.response.status_code == 404:
            return {"error": "location_not_found"}
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


async def fetch_forecast(
    api_key: str,
    location: str,
    units: str = "imperial",
) -> Optional[List[Dict[str, Any]]]:
    """Fetch 5-day weather forecast (one entry per day)."""
    if not api_key or not location:
        return None

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{WEATHER_BASE}/forecast",
                params={"q": location, "appid": api_key, "units": units, "cnt": 40},
            )
            resp.raise_for_status()
            data = resp.json()

        unit_sym = "°F" if units == "imperial" else "°C"
        days: Dict[str, Dict] = {}

        for item in data["list"]:
            dt = datetime.fromtimestamp(item["dt"])
            day_key = dt.strftime("%Y-%m-%d")
            day_label = dt.strftime("%a")

            if day_key not in days:
                icon_code = item["weather"][0]["icon"].replace("n", "d")  # prefer day icon
                days[day_key] = {
                    "day": day_label,
                    "icon": WEATHER_ICONS.get(icon_code, "🌡️"),
                    "description": item["weather"][0]["description"].title(),
                    "high": round(item["main"]["temp_max"]),
                    "low": round(item["main"]["temp_min"]),
                    "unit_sym": unit_sym,
                    "humidity": item["main"]["humidity"],
                }
            else:
                days[day_key]["high"] = max(days[day_key]["high"], round(item["main"]["temp_max"]))
                days[day_key]["low"] = min(days[day_key]["low"], round(item["main"]["temp_min"]))

        return list(days.values())[:5]
    except Exception:
        return None
