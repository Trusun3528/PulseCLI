"""
News widget for Pulse — scrollable top headlines with category filter.
"""

import webbrowser
from typing import Any, Dict, List, Optional

from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label, Static
from textual import work

from config import load_config
from providers.news import CATEGORIES, CATEGORY_ICONS, fetch_headlines


class NewsWidget(Widget):
    """
    News headlines browser widget with a category filter.
    Displays headlines fetched from NewsAPI in a scrollable data table.
    """

    BINDINGS = [
        Binding("enter", "open_article", "Open in Browser"),
        Binding("r", "refresh", "Refresh"),
    ]

    DEFAULT_CSS = """
    NewsWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #news-toolbar {
        height: 3;
        width: 1fr;
        layout: horizontal;
        background: #1a1d2e;
        padding: 0 1;
    }
    #news-toolbar Button {
        min-width: 14;
        height: 3;
        margin: 0 0 0 1;
        background: #0d0f14;
        color: #94a3b8;
        border: tall #2d3057;
    }
    #news-toolbar Button.active-cat {
        background: #7c3aed;
        color: #ffffff;
        border: tall #7c3aed;
    }
    #news-table {
        height: 1fr;
    }
    DataTable {
        height: 1fr;
        background: #0d0f14;
    }
    #news-status {
        height: 1;
        background: #1a1d2e;
        color: #94a3b8;
        padding: 0 2;
    }
    """

    current_category: reactive[str] = reactive("general")

    def compose(self) -> ComposeResult:
        """
        Build the widget layout. Yields a top toolbar for categories,
        a data table for headlines, and a status bar at the bottom.
        """
        with Horizontal(id="news-toolbar"):
            for cat in CATEGORIES:
                icon = CATEGORY_ICONS.get(cat, "📰")
                label = f"{icon} {cat.title()}"
                btn = Button(label, id=f"cat-{cat}", classes="active-cat" if cat == "general" else "")
                yield btn
        yield DataTable(id="news-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="news-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("  Source", "Title", "Age")
        table.cursor_type = "row"
        self.load_news()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("cat-"):
            cat = btn_id[4:]
            # Update active button styling
            for btn in self.query("#news-toolbar Button"):
                btn.remove_class("active-cat")
            event.button.add_class("active-cat")
            self.current_category = cat
            self.load_news()

    @work(exclusive=True, thread=False)
    async def load_news(self) -> None:
        """
        Asynchronously fetches and populates the data table with news headlines
        based on the user's config and selected category.
        """
        config = load_config()
        nc = config["news"]

        table = self.query_one(DataTable)
        table.clear()
        status = self.query_one("#news-status", Static)
        status.update("[dim]⟳ Fetching headlines…[/dim]")

        articles = await fetch_headlines(
            nc.get("api_key", ""),
            nc.get("country", "us"),
            self.current_category,
            nc.get("page_size", 25),
        )

        if articles is None or (isinstance(articles, dict) and "error" in articles):
            err = (articles or {}).get("error", "unknown") if isinstance(articles, dict) else "unknown"
            if err == "no_key":
                table.add_row("", self._no_key_text(), "")
            else:
                table.add_row("", Text(f"⚠  Error: {err}", style="#ef4444"), "")
            status.update("")
            return

        self._articles = articles  # store for open action

        for i, a in enumerate(articles):
            source = Text(a["source"], style="#7c3aed", no_wrap=True)
            title = Text(a["title"], no_wrap=True)
            age = Text(a["time_ago"], style="#64748b", justify="right")
            table.add_row(source, title, age, key=str(i))

        fallback = articles[0].get("fallback_country", "") if articles else ""
        fallback_note = f"  [dim #f59e0b]⚠ No '{fallback.upper()}' articles on free tier — showing US[/]" if fallback else ""
        status.update(f"[dim] {len(articles)} articles · Press [bold]Enter[/bold] to open · [bold]R[/bold] refresh[/dim]{fallback_note}")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_open_article()

    def action_open_article(self) -> None:
        """
        Opens the currently selected article's URL in the system's default web browser.
        """
        table = self.query_one(DataTable)
        if table.cursor_row is None:
            return
        articles = getattr(self, "_articles", [])
        if table.cursor_row < len(articles):
            url = articles[table.cursor_row].get("url", "")
            if url:
                webbrowser.open(url)
                self.notify(f"Opened in browser", severity="information")

    def action_refresh(self) -> None:
        self.load_news()

    def _no_key_text(self) -> Text:
        t = Text()
        t.append("🔑  No NewsAPI key configured. Press ", style="#f59e0b")
        t.append("S", style="bold #7c3aed")
        t.append(" to open Settings.", style="#f59e0b")
        return t
