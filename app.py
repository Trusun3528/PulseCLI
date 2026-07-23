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
from screens.tv_screen import TvScreen
from widgets.github_widget import GitHubWidget
from widgets.hackernews_widget import HackerNewsWidget
from widgets.news_widget import NewsWidget
from widgets.youtube_widget import YoutubeWidget
from widgets.stocks_widget import StocksWidget
from widgets.sysinfo_widget import SysInfoWidget
from widgets.weather_widget import WeatherWidget
from widgets.crypto_widget import CryptoWidget
from widgets.aimodels_widget import AiModelsWidget
from widgets.calendar_widget import CalendarWidget
from widgets.github_prs_widget import GithubPrsWidget
from widgets.files_widget import FilesWidget
from widgets.qr_generator_widget import QrGeneratorWidget


class PulseApp(App):
    """Pulse — your personal terminal dashboard."""

    TITLE = "Pulse"
    SUB_TITLE = "Terminal Dashboard"
    CSS_PATH = "app.tcss"

    # Keyboard bindings available globally within the app.
    # Format is Binding(key, action, description)
    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("s", "settings", "Settings"),
        Binding("t", "tv_mode", "TV Mode"),
        Binding("r", "refresh_current", "Refresh"),
        Binding("a", "toggle_auto_scroll", "Auto-Scroll"),
        Binding("1", "switch_tab('weather')", "Weather", show=False),
        Binding("2", "switch_tab('news')", "News", show=False),
        Binding("3", "switch_tab('youtube')", "YouTube", show=False),
        Binding("4", "switch_tab('hackernews')", "Hacker News", show=False),
        Binding("5", "switch_tab('github')", "GitHub", show=False),
        Binding("6", "switch_tab('stocks')", "Stocks", show=False),
        Binding("7", "switch_tab('system')", "System", show=False),
        Binding("8", "switch_tab('crypto')", "Crypto", show=False),
        Binding("9", "switch_tab('aimodels')", "AI Models", show=False),
        Binding("0", "switch_tab('calendar')", "Calendar", show=False),
        Binding("-", "switch_tab('github_prs')", "PRs", show=False),
        Binding("=", "switch_tab('files')", "Files", show=False),
        Binding("[", "switch_tab('qrgen')", "QR Gen", show=False),
        Binding("ctrl+r", "refresh_current", "Refresh", show=False),
    ]

    def compose(self) -> ComposeResult:
        """
        Builds the user interface of the application.
        This method yields the widgets that make up the layout.
        """
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
            with TabPane("  🪙  Crypto  ", id="crypto"):
                yield CryptoWidget()
            with TabPane("  🤖  AI Models  ", id="aimodels"):
                yield AiModelsWidget()
            with TabPane("  📅  Calendar  ", id="calendar"):
                yield CalendarWidget()
            with TabPane("  🐙  PRs  ", id="github_prs"):
                yield GithubPrsWidget()
            with TabPane("  📂  Files  ", id="files"):
                yield FilesWidget()
            with TabPane("  📱  QR Gen  ", id="qrgen"):
                yield QrGeneratorWidget()
        yield Footer()

    def on_mount(self) -> None:
        """
        Called when the application starts (is mounted).
        Sets up the auto-refresh timer based on the user's config.
        """
        config = load_config()
        interval = config.get("general", {}).get("refresh_interval", 300)
        self.set_interval(interval, self.action_refresh_current)

    @work
    async def action_settings(self) -> None:
        """
        Action triggered by pressing the 's' key.
        Opens the settings screen asynchronously to allow the user to modify configuration.
        """
        config = load_config()
        result = await self.push_screen_wait(SettingsScreen(config))
        if result is not None:
            # Settings were saved — notify and refresh the active tab
            self.notify("Settings saved! Refreshing data…", severity="information", timeout=3)
            self.action_refresh_current()

    def action_tv_mode(self) -> None:
        """
        Action triggered by 't'. Pushes the TV Mode screen.
        """
        self.push_screen(TvScreen())

    def action_switch_tab(self, tab_id: str) -> None:
        """
        Action triggered by pressing number keys to switch tabs.
        
        Args:
            tab_id (str): The ID of the tab to switch to (e.g., 'weather', 'news').
        """
        try:
            self.query_one(TabbedContent).active = tab_id
        except Exception:
            pass

    def action_toggle_auto_scroll(self) -> None:
        """
        Action triggered by 'a'. Toggles automatic cycling of tabs every few seconds.
        """
        if hasattr(self, "auto_scroll_timer") and self.auto_scroll_timer is not None:
            self.auto_scroll_timer.stop()
            self.auto_scroll_timer = None
            self.notify("Auto-scroll disabled", severity="information", timeout=2)
        else:
            self.auto_scroll_timer = self.set_interval(5.0, self.cycle_next_tab)
            self.notify("Auto-scroll enabled", severity="information", timeout=2)

    def cycle_next_tab(self) -> None:
        """
        Cycles to the next tab in the dashboard.
        """
        try:
            tabs = self.query_one(TabbedContent)
            current = tabs.active
            tab_ids = [
                "weather", "news", "youtube", "hackernews", "github",
                "stocks", "system", "crypto", "aimodels", "calendar",
                "github_prs", "files", "qrgen"
            ]
            if current in tab_ids:
                next_idx = (tab_ids.index(current) + 1) % len(tab_ids)
                tabs.active = tab_ids[next_idx]
        except Exception:
            pass

    def action_refresh_current(self) -> None:
        """
        Action triggered by pressing 'r'.
        Refreshes the currently active tab's widget by calling its specific load method.
        """
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
                "crypto": CryptoWidget,
                "aimodels": AiModelsWidget,
                "calendar": CalendarWidget,
                "github_prs": GithubPrsWidget,
                "files": FilesWidget,
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
                elif hasattr(widget, "load_events"):
                    widget.load_events()
                elif hasattr(widget, "load_prs"):
                    widget.load_prs()
                elif hasattr(widget, "load_models"):
                    widget.load_models()
                elif hasattr(widget, "action_refresh"):
                    widget.action_refresh()
        except Exception:
            pass
