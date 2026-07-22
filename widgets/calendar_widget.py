from typing import Dict, List

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import DataTable, Static
from textual import work

from config import load_config
from providers.calendar import fetch_calendar_events

class CalendarWidget(Widget):
    """Calendar events browser."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    CalendarWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #calendar-header {
        height: 3;
        background: #1a1d2e;
        color: #94a3b8;
        padding: 0 2;
        content-align: left middle;
    }
    #calendar-status {
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

    def compose(self) -> ComposeResult:
        yield Static("📅  Calendar Events  ", id="calendar-header")
        yield DataTable(id="calendar-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="calendar-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("  Date", "Title", "Description")
        self.load_events()

    @work(exclusive=True, thread=False)
    async def load_events(self) -> None:
        config = load_config()
        ics_url = config.get("calendar", {}).get("ics_url", "")
        
        table = self.query_one(DataTable)
        table.clear()
        status = self.query_one("#calendar-status", Static)
        status.update("[dim]⟳ Fetching calendar events…[/dim]")

        events = await fetch_calendar_events(ics_url)
        
        if isinstance(events, list) and len(events) > 0 and "error" in events[0]:
            table.add_row("", Text(f"⚠  {events[0]['error']}", style="#ef4444"), "")
            status.update("")
            return

        for i, e in enumerate(events):
            date = Text(e.get("date", ""), style="bold #10b981")
            title = Text(e.get("title", ""), style="#e2e8f0")
            desc = Text(e.get("description", ""), style="#64748b", no_wrap=True)
            table.add_row(date, title, desc, key=str(i))

        src = "Custom ICS" if ics_url else "World Holidays"
        status.update(f"[dim] 📅 Calendar ({src}) · {len(events)} events · [bold]R[/bold] refresh[/dim]")

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_scroll_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_scroll_up()

    def action_refresh(self) -> None:
        self.load_events()
