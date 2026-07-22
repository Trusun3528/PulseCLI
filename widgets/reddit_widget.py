"""
Reddit posts widget for Pulse — browse subreddits with sort control.
"""

import webbrowser
from typing import Any, Dict, List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, DataTable, Select, Static
from textual import work

from config import load_config
from providers.reddit import SORT_OPTIONS, fetch_posts

SORT_ICONS = {"hot": "🔥", "new": "✨", "top": "🏆", "rising": "📈"}


class RedditWidget(Widget):
    """Reddit post browser with subreddit and sort selectors."""

    BINDINGS = [
        Binding("enter", "open_post", "Open in Browser"),
        Binding("c", "open_comments", "Open Comments"),
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    RedditWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #reddit-toolbar {
        height: 3;
        width: 1fr;
        layout: horizontal;
        background: #1a1d2e;
        padding: 0 1;
    }
    #reddit-toolbar Button {
        min-width: 12;
        height: 3;
        margin: 0 0 0 1;
        background: #0d0f14;
        color: #94a3b8;
        border: tall #2d3057;
    }
    #reddit-toolbar Button.active-sort {
        background: #ef4444;
        color: #ffffff;
        border: tall #ef4444;
    }
    #subreddit-select {
        width: 28;
        height: 3;
        margin: 0 1 0 0;
    }
    #reddit-status {
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

    current_sort: reactive[str] = reactive("hot")

    def compose(self) -> ComposeResult:
        config = load_config()
        subreddits = config["reddit"].get("subreddits", ["programming"])
        self._subreddits = subreddits
        self._current_sub = subreddits[0] if subreddits else "programming"

        with Horizontal(id="reddit-toolbar"):
            sub_options = [(f"r/{s}", s) for s in subreddits]
            yield Select(sub_options, id="subreddit-select", value=self._current_sub)
            for sort in SORT_OPTIONS:
                icon = SORT_ICONS.get(sort, "")
                btn = Button(
                    f"{icon} {sort.title()}",
                    id=f"sort-{sort}",
                    classes="active-sort" if sort == "hot" else "",
                )
                yield btn

        yield DataTable(id="reddit-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="reddit-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("  Score", "Awards", "Title", "Comments", "Domain")
        self.load_posts()

    def on_select_changed(self, event: Select.Changed) -> None:
        self._current_sub = str(event.value)
        self.load_posts()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""
        if btn_id.startswith("sort-"):
            sort = btn_id[5:]
            for btn in self.query("#reddit-toolbar Button"):
                btn.remove_class("active-sort")
            event.button.add_class("active-sort")
            self.current_sort = sort
            self.load_posts()

    @work(exclusive=True, thread=False)
    async def load_posts(self) -> None:
        config = load_config()
        rc = config["reddit"]

        table = self.query_one(DataTable)
        table.clear()
        status = self.query_one("#reddit-status", Static)
        status.update(f"[dim]⟳ Fetching r/{self._current_sub}…[/dim]")

        posts = await fetch_posts(
            self._current_sub,
            sort=self.current_sort,
            limit=rc.get("limit", 25),
            client_id=rc.get("client_id", ""),
            client_secret=rc.get("client_secret", ""),
            user_agent=rc.get("user_agent", "pulse-cli:v1.0"),
        )

        if isinstance(posts, dict) and posts.get("error") == "no_credentials":
            table.add_row(
                "", "",
                Text("🔑  Reddit requires a free API key. Press S → open Settings → add Client ID & Secret.", style="#f59e0b"),
                "", "",
            )
            status.update(
                "[dim] Get free credentials at [bold]reddit.com/prefs/apps[/bold] "
                "→ Create App → script type → copy Client ID & Secret[/dim]"
            )
            return

        if isinstance(posts, dict) and "error" in posts:
            table.add_row("", "", Text(f"⚠  {posts['error']}", style="#ef4444"), "", "")
            status.update("")
            return

        # Handle list with single error dict
        if posts and isinstance(posts[0], dict) and "error" in posts[0]:
            table.add_row("", "", Text(f"⚠  {posts[0]['error']}", style="#ef4444"), "", "")
            status.update("")
            return

        self._posts = posts or []

        for i, p in enumerate(self._posts):
            score = Text(f"▲ {p['score']}", style="#ff6b35", justify="right")
            awards = Text("🏅" * min(p["awards"], 3) if p["awards"] else " ", justify="center")
            title_text = Text(no_wrap=True)
            if p.get("flair"):
                title_text.append(f"[{p['flair']}] ", style="#7c3aed")
            title_text.append(p["title"])
            comments = Text(f"💬 {p['num_comments']:,}", style="#64748b", justify="right")
            domain = Text(p.get("domain", ""), style="#475569", no_wrap=True)
            table.add_row(score, awards, title_text, comments, domain, key=str(i))

        icon = SORT_ICONS.get(self.current_sort, "")
        status.update(
            f"[dim] r/{self._current_sub} · {icon} {self.current_sort.title()} · "
            f"{len(self._posts)} posts · [bold]Enter[/bold] open link · [bold]C[/bold] comments · [bold]J/K[/bold] navigate[/dim]"
        )

    def action_open_post(self) -> None:
        self._open_url_for_row("url")

    def action_open_comments(self) -> None:
        self._open_url_for_row("permalink")

    def _open_url_for_row(self, key: str) -> None:
        table = self.query_one(DataTable)
        posts = getattr(self, "_posts", [])
        if table.cursor_row is not None and table.cursor_row < len(posts):
            url = posts[table.cursor_row].get(key, "")
            if url:
                webbrowser.open(url)
                self.notify("Opened in browser", severity="information")

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_scroll_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_scroll_up()

    def action_refresh(self) -> None:
        self.load_posts()
