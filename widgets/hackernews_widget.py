"""
Hacker News widget for Pulse.
"""

import webbrowser
from typing import Any, Dict, List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Button, DataTable, Static
from textual import work

from providers.hackernews import STORY_TYPES, fetch_stories

TYPE_ICONS = {
    "top": "🔝",
    "new": "✨",
    "best": "⭐",
    "ask": "❓",
    "show": "🎉",
}


class HackerNewsWidget(Widget):
    """Hacker News stories browser."""

    BINDINGS = [
        Binding("enter", "open_story", "Open Article"),
        Binding("c", "open_hn", "Open HN Thread"),
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    HackerNewsWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #hn-toolbar {
        height: 3;
        width: 1fr;
        layout: horizontal;
        background: #1a1d2e;
        padding: 0 1;
    }
    #hn-toolbar Button {
        min-width: 12;
        height: 3;
        margin: 0 0 0 1;
        background: #0d0f14;
        color: #94a3b8;
        border: tall #2d3057;
    }
    #hn-toolbar Button.active-type {
        background: #f97316;
        color: #ffffff;
        border: tall #f97316;
    }
    #hn-status {
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
        self._story_type = "top"
        self._stories: List[Dict] = []

    def compose(self) -> ComposeResult:
        with Horizontal(id="hn-toolbar"):
            for st in STORY_TYPES:
                icon = TYPE_ICONS.get(st, "")
                btn = Button(
                    f"{icon} {st.title()}",
                    id=f"type-{st}",
                    classes="active-type" if st == "top" else "",
                )
                yield btn
        yield DataTable(id="hn-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="hn-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("  Points", "💬", "Title", "Domain", "By")
        self.load_stories()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("type-"):
            self._story_type = btn_id[5:]
            for btn in self.query("#hn-toolbar Button"):
                btn.remove_class("active-type")
            event.button.add_class("active-type")
            self.load_stories()

    @work(exclusive=True, thread=False)
    async def load_stories(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        status = self.query_one("#hn-status", Static)
        status.update("[dim]⟳ Fetching Hacker News…[/dim]")

        stories = await fetch_stories(self._story_type, limit=30)

        if isinstance(stories, dict) and "error" in stories:
            table.add_row("", "", Text(f"⚠  {stories['error']}", style="#ef4444"), "", "")
            status.update("")
            return

        self._stories = stories or []

        for i, s in enumerate(self._stories):
            pts = Text(f"▲ {s['score']}", style="#f97316", justify="right")
            cmts = Text(str(s["comments"]), style="#64748b", justify="right")
            title = Text(s["title"], no_wrap=True)
            domain = Text(s.get("domain", ""), style="#475569", no_wrap=True)
            author = Text(s.get("author", ""), style="#7c3aed")
            table.add_row(pts, cmts, title, domain, author, key=str(i))

        icon = TYPE_ICONS.get(self._story_type, "")
        status.update(
            f"[dim] 🔥 Hacker News {icon} {self._story_type.title()} · "
            f"{len(self._stories)} stories · [bold]Enter[/bold] open · [bold]C[/bold] HN thread[/dim]"
        )

    def action_open_story(self) -> None:
        self._open("url")

    def action_open_hn(self) -> None:
        self._open("hn_url")

    def _open(self, key: str) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self._stories):
            url = self._stories[table.cursor_row].get(key, "")
            if url:
                webbrowser.open(url)
                self.notify("Opened in browser", severity="information")

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_scroll_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_scroll_up()

    def action_refresh(self) -> None:
        self.load_stories()
