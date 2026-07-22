import os
import webbrowser
from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DirectoryTree, Static
from textual.binding import Binding

class FilesWidget(Widget):
    """File Explorer browser."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    DEFAULT_CSS = """
    FilesWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #files-header {
        height: 3;
        background: #1a1d2e;
        color: #94a3b8;
        padding: 0 2;
        content-align: left middle;
    }
    DirectoryTree {
        height: 1fr;
        background: #0d0f14;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("📂  File Explorer  ", id="files-header")
        yield DirectoryTree(os.path.expanduser("~"), id="files-tree")

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        path = event.path
        if path.exists():
            try:
                webbrowser.open(path.as_uri())
                self.notify(f"Opened {path.name}", severity="information")
            except Exception as e:
                self.notify(f"Failed to open file: {e}", severity="error")

    def action_refresh(self) -> None:
        tree = self.query_one(DirectoryTree)
        tree.reload()
