"""
Pulse — Main Textual application.
A beautiful, interactive terminal dashboard for news, weather, YouTube Trending, and more.
"""

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual import work
from textual.widgets import Footer, Header, TabbedContent, TabPane

from config import load_config
from screens.settings_screen import SettingsScreen
from widgets.github_widget import GitHubWidget
from widgets.hackernews_widget import HackerNewsWidget
from widgets.news_widget import NewsWidget
from widgets.youtube_widget import YoutubeWidget
from widgets.stocks_widget import StocksWidget
from widgets.sysinfo_widget import SysInfoWidget
from widgets.weather_widget import WeatherWidget


class PulseApp(App):
    """Pulse — your personal terminal dashboard."""

    TITLE = "Pulse"
    SUB_TITLE = "Terminal Dashboard"
    CSS_PATH = "app.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("s", "settings", "Settings"),
        Binding("r", "refresh_current", "Refresh"),
        Binding("1", "switch_tab('weather')", "Weather", show=False),
        Binding("2", "switch_tab('news')", "News", show=False),
        Binding("3", "switch_tab('youtube')", "YouTube", show=False),
        Binding("4", "switch_tab('hackernews')", "Hacker News", show=False),
        Binding("5", "switch_tab('github')", "GitHub", show=False),
        Binding("6", "switch_tab('stocks')", "Stocks", show=False),
        Binding("7", "switch_tab('system')", "System", show=False),
        Binding("ctrl+r", "refresh_current", "Refresh", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with TabbedContent(id="main-tabs", initial="weather"):
            with TabPane("  🌤  Weather  ", id="weather"):
                yield WeatherWidget()
            with TabPane("  📰  News  ", id="news"):
                yield NewsWidget()
            with TabPane("  ▶️  YouTube  ", id="youtube"):
                yield YoutubeWidget()
            with TabPane("  🔥  Hacker News  ", id="hackernews"):
                yield HackerNewsWidget()
            with TabPane("  🐙  GitHub  ", id="github"):
                yield GitHubWidget()
            with TabPane("  📈  Stocks  ", id="stocks"):
                yield StocksWidget()
            with TabPane("  🖥  System  ", id="system"):
                yield SysInfoWidget()
        yield Footer()

    def on_mount(self) -> None:
        """Set up auto-refresh timer on mount."""
        config = load_config()
        interval = config.get("general", {}).get("refresh_interval", 300)
        self.set_interval(interval, self.action_refresh_current)

    @work
    async def action_settings(self) -> None:
        """Open the settings screen."""
        config = load_config()
        result = await self.push_screen_wait(SettingsScreen(config))
        if result is not None:
            # Settings were saved — notify and refresh the active tab
            self.notify("Settings saved! Refreshing data…", severity="information", timeout=3)
            self.action_refresh_current()

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab by ID."""
        try:
            self.query_one(TabbedContent).active = tab_id
        except Exception:
            pass

    def action_refresh_current(self) -> None:
        """Refresh the currently active tab's widget."""
        try:
            tabs = self.query_one(TabbedContent)
            active = tabs.active
            widget_map = {
                "weather": WeatherWidget,
                "news": NewsWidget,
                "youtube": YoutubeWidget,
                "hackernews": HackerNewsWidget,
                "github": GitHubWidget,
                "stocks": StocksWidget,
                "system": SysInfoWidget,
            }
            widget_class = widget_map.get(active)
            if widget_class:
                widget = self.query_one(widget_class)
                if hasattr(widget, "load_data"):
                    widget.load_data()
                elif hasattr(widget, "load_news"):
                    widget.load_news()
                elif hasattr(widget, "load_posts"):
                    widget.load_posts()
                elif hasattr(widget, "load_stories"):
                    widget.load_stories()
                elif hasattr(widget, "load_trending"):
                    widget.load_trending()
                elif hasattr(widget, "load_quotes"):
                    widget.load_quotes()
        except Exception:
            pass
