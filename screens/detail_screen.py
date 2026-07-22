"""
Detail screen for Pulse — full-screen article/post detail view.
"""

import webbrowser
from typing import Optional

from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Button, Footer, Static


class DetailScreen(Screen):
    """Full-screen detail view for an article or post."""

    BINDINGS = [
        Binding("escape", "dismiss", "Back"),
        Binding("o", "open_url", "Open in Browser"),
        Binding("q", "dismiss", "Back", show=False),
    ]

    CSS = """
    DetailScreen {
        background: #0d0f14;
    }
    #detail-title-bar {
        height: 3;
        background: #1a1d2e;
        color: #e2e8f0;
        padding: 0 2;
        content-align: left middle;
        text-style: bold;
    }
    #detail-scroll {
        height: 1fr;
        padding: 1 4;
    }
    #detail-footer-bar {
        height: 3;
        background: #1a1d2e;
        layout: horizontal;
        align: left middle;
        padding: 0 2;
        color: #94a3b8;
    }
    """

    def __init__(self, title: str, content: str, url: str = "", source: str = "", **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self._content = content
        self._url = url
        self._source = source

    def compose(self) -> ComposeResult:
        yield Static(f"  {self._title[:80]}", id="detail-title-bar")
        with ScrollableContainer(id="detail-scroll"):
            meta = Text()
            if self._source:
                meta.append(f"📰 {self._source}  ", style="#7c3aed")
            if self._url:
                meta.append(self._url, style="underline #06b6d4")
            yield Static(meta)
            yield Static(Text(""))
            if self._content:
                yield Static(self._content)
            else:
                yield Static(Text("No content available. Open in browser for full article.", style="dim #94a3b8"))
        yield Footer()

    def action_open_url(self) -> None:
        if self._url:
            webbrowser.open(self._url)
            self.notify("Opened in browser", severity="information")

    def action_dismiss(self) -> None:
        self.dismiss()
