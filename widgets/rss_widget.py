"""
RSS Feed Widget for Pulse.
Displays the latest articles from a configured RSS or Atom feed.
"""

import webbrowser
from typing import List, Dict, Any

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import DataTable, Static
from textual import work

from providers.rss import get_rss_feed
from config import load_config


class RSSWidget(Widget):
    """Widget to display RSS feed articles."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("enter", "open_link", "Open Link"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    RSSWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #rss-status {
        height: 1;
        background: #1a1d2e;
        color: #94a3b8;
        padding: 0 2;
    }
    DataTable {
        height: 1fr;
        background: #0d0f14;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._articles: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield DataTable(id="rss-table", cursor_type="row", zebra_stripes=True)
        yield Static("Initializing...", id="rss-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Published", "Title")
        self.load_feed()
        # Set up an interval to refresh automatically every 5 minutes
        self.set_interval(300.0, self.load_feed)

    @work(exclusive=True, thread=True)
    def load_feed(self) -> None:
        """Fetch feed data in a background thread."""
        self.app.call_from_thread(self._update_status, "[dim]⟳ Fetching RSS feed...[/dim]")
        
        config = load_config().get("rss", {})
        url = config.get("url", "https://news.ycombinator.com/rss")
        limit = config.get("limit", 25)
        
        result = get_rss_feed(url, limit)
        self.app.call_from_thread(self._populate_table, result)

    def _update_status(self, text: str):
        try:
            self.query_one("#rss-status", Static).update(text)
        except Exception:
            pass

    def _populate_table(self, result: Dict[str, Any]):
        table = self.query_one(DataTable)
        
        # Clear table while preserving columns
        table.clear()
        
        self._articles = result.get("articles", [])
        error = result.get("error")
        feed_title = result.get("title", "RSS")

        if error:
            table.add_row(Text("Error", style="#ef4444"), Text(error, style="#ef4444"), key="error")
            self._update_status(f"[dim]⚠ Error fetching feed[/dim]")
            return

        if not self._articles:
            table.add_row(Text("-", style="#64748b"), Text("No articles found in this feed.", style="#64748b"), key="empty")
            self._update_status(f"[dim]✓ Empty feed[/dim]")
            return

        for i, article in enumerate(self._articles):
            published = Text(article.get("published", "")[:20], style="#64748b", no_wrap=True)
            title = Text(article.get("title", ""), style="#e2e8f0")
            table.add_row(published, title, key=str(i))

        self._update_status(f"[dim]📰 {feed_title} · {len(self._articles)} articles[/dim]")

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_scroll_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_scroll_up()

    def action_open_link(self) -> None:
        table = self.query_one(DataTable)
        try:
            row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
            index = int(row_key.value)
            link = self._articles[index].get("link")
            if link:
                webbrowser.open(link)
        except (ValueError, TypeError, IndexError, AttributeError):
            pass

    def action_refresh(self) -> None:
        self.load_feed()
