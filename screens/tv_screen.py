"""
TV Mode screen for Pulse — a grid-based dashboard for large displays.
"""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import ContentSwitcher, Static
from datetime import datetime

from widgets.news_widget import NewsWidget
from widgets.youtube_widget import YoutubeWidget
from widgets.weather_widget import WeatherWidget
from widgets.sysinfo_widget import SysInfoWidget
from widgets.calendar_widget import CalendarWidget
from widgets.breaking_news_widget import BreakingNewsWidget
from widgets.marquee_widget import MarqueeWidget
from widgets.qr_widget import QrWidget
from widgets.hackernews_widget import HackerNewsWidget
from widgets.github_widget import GitHubWidget
from widgets.stocks_widget import StocksWidget
from widgets.crypto_widget import CryptoWidget
from widgets.aimodels_widget import AiModelsWidget
from widgets.github_prs_widget import GithubPrsWidget
from widgets.files_widget import FilesWidget
from widgets.packages_widget import PackagesWidget

from config import load_config

WIDGET_MAP = {
    "news": NewsWidget,
    "youtube": YoutubeWidget,
    "hackernews": HackerNewsWidget,
    "github": GitHubWidget,
    "stocks": StocksWidget,
    "crypto": CryptoWidget,
    "system": SysInfoWidget,
    "weather": WeatherWidget,
    "aimodels": AiModelsWidget,
    "calendar": CalendarWidget,
    "github_prs": GithubPrsWidget,
    "files": FilesWidget,
    "packages": PackagesWidget,
    "qr": QrWidget,
}


