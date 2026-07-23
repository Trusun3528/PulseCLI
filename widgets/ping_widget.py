"""
Ping Monitor Widget for Pulse.
Continuously pings a configured list of targets.
"""

from typing import List, Dict, Any
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import DataTable, Static
from textual import work

from providers.ping import ping_targets
from config import load_config


class PingWidget(Widget):
    """Widget to display ping latency and status."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    PingWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #ping-status {
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
        self._targets: List[Dict[str, str]] = []
        # Store interval object to clear it if needed
        self._refresh_interval = None

    def compose(self) -> ComposeResult:
        yield DataTable(id="ping-table", cursor_type="row", zebra_stripes=True)
        yield Static("Initializing...", id="ping-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Name", "Host", "Status", "Latency")
        
        # Load targets from config
        config = load_config().get("ping", {})
        self._targets = config.get("targets", [
            {"name": "Google DNS", "host": "8.8.8.8"},
            {"name": "Cloudflare", "host": "1.1.1.1"}
        ])
        
        # Start initial load
        self.load_pings()
        
        # Set up an interval to refresh automatically every 15 seconds
        self._refresh_interval = self.set_interval(15.0, self.load_pings)

    @work(exclusive=True, thread=True)
    def load_pings(self) -> None:
        """Fetch ping data in a background thread."""
        self.app.call_from_thread(self._update_status, "[dim]⟳ Pinging targets...[/dim]")
        
        results = ping_targets(self._targets)
        
        self.app.call_from_thread(self._populate_table, results)

    def _update_status(self, text: str):
        try:
            self.query_one("#ping-status", Static).update(text)
        except Exception:
            pass

    def _populate_table(self, results: List[Dict[str, Any]]):
        table = self.query_one(DataTable)
        
        # Clear table while preserving columns
        table.clear()

        online_count = 0
        for i, res in enumerate(results):
            name = Text(res.get("name", ""), style="#7c3aed", no_wrap=True)
            host = Text(res.get("host", ""), style="#64748b", no_wrap=True)
            
            status_text = res.get("status", "Unknown")
            if status_text == "Online":
                status = Text("⬤ Online", style="#10b981")
                online_count += 1
            else:
                status = Text("⬤ Offline", style="#ef4444")
                
            latency_text = res.get("latency", "-")
            lat_float = 0.0
            try:
                lat_float = float(latency_text.replace("ms", ""))
            except ValueError:
                pass
                
            # Color latency
            lat_style = "#10b981" # Green
            if lat_float > 150:
                lat_style = "#ef4444" # Red
            elif lat_float > 50:
                lat_style = "#eab308" # Yellow
                
            latency = Text(latency_text, style=lat_style)
            
            table.add_row(name, host, status, latency, key=str(i))

        self._update_status(f"[dim]✓ {online_count}/{len(results)} hosts online · Auto-refreshing[/dim]")

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_scroll_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_scroll_up()

    def action_refresh(self) -> None:
        self.load_pings()
