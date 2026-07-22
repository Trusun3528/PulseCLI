import webbrowser
from typing import Dict, List

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import DataTable, Static
from textual import work

from providers.aimodels import fetch_trending_models

class AiModelsWidget(Widget):
    """Trending AI Models browser (Hugging Face)."""

    BINDINGS = [
        Binding("enter", "open_model", "Open on Hugging Face"),
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    AiModelsWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #aimodels-header {
        height: 3;
        background: #1a1d2e;
        color: #94a3b8;
        padding: 0 2;
        content-align: left middle;
    }
    #aimodels-status {
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
        self._models: List[Dict] = []

    def compose(self) -> ComposeResult:
        yield Static("🤖  Trending AI Models (Hugging Face)  ", id="aimodels-header")
        yield DataTable(id="aimodels-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="aimodels-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("  Model", "Author", "Task", "⬇️ Downloads")
        self.load_models()

    @work(exclusive=True, thread=False)
    async def load_models(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        status = self.query_one("#aimodels-status", Static)
        status.update("[dim]⟳ Fetching trending AI models…[/dim]")

        models = await fetch_trending_models(limit=30)
        
        if isinstance(models, list) and len(models) > 0 and "error" in models[0]:
            table.add_row("", Text(f"⚠  {models[0]['error']}", style="#ef4444"), "", "")
            status.update("")
            return

        self._models = models or []

        for i, m in enumerate(self._models):
            name = Text(m["id"], style="bold #3b82f6")
            author = Text(m.get("author", ""), style="#94a3b8")
            task = Text(m.get("pipeline_tag", ""), style="#10b981")
            dl = Text(f"{m.get('downloads', 0):,}", justify="right", style="#f59e0b")
            table.add_row(name, author, task, dl, key=str(i))

        status.update(
            f"[dim] 🤖 Trending AI Models · "
            f"{len(self._models)} models · [bold]Enter[/bold] open on Hugging Face[/dim]"
        )

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.action_open_model()

    def action_open_model(self) -> None:
        table = self.query_one(DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self._models):
            url = self._models[table.cursor_row].get("url", "")
            if url:
                webbrowser.open(url)
                self.notify("Opened on Hugging Face", severity="information")

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_scroll_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_scroll_up()

    def action_refresh(self) -> None:
        self.load_models()
