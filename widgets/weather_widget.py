"""
Weather widget for Pulse — displays current conditions and 5-day forecast.
"""

from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.widgets import Static
from textual import work

from config import load_config
from providers.weather import fetch_forecast, fetch_weather


class WeatherWidget(Static):
    """Full weather panel with current conditions and forecast."""

    DEFAULT_CSS = """
    WeatherWidget {
        height: 1fr;
        width: 1fr;
    }
    """

    def on_mount(self) -> None:
        self.update(self._loading_panel())
        self.load_data()

    @work(exclusive=True, thread=False)
    async def load_data(self) -> None:
        """Fetch weather data and update the display."""
        config = load_config()
        wc = config["weather"]

        current, forecast = None, None
        if wc.get("api_key"):
            current = await fetch_weather(wc["api_key"], wc["location"], wc["units"])
            forecast = await fetch_forecast(wc["api_key"], wc["location"], wc["units"])

        self.update(self._build_content(current, forecast, wc))

    def _loading_panel(self) -> Panel:
        return Panel(
            Align.center(Text("⟳ Loading weather data…", style="dim")),
            title="[bold #06b6d4]🌤  Weather[/]",
            border_style="#2d3057",
            padding=(2, 4),
        )

    def _build_content(
        self,
        current: Optional[Dict[str, Any]],
        forecast: Optional[List[Dict[str, Any]]],
        cfg: Dict,
    ):
        if not cfg.get("api_key"):
            return self._no_key_panel()
        if current is None or "error" in current:
            err = (current or {}).get("error", "unknown")
            return self._error_panel(err)

        body = Group(
            self._render_current(current),
            Text(""),
            self._render_forecast(forecast or []),
        )
        return Panel(
            body,
            title=f"[bold #06b6d4]🌤  Weather — {current['location']}[/]",
            border_style="#7c3aed",
            padding=(1, 2),
        )

    def _render_current(self, d: Dict[str, Any]) -> Group:
        # Big temperature display
        temp_text = Text()
        temp_text.append(f"  {d['icon']}  ", style="bold")
        temp_text.append(f"{d['temp']}{d['unit_sym']}", style="bold #e2e8f0 on default")
        temp_text.append(f"  {d['description']}", style="#94a3b8")

        feels = Text(f"  Feels like {d['feels_like']}{d['unit_sym']}  ·  "
                     f"H: {d['temp_max']}{d['unit_sym']}  L: {d['temp_min']}{d['unit_sym']}",
                     style="#64748b")

        details = Text()
        details.append(f"  💧 {d['humidity']}%  ", style="#60a5fa")
        details.append(f"💨 {d['wind_speed']} {d['wind_unit']} {d['wind_dir']}  ", style="#a78bfa")
        details.append(f"👁  {d['visibility_km']} km  ", style="#34d399")
        details.append(f"🌡  {d['pressure']} hPa  ", style="#fb923c")
        details.append(f"☁  {d['cloudiness']}%  ", style="#94a3b8")

        sun = Text(f"  🌅 Sunrise {d['sunrise']}  ·  🌇 Sunset {d['sunset']}", style="#fbbf24")

        return Group(temp_text, feels, Text(""), details, sun)

    def _render_forecast(self, forecast: List[Dict[str, Any]]) -> Group:
        if not forecast:
            return Group(Text(""))

        header = Text("  ── 5-Day Forecast ─────────────────────", style="dim #2d3057")

        day_cols = []
        for day in forecast:
            col = Text(justify="center")
            col.append(f"{day['day']}\n", style="bold #94a3b8")
            col.append(f"{day['icon']}\n", style="")
            col.append(f"{day['high']}{day['unit_sym']}\n", style="bold #f87171")
            col.append(f"{day['low']}{day['unit_sym']}", style="#60a5fa")
            day_cols.append(col)

        return Group(header, Text(""), Columns(day_cols, equal=True, expand=True))

    def _no_key_panel(self) -> Panel:
        msg = Text(justify="center")
        msg.append("🔑  No Weather API Key\n\n", style="bold #f59e0b")
        msg.append("Press ", style="#94a3b8")
        msg.append("S", style="bold #7c3aed")
        msg.append(" to open Settings and add your free key from\n", style="#94a3b8")
        msg.append("https://openweathermap.org/api", style="underline #06b6d4")
        return Panel(
            Align.center(msg, vertical="middle"),
            title="[bold #06b6d4]🌤  Weather[/]",
            border_style="#2d3057",
            padding=(3, 4),
        )

    def _error_panel(self, error: str) -> Panel:
        msgs = {
            "no_key": "No API key configured. Press S to open Settings.",
            "invalid_key": (
                "API key not recognized yet.\n\n"
                "  • OpenWeatherMap keys take up to 10 minutes to activate after creation.\n"
                "  • Double-check the key is copied correctly in Settings (press S)."
            ),
            "location_not_found": "Location not found. Check the city name in Settings (press S).",
        }
        msg = Text(justify="center")
        msg.append("⚠  ", style="bold #ef4444")
        msg.append(msgs.get(error, f"Error: {error}"), style="#94a3b8")
        return Panel(
            Align.center(msg, vertical="middle"),
            title="[bold #06b6d4]🌤  Weather[/]",
            border_style="#ef4444",
            padding=(3, 4),
        )

    def action_refresh(self) -> None:
        self.load_data()
