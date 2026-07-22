"""
GitHub Trending widget for Pulse.
"""

import webbrowser
from typing import Any, Dict, List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Button, DataTable, Select, Static
from textual import work

from providers.github import LANGUAGES, SINCE_OPTIONS, fetch_trending

SINCE_ICONS = {"daily": "📅", "weekly": "🗓", "monthly": "📆"}
SINCE_LABELS = {"daily": "Today", "weekly": "This Week", "monthly": "This Month"}


class GitHubWidget(Widget):
    """GitHub Trending repository browser."""

    BINDINGS = [
        Binding("enter", "open_repo", "Open on GitHub"),
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    GitHubWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #gh-toolbar {
        height: 3;
        width: 1fr;
        layout: horizontal;
        background: #1a1d2e;
        padding: 0 1;
    }
    #gh-toolbar Button {
        min-width: 14;
        height: 3;
        margin: 0 0 0 1;
        background: #0d0f14;
        color: #94a3b8;
        border: tall #2d3057;
    }
    #gh-toolbar Button.active-since {
        background: #10b981;
        color: #ffffff;
        border: tall #10b981;
    }
    #lang-select {
        width: 26;
        height: 3;
        margin: 0 0 0 1;
    }
    #gh-status {
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
        self._since = "daily"
        self._language = ""
        self._repos: List[Dict] = []

    def compose(self) -> ComposeResult:
        lang_options = [("🌐 All Languages", "")] + [(f"  {lang}", lang) for lang in LANGUAGES if lang]
        with Horizontal(id="gh-toolbar"):
            yield Select(lang_options, id="lang-select", value="")
            for since in SINCE_OPTIONS:
                icon = SINCE_ICONS.get(since, "")
                label = SINCE_LABELS.get(since, since.title())
                btn = Button(
                    f"{icon} {label}",
                    id=f"since-{since}",
                    classes="active-since" if since == "daily" else "",
                )
                yield btn
        yield DataTable(id="gh-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="gh-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("  Repository", "Description", "Lang", "⭐ Stars", "🍴 Forks", "⭐ Period")
        self.load_trending()

    def on_select_changed(self, event: Select.Changed) -> None:
        self._language = str(event.value) if event.value else ""
        self.load_trending()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("since-"):
            self._since = btn_id[6:]
            for btn in self.query("#gh-toolbar Button"):
                btn.remove_class("active-since")
            event.button.add_class("active-since")
            self.load_trending()

    @work(exclusive=True, thread=False)
    async def load_trending(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        status = self.query_one("#gh-status", Static)
        status.update("[dim]⟳ Fetching GitHub Trending…[/dim]")

        repos = await fetch_trending(self._language, self._since)

        if isinstance(repos, dict) and "error" in repos:
            table.add_row(
                Text(f"⚠  {repos['error']}", style="#ef4444"), "", "", "", "", ""
            )
            status.update("")
            return

        self._repos = repos or []

        for i, repo in enumerate(self._repos):
            name = Text(repo["name"], style="bold #e2e8f0", no_wrap=True)
            desc = Text(repo.get("description", ""), style="#94a3b8", no_wrap=True)
            lang = Text(repo.get("language", ""), style="#a78bfa")
            stars = Text(f"⭐ {repo['stars']}", style="#fbbf24", justify="right")
            forks = Text(f"🍴 {repo['forks']}", style="#64748b", justify="right")
            period = Text(repo.get("stars_period", ""), style="#34d399", no_wrap=True)
            table.add_row(name, desc, lang, stars, forks, period, key=str(i))

        since_label = SINCE_LABELS.get(self._since, self._since)
        lang_label = f" · {self._language}" if self._language else ""
        status.update(
            f"[dim] 🐙 GitHub Trending{lang_label} · {since_label} · "
            f"{len(self._repos)} repos · [bold]Enter[/bold] open on GitHub[/dim]"
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_open_repo()

    def action_open_repo(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self._repos):
            url = self._repos[table.cursor_row].get("url", "")
            if url:
                webbrowser.open(url)
                self.notify("Opened on GitHub", severity="information")

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_scroll_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_scroll_up()

    def action_refresh(self) -> None:
        self.load_trending()
