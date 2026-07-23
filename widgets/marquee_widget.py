"""
Marquee ticker widget for TV Mode.
Scrolls stock and crypto prices continuously across the bottom of the screen.
"""

from textual.widget import Widget
from textual.widgets import Static
from textual.containers import ScrollableContainer
from textual.reactive import reactive
from textual import work
from config import load_config
from providers.stocks import fetch_quotes
from rich.text import Text

class MarqueeWidget(ScrollableContainer):
    """A scrolling text marquee."""

    DEFAULT_CSS = """
    MarqueeWidget {
        height: 2;
        width: 1fr;
        background: #111420;
        color: #e2e8f0;
        overflow-x: hidden;
        overflow-y: hidden;
        border-top: tall #2d3057;
    }
    #marquee-text {
        height: 1;
        width: auto;
    }
    """
    
    _quotes = reactive([])

    def compose(self):
        yield Static("", id="marquee-text")

    def on_mount(self):
        self.load_data()
        self.set_interval(60, self.load_data)
        self.set_interval(0.15, self.scroll_ticker)

    @work(exclusive=True, thread=False)
    async def load_data(self):
        config = load_config()
        sc = config.get("stocks", {}).get("tickers", [])
        cc = config.get("crypto", {}).get("tickers", [])
        tickers = sc + cc
        
        if not tickers:
            self.query_one(Static).update("   No tickers configured. Press S in normal mode to open Settings.   ")
            return

        quotes = await fetch_quotes(tickers)
        self._quotes = quotes
        
        t = Text()
        # Build a very long string by repeating the quotes a few times
        for _ in range(10):
            for q in quotes:
                if "error" in q: continue
                ticker = q["ticker"]
                price = f"${q['price']:,.2f}"
                chg = q["change"]
                arrow = "▲" if chg >= 0 else "▼"
                color = "#22c55e" if chg >= 0 else "#ef4444"
                
                t.append(f"{ticker} ", style="bold")
                t.append(f"{price} ")
                t.append(f"{arrow} {abs(chg):.2f}        •        ", style=color)
                
        # Space at the start
        final_t = Text("        •        ")
        final_t.append(t)
        
        static = self.query_one("#marquee-text", Static)
        static.update(final_t)

    def scroll_ticker(self):
        if not self._quotes:
            return
            
        # Scroll right by 1 column
        # If we reach the end of the first loop, we could reset it, but with 10 repetitions,
        # it will take a long time to run out. To be safe, we can reset scroll_x if it gets too large.
        if self.scroll_x > 5000:
            self.scroll_x = 0
        else:
            self.scroll_x += 1
