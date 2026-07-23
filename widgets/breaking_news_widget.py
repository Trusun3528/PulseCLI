"""
Breaking News Widget for TV Mode.
Displays the current top headline or video title.
"""

from textual.widget import Widget
from textual.widgets import Static

class BreakingNewsWidget(Widget):
    """A top-docked bar displaying the current content's title."""
    
    DEFAULT_CSS = """
    BreakingNewsWidget {
        height: 1;
        width: 1fr;
        background: #e60000;
        color: #ffffff;
        content-align: center middle;
        text-style: bold;
    }
    """
    
    def compose(self):
        yield Static("  TV MODE  ", id="breaking-text")

    def update_text(self, text: str):
        self.query_one("#breaking-text", Static).update(text)
