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
    TvScreen #news-toolbar, TvScreen #youtube-toolbar, TvScreen #news-status, TvScreen #youtube-status {
        display: none;
    }
    TvScreen DataTable {
        border: none;
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
        yield BreakingNewsWidget(id="tv-breaking")
        
        with Container(id="tv-main"):
            with ContentSwitcher(initial="tv-youtube", id="main-switcher"):
                yield NewsWidget(id="tv-news")
                yield YoutubeWidget(id="tv-youtube")
        
        with Container(id="tv-weather"):
            yield Static("", id="tv-clock")
            yield WeatherWidget()
            
        yield QrWidget(id="tv-qr")
            
        with Container(id="tv-side-bot"):
            with ContentSwitcher(initial="tv-calendar", id="side-switcher"):
                yield CalendarWidget(id="tv-calendar")
                yield SysInfoWidget(id="tv-sysinfo")
                
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
            news_widget = self.query_one("#tv-news", NewsWidget)
            
            if switcher.current == "tv-youtube":
                # Only switch to news if it's not rate limited
                if not getattr(news_widget, "is_429_error", False):
                    switcher.current = "tv-news"
                    if hasattr(news_widget, "cycle_category"):
                        news_widget.cycle_category()
            else:
                switcher.current = "tv-youtube"
                
            self.update_tv_state()
        except Exception:
            pass

    def cycle_side_content(self) -> None:
        """Alternates the side content switcher."""
        try:
            switcher = self.query_one("#side-switcher", ContentSwitcher)
            if switcher.current == "tv-calendar":
                switcher.current = "tv-sysinfo"
            else:
                switcher.current = "tv-calendar"
        except Exception:
            pass
            
    def cycle_active_item(self) -> None:
        """Cycles the highlighted row in the active main widget."""
        try:
            switcher = self.query_one("#main-switcher", ContentSwitcher)
            if switcher.current == "tv-news":
                widget = self.query_one("#tv-news", NewsWidget)
            else:
                widget = self.query_one("#tv-youtube", YoutubeWidget)
                
            from textual.widgets import DataTable
            table = widget.query_one(DataTable)
            if table.row_count > 0:
                current = table.cursor_row if table.cursor_row is not None else 0
                next_row = (current + 1) % table.row_count
                table.move_cursor(row=next_row)
                
            self.update_tv_state()
        except Exception:
            pass
            
    def update_tv_state(self) -> None:
        """Updates the QR code and breaking news bar based on active content."""
        try:
            switcher = self.query_one("#main-switcher", ContentSwitcher)
            qr = self.query_one("#tv-qr", QrWidget)
            breaking = self.query_one("#tv-breaking", BreakingNewsWidget)
            
            from textual.widgets import DataTable
            
            url = ""
            title_text = "  TV MODE  "
            
            if switcher.current == "tv-news":
                news = self.query_one("#tv-news", NewsWidget)
                articles = getattr(news, "_articles", [])
                table = news.query_one(DataTable)
                idx = table.cursor_row if table.cursor_row is not None else 0
                
                if articles and len(articles) > idx:
                    url = articles[idx].get("url", "")
                    src = articles[idx].get("source", "")
                    ttl = articles[idx].get("title", "")
                    title_text = f"  TOP STORY  |  {src}  |  {ttl}  "
            else:
                youtube = self.query_one("#tv-youtube", YoutubeWidget)
                videos = getattr(youtube, "_videos", [])
                table = youtube.query_one(DataTable)
                idx = table.cursor_row if table.cursor_row is not None else 0
                
                if videos and len(videos) > idx:
                    url = videos[idx].get("url", "")
                    ttl = videos[idx].get("title", "")
                    ch = videos[idx].get("channel", "")
                    title_text = f"  TRENDING VIDEO  |  {ch}  |  {ttl}  "
                    
            qr.update_url(url)
            breaking.update_text(title_text)
        except Exception:
            pass