class TvScreen(Screen):
    """
    A grid-based layout suitable for a TV or large monitor.
    Features alternating main content, side widgets, and a bottom ticker.
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
        Binding("t", "dismiss", "Close TV Mode"),
    ]

    CSS = """
    TvScreen {
        layout: grid;
        grid-size: 4 5;
        grid-columns: 1fr 1fr 1fr 1fr;
        grid-rows: 1 1fr auto 1fr 2;
        background: #0d0f14;
    }
    
    /* Strip away standard dashboard UI clutter for a cleaner TV look */
    TvScreen #hn-toolbar, TvScreen #github-toolbar, TvScreen #news-toolbar, TvScreen #youtube-toolbar, TvScreen #news-status, TvScreen #youtube-status, TvScreen #hn-status, TvScreen #github-status {
        display: none;
    }
    TvScreen DataTable {
        border: none;
        width: 100%;
        height: 100%;
    }
    
    #tv-breaking {
        column-span: 4;
        row-span: 1;
    }
    
    #tv-main {
        column-span: 3;
        row-span: 3;
        border-right: tall #2d3057;
        border-bottom: tall #2d3057;
    }
    
    #tv-weather {
        column-span: 1;
        row-span: 1;
        border-bottom: tall #2d3057;
    }
    
    #tv-qr {
        column-span: 1;
        row-span: 1;
        border-bottom: tall #2d3057;
    }
    
    #tv-side-bot {
        column-span: 1;
        row-span: 1;
        border-bottom: tall #2d3057;
    }
    
    #tv-ticker {
        column-span: 4;
        row-span: 1;
    }
    
    #tv-clock {
        height: 3;
        background: #e60000;
        color: #ffffff;
        content-align: center middle;
        text-style: bold;
        border-bottom: tall #2d3057;
    }
    """

    def compose(self) -> ComposeResult:
        config = load_config()
        tvc = config.get("tv_mode", {})
        
        main_1_id = tvc.get("main_1", "news")
        main_2_id = tvc.get("main_2", "youtube")
        side_1_id = tvc.get("side_1", "calendar")
        side_2_id = tvc.get("side_2", "system")
        qr_spot_id = tvc.get("qr_spot", "qr")
        
        self.tv_main_1_id = f"tv-main1-{main_1_id}"
        self.tv_main_2_id = f"tv-main2-{main_2_id}"
        self.tv_side_1_id = f"tv-side1-{side_1_id}"
        self.tv_side_2_id = f"tv-side2-{side_2_id}"
        
        def get_widget(id_str, fallback, widget_id):
            widget_class = WIDGET_MAP.get(id_str, WIDGET_MAP[fallback])
            return widget_class(id=widget_id)

        yield BreakingNewsWidget(id="tv-breaking")
        
        with Container(id="tv-main"):
            with ContentSwitcher(initial=self.tv_main_1_id, id="main-switcher"):
                yield get_widget(main_1_id, "news", self.tv_main_1_id)
                if main_1_id != main_2_id:
                    yield get_widget(main_2_id, "youtube", self.tv_main_2_id)
        
        with Container(id="tv-weather"):
            yield Static("", id="tv-clock")
            yield WeatherWidget()
            
        yield get_widget(qr_spot_id, "qr", "tv-qr")
            
        with Container(id="tv-side-bot"):
            with ContentSwitcher(initial=self.tv_side_1_id, id="side-switcher"):
                yield get_widget(side_1_id, "calendar", self.tv_side_1_id)
                if side_1_id != side_2_id:
                    yield get_widget(side_2_id, "system", self.tv_side_2_id)
                
        yield MarqueeWidget(id="tv-ticker")

    def on_mount(self) -> None:
        """Set up the timers."""
        self.set_interval(30.0, self.cycle_main_content)
        self.set_interval(20.0, self.cycle_side_content)
        self.set_interval(8.0, self.cycle_active_item)
        self.set_interval(1.0, self.update_clock)
        self.update_clock()
        self.set_timer(2.0, self.update_tv_state)  # initial delay to let data load
        
    def update_clock(self) -> None:
        """Updates the clock widget with the current time and date."""
        try:
            now = datetime.now()
            date_str = now.strftime("%a %b %d")
            time_str = now.strftime("%H:%M:%S")
            self.query_one("#tv-clock", Static).update(f"{date_str}\n{time_str}")
        except Exception:
            pass

    def cycle_main_content(self) -> None:
        """Alternates the main content switcher."""
        try:
            switcher = self.query_one("#main-switcher", ContentSwitcher)
            if not hasattr(self, "tv_main_1_id") or self.tv_main_1_id == self.tv_main_2_id:
                return

            current_widget = self.query_one(f"#{switcher.current}")
            
            if switcher.current == self.tv_main_2_id:
                # Only switch if it's not rate limited
                if not getattr(current_widget, "is_429_error", False):
                    switcher.current = self.tv_main_1_id
                    new_widget = self.query_one(f"#{self.tv_main_1_id}")
                    if hasattr(new_widget, "cycle_category"):
                        new_widget.cycle_category()
            else:
                switcher.current = self.tv_main_2_id
                
            self.update_tv_state()
        except Exception:
            pass

    def cycle_side_content(self) -> None:
        """Alternates the side content switcher."""
        try:
            if not hasattr(self, "tv_side_1_id") or self.tv_side_1_id == self.tv_side_2_id:
                return
            switcher = self.query_one("#side-switcher", ContentSwitcher)
            if switcher.current == self.tv_side_1_id:
                switcher.current = self.tv_side_2_id
            else:
                switcher.current = self.tv_side_1_id
        except Exception:
            pass
            
    def cycle_active_item(self) -> None:
        """Cycles the highlighted row in the active main widget."""
        try:
            switcher = self.query_one("#main-switcher", ContentSwitcher)
            widget = self.query_one(f"#{switcher.current}")
                
            from textual.widgets import DataTable
            table = widget.query_one(DataTable)
            if table.row_count > 0:
                current = table.cursor_row if table.cursor_row is not None else 0
                next_row = (current + 1) % table.row_count
                table.move_cursor(row=next_row)
                
            self.update_tv_state()
        except Exception:
            pass
            
    def _get_url_and_title(self, widget) -> tuple[str, str]:
        from textual.widgets import DataTable
        url = ""
        title = "  TV MODE  "
        try:
            table = widget.query_one(DataTable)
            idx = table.cursor_row if table.cursor_row is not None else 0
            
            if hasattr(widget, "_articles") and widget._articles and len(widget._articles) > idx:
                item = widget._articles[idx]
                url = item.get("url", "")
                title = f"  TOP STORY  |  {item.get('source', '')}  |  {item.get('title', '')}  "
            elif hasattr(widget, "_videos") and widget._videos and len(widget._videos) > idx:
                item = widget._videos[idx]
                url = item.get("url", "")
                title = f"  TRENDING VIDEO  |  {item.get('channel', '')}  |  {item.get('title', '')}  "
            elif hasattr(widget, "_stories") and widget._stories and len(widget._stories) > idx:
                item = widget._stories[idx]
                url = item.get("url", item.get("hn_url", ""))
                title = f"  HACKER NEWS  |  {item.get('title', '')}  "
            elif hasattr(widget, "_repos") and widget._repos and len(widget._repos) > idx:
                item = widget._repos[idx]
                url = item.get("html_url", "")
                title = f"  GITHUB  |  {item.get('name', '')}  "
            elif hasattr(widget, "_prs") and widget._prs and len(widget._prs) > idx:
                item = widget._prs[idx]
                url = item.get("html_url", "")
                title = f"  PULL REQUEST  |  {item.get('title', '')}  "
            elif hasattr(widget, "_quotes") and widget._quotes and len(widget._quotes) > idx:
                item = widget._quotes[idx]
                title = f"  MARKET  |  {item.get('symbol', '')} : {item.get('price', '')}  "
            elif hasattr(widget, "_packages") and widget._packages and len(widget._packages) > idx:
                item = widget._packages[idx]
                title = f"  UPDATE AVAILABLE  |  {item.get('name', '')} {item.get('available', '')}  "
        except Exception:
            pass
        return url, title

    def update_tv_state(self) -> None:
        """Updates the QR code and breaking news bar based on active content."""
        try:
            switcher = self.query_one("#main-switcher", ContentSwitcher)
            active_widget = self.query_one(f"#{switcher.current}")
            
            breaking = self.query_one("#tv-breaking", BreakingNewsWidget)
            url, title_text = self._get_url_and_title(active_widget)
            
            breaking.update_text(title_text)
            
            try:
                qr = self.query_one("#tv-qr", QrWidget)
                if hasattr(qr, "update_url"):
                    qr.update_url(url)
            except Exception:
                pass
        except Exception:
            pass
