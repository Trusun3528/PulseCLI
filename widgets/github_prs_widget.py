import webbrowser
from typing import Dict, List

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import DataTable, Static
from textual import work

from config import load_config
from providers.github_prs import fetch_github_prs

class GithubPrsWidget(Widget):
    """GitHub Pull Requests browser."""

    BINDINGS = [
        Binding("enter", "open_pr", "Open PR"),
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    GithubPrsWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #gh-prs-header {
        height: 3;
        background: #1a1d2e;
        color: #94a3b8;
        padding: 0 2;
        content-align: left middle;
    }
    #gh-prs-status {
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
        self._prs: List[Dict] = []

    def compose(self) -> ComposeResult:
        yield Static("🐙  My Pull Requests  ", id="gh-prs-header")
        yield DataTable(id="gh-prs-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="gh-prs-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("  Repository", "Title", "Created", "State")
        self.load_prs()

    @work(exclusive=True, thread=False)
    async def load_prs(self) -> None:
        config = load_config()
        gh_config = config.get("github_prs", {})
        username = gh_config.get("username", "")
        token = gh_config.get("token", "")
        
        table = self.query_one(DataTable)
        table.clear()
        status = self.query_one("#gh-prs-status", Static)
        status.update("[dim]⟳ Fetching pull requests…[/dim]")

        prs = await fetch_github_prs(username, token)
        
        if isinstance(prs, list) and len(prs) > 0 and "error" in prs[0]:
            table.add_row("", Text(f"⚠  {prs[0]['error']}", style="#ef4444"), "", "")
            status.update("")
            return

        self._prs = prs or []

        for i, pr in enumerate(self._prs):
            repo = Text(pr.get("repo", ""), style="bold #a78bfa")
            title = Text(pr.get("title", ""), style="#e2e8f0", no_wrap=True)
            created = Text(pr.get("created_at", ""), style="#64748b")
            state = Text(pr.get("state", "").upper(), style="#10b981")
            
            table.add_row(repo, title, created, state, key=str(i))

        status.update(
            f"[dim] 🐙 GitHub PRs ({username}) · "
            f"{len(self._prs)} open PRs · [bold]Enter[/bold] view in browser[/dim]"
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_open_pr()

    def action_open_pr(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self._prs):
            url = self._prs[table.cursor_row].get("url", "")
            if url:
                webbrowser.open(url)
                self.notify("Opened PR in browser", severity="information")

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_scroll_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_scroll_up()

    def action_refresh(self) -> None:
        self.load_prs()
