"""
Local package updates widget for Pulse.
Displays available updates using the system's package manager.
"""

from typing import Dict, List, Any

from rich.text import Text
import subprocess
from textual.app import ComposeResult
from textual.binding import Binding
from textual.widget import Widget
from textual.widgets import DataTable, Static, Button
from textual.containers import Horizontal
from textual import work

from providers.packages import get_upgradable_packages, get_update_command


class PackagesWidget(Widget):
    """Widget to display available local package updates."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    PackagesWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #packages-status {
        height: 1;
        background: #1a1d2e;
        color: #94a3b8;
        padding: 0 2;
    }
    #packages-controls {
        height: 3;
        align: right middle;
        padding-right: 1;
    }
    DataTable {
        height: 1fr;
        background: #0d0f14;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._packages: List[Dict[str, Any]] = []
        self._manager: str = "Unknown"

    def compose(self) -> ComposeResult:
        with Horizontal(id="packages-controls"):
            yield Button("Update System", id="btn-update", variant="error")
        yield DataTable(id="packages-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="packages-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Package Name", "Current Version", "Available Version")
        self.load_packages()

    @work(exclusive=True, thread=True)
    def load_packages(self) -> None:
        """Fetch package updates in a background thread."""
        self.app.call_from_thread(self._update_status, "[dim]⟳ Querying package manager...[/dim]")
        self.app.call_from_thread(self._clear_table)
        
        result = get_upgradable_packages()
        self.app.call_from_thread(self._populate_table, result)

    def _clear_table(self):
        self.query_one(DataTable).clear()

    def _update_status(self, text: str):
        self.query_one("#packages-status", Static).update(text)

    def _populate_table(self, result: Dict[str, Any]):
        table = self.query_one(DataTable)
        self._packages = result.get("packages", [])
        self._manager = result.get("manager", "Unknown")
        error = result.get("error")

        btn = self.query_one("#btn-update", Button)
        if not get_update_command(self._manager) or not self._packages:
            btn.display = False
        else:
            btn.display = True

        if error:
            table.add_row(Text("Error", style="#ef4444"), Text(error, style="#ef4444"), "")
            self._update_status(f"[dim]⚠ Error querying {self._manager}[/dim]")
            return

        if not self._packages:
            table.add_row(Text("Up to date!", style="#10b981"), "", "")
            self._update_status(f"[dim]✓ System is up to date ({self._manager})[/dim]")
            return

        for i, pkg in enumerate(self._packages):
            name = Text(pkg.get("name", ""), style="#7c3aed", no_wrap=True)
            current = Text(pkg.get("current", ""), style="#64748b", no_wrap=True)
            available = Text(pkg.get("available", ""), style="#06b6d4", no_wrap=True)
            table.add_row(name, current, available, key=str(i))

        self._update_status(f"[dim]📦 {self._manager} · {len(self._packages)} updates available[/dim]")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-update":
            cmd = get_update_command(self._manager)
            if not cmd:
                return
            
            # Use shell execution if it's a single string command (like apt update && apt upgrade)
            use_shell = len(cmd) == 1 and "&&" in cmd[0]
            
            with self.app.suspend():
                print("\n" + "="*50)
                print(f"Running system update via {self._manager}...")
                print("="*50 + "\n")
                if use_shell:
                    subprocess.run(cmd[0], shell=True)
                else:
                    subprocess.run(cmd)
                print("\n" + "="*50)
                print("Update finished! Press Enter to return to the dashboard...")
                input()
                
            self.load_packages()

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_scroll_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_scroll_up()

    def action_refresh(self) -> None:
        self.load_packages()
