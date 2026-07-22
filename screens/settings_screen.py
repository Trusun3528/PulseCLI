"""
Settings screen for Pulse — full-screen in-app configuration UI.
"""

from typing import Any, Dict, List

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Select, Static, Switch


class SettingsScreen(Screen):
    """Full-screen settings panel."""

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("ctrl+s", "save", "Save"),
    ]

    CSS = """
    SettingsScreen {
        background: #0d0f14;
        align: center middle;
    }
    #settings-container {
        width: 80;
        height: 90%;
        background: #1a1d2e;
        border: solid #7c3aed;
        padding: 0;
    }
    #settings-title {
        height: 3;
        background: #7c3aed;
        color: #ffffff;
        content-align: center middle;
        text-style: bold;
    }
    #settings-scroll {
        height: 1fr;
        padding: 1 2;
    }
    .section-title {
        color: #06b6d4;
        text-style: bold;
        margin: 1 0 0 0;
        padding: 0 0 0 0;
    }
    .section-divider {
        color: #2d3057;
        margin: 0 0 1 0;
    }
    .field-label {
        color: #94a3b8;
        margin: 1 0 0 0;
        height: 1;
    }
    .field-hint {
        color: #475569;
        height: 1;
        margin: 0;
    }
    Input {
        border: tall #2d3057;
        background: #0d0f14;
        color: #e2e8f0;
        margin: 0 0 0 0;
    }
    Input:focus {
        border: tall #7c3aed;
    }
    Select {
        border: tall #2d3057;
        background: #0d0f14;
        color: #e2e8f0;
        margin: 0 0 0 0;
    }
    #settings-footer {
        height: 4;
        background: #0d0f14;
        layout: horizontal;
        align: right middle;
        padding: 0 2;
    }
    #settings-footer Button {
        margin: 0 0 0 1;
        min-width: 14;
    }
    #btn-save {
        background: #7c3aed;
        color: #ffffff;
        border: tall #7c3aed;
    }
    #btn-save:hover {
        background: #6d28d9;
    }
    #btn-cancel {
        background: #1a1d2e;
        color: #94a3b8;
        border: tall #2d3057;
    }
    """

    def __init__(self, config: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self._config = config

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-container"):
            yield Static("⚙  Pulse Settings", id="settings-title")
            with ScrollableContainer(id="settings-scroll"):
                yield from self._weather_section()
                yield from self._news_section()
                yield from self._youtube_section()
                yield from self._stocks_section()
                yield from self._crypto_section()
                yield from self._calendar_section()
                yield from self._github_prs_section()
                yield from self._general_section()
            with Horizontal(id="settings-footer"):
                yield Static("Press Ctrl+S to save  ·  Esc to cancel", classes="field-hint")
                yield Button("✕  Cancel", id="btn-cancel")
                yield Button("✓  Save", id="btn-save", variant="primary")

    def _weather_section(self):
        wc = self._config.get("weather", {})
        yield Static("🌤  Weather", classes="section-title")
        yield Static("──────────────────────────────────────────", classes="section-divider")
        yield Label("OpenWeatherMap API Key", classes="field-label")
        yield Label("Free key from openweathermap.org/api", classes="field-hint")
        yield Input(value=wc.get("api_key", ""), placeholder="e.g. a1b2c3d4e5f6...", password=True, id="weather-api-key")
        yield Label("Location", classes="field-label")
        yield Label("City name or 'City, Country Code'", classes="field-hint")
        yield Input(value=wc.get("location", ""), placeholder="e.g. New York or London,UK", id="weather-location")
        yield Label("Units", classes="field-label")
        units_opts = [("°F  Imperial (Fahrenheit)", "imperial"), ("°C  Metric (Celsius)", "metric")]
        yield Select(units_opts, value=wc.get("units", "imperial"), id="weather-units")

    def _news_section(self):
        nc = self._config.get("news", {})
        yield Static("📰  News", classes="section-title")
        yield Static("──────────────────────────────────────────", classes="section-divider")
        yield Label("NewsAPI Key", classes="field-label")
        yield Label("Free key (100 req/day) from newsapi.org", classes="field-hint")
        yield Input(value=nc.get("api_key", ""), placeholder="e.g. abc123...", password=True, id="news-api-key")
        yield Label("Country Code", classes="field-label")
        yield Label("2-letter country code for headlines", classes="field-hint")
        yield Input(value=nc.get("country", "us"), placeholder="e.g. us, gb, ca", id="news-country")

    def _youtube_section(self):
        yc = self._config.get("youtube", {})
        yield Static("▶️  YouTube Trending", classes="section-title")
        
        yield Label("ℹ  YouTube Data API v3 requires a free API key", classes="field-hint")
        yield Label("  1. Go to console.cloud.google.com", classes="field-hint")
        yield Label("  2. Create a project and enable YouTube Data API v3", classes="field-hint")
        yield Label("  3. Create an API key under Credentials", classes="field-hint")
        
        yield Label("API Key", classes="field-label")
        yield Input(value=yc.get("api_key", ""), placeholder="AIzaSy...", password=True, id="youtube-api-key")
        
        yield Label("Region Code", classes="field-label")
        yield Input(value=yc.get("region_code", "US"), placeholder="e.g. US, GB, JP", id="youtube-region-code")

    def _stocks_section(self):
        sc = self._config.get("stocks", {})
        yield Static("📈  Stocks", classes="section-title")
        yield Static("──────────────────────────────────────────", classes="section-divider")
        yield Label("Stock Tickers (comma-separated)", classes="field-label")
        yield Label("No API key required — powered by Yahoo Finance", classes="field-hint")
        tickers = ", ".join(sc.get("tickers", []))
        yield Input(value=tickers, placeholder="e.g. AAPL, GOOGL, MSFT, TSLA", id="stocks-tickers")

    def _crypto_section(self):
        cc = self._config.get("crypto", {})
        yield Static("🪙  Crypto", classes="section-title")
        yield Static("──────────────────────────────────────────", classes="section-divider")
        yield Label("Crypto Tickers (comma-separated)", classes="field-label")
        yield Label("Format like BTC-USD", classes="field-hint")
        tickers = ", ".join(cc.get("tickers", []))
        yield Input(value=tickers, placeholder="e.g. BTC-USD, ETH-USD", id="crypto-tickers")

    def _calendar_section(self):
        cc = self._config.get("calendar", {})
        yield Static("📅  Calendar", classes="section-title")
        yield Static("──────────────────────────────────────────", classes="section-divider")
        yield Label("Calendar ICS URL", classes="field-label")
        yield Label("Leave empty for public holidays", classes="field-hint")
        yield Input(value=cc.get("ics_url", ""), placeholder="https://.../basic.ics", id="calendar-url")

    def _github_prs_section(self):
        gc = self._config.get("github_prs", {})
        yield Static("🐙  GitHub PRs", classes="section-title")
        yield Static("──────────────────────────────────────────", classes="section-divider")
        yield Label("GitHub Username", classes="field-label")
        yield Label("Your GitHub handle", classes="field-hint")
        yield Input(value=gc.get("username", ""), placeholder="e.g. octocat", id="github-prs-username")
        yield Label("GitHub PAT (Optional but recommended)", classes="field-label")
        yield Input(value=gc.get("token", ""), placeholder="ghp_...", password=True, id="github-prs-token")

    def _general_section(self):
        gc = self._config.get("general", {})
        yield Static("⚙  General", classes="section-title")
        yield Static("──────────────────────────────────────────", classes="section-divider")
        yield Label("Refresh Interval (seconds)", classes="field-label")
        yield Label("How often to auto-refresh data (default 300)", classes="field-hint")
        yield Input(
            value=str(gc.get("refresh_interval", 300)),
            placeholder="300",
            id="general-refresh",
            type="integer",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.action_save()
        elif event.button.id == "btn-cancel":
            self.action_dismiss()

    def action_save(self) -> None:
        """Collect all field values and save config."""
        from config import save_config

        config = self._config.copy()

        # Weather
        config["weather"]["api_key"] = self.query_one("#weather-api-key", Input).value.strip()
        config["weather"]["location"] = self.query_one("#weather-location", Input).value.strip()
        config["weather"]["units"] = str(self.query_one("#weather-units", Select).value)

        # News
        config["news"]["api_key"] = self.query_one("#news-api-key", Input).value.strip()
        config["news"]["country"] = self.query_one("#news-country", Input).value.strip().lower()

        # YouTube
        if "youtube" not in config:
            config["youtube"] = {}
        config["youtube"]["api_key"] = self.query_one("#youtube-api-key", Input).value.strip()
        config["youtube"]["region_code"] = self.query_one("#youtube-region-code", Input).value.strip().upper()
        # Stocks
        tickers_raw = self.query_one("#stocks-tickers", Input).value
        config["stocks"]["tickers"] = [t.strip().upper() for t in tickers_raw.split(",") if t.strip()]

        # Crypto
        if "crypto" not in config:
            config["crypto"] = {}
        crypto_raw = self.query_one("#crypto-tickers", Input).value
        config["crypto"]["tickers"] = [t.strip().upper() for t in crypto_raw.split(",") if t.strip()]

        # Calendar
        if "calendar" not in config:
            config["calendar"] = {}
        config["calendar"]["ics_url"] = self.query_one("#calendar-url", Input).value.strip()

        # GitHub PRs
        if "github_prs" not in config:
            config["github_prs"] = {}
        config["github_prs"]["username"] = self.query_one("#github-prs-username", Input).value.strip()
        config["github_prs"]["token"] = self.query_one("#github-prs-token", Input).value.strip()

        # General
        try:
            config["general"]["refresh_interval"] = int(self.query_one("#general-refresh", Input).value)
        except ValueError:
            config["general"]["refresh_interval"] = 300

        save_config(config)
        self.dismiss(config)

    def action_dismiss(self) -> None:
        self.dismiss(None)
