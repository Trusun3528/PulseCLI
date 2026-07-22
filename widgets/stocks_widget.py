"""
Stocks widget for Pulse — real-time quotes with sparklines.
"""

import webbrowser
from typing import Any, Dict, List

from rich.align import Align
from rich.text import Text
from rich.panel import Panel
from textual.app import ComposeResult
from textual.binding import Binding
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import DataTable, Static
from textual import work

from config import load_config
from providers.stocks import fetch_quotes


class StocksWidget(Widget):
    """Stock market ticker with sparklines and price change indicators."""

    BINDINGS = [
        Binding("enter", "open_yahoo", "Open Yahoo Finance"),
        Binding("r", "refresh", "Refresh"),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    DEFAULT_CSS = """
    StocksWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #stocks-header {
        height: 3;
        background: #1a1d2e;
        color: #94a3b8;
        padding: 0 2;
        content-align: left middle;
    }
    #stocks-status {
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

    _quotes: reactive[List[Dict]] = reactive([])

    def compose(self) -> ComposeResult:
        yield Static("", id="stocks-header")
        yield DataTable(id="stocks-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="stocks-status")

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns(
            "  Ticker", "Price", "Change", "Chg %", "Sparkline (7d)",
            "Market Cap", "52W Range",
        )
        self._update_header()
        self.load_quotes()
        # Auto-refresh timer
        self.set_interval(60, self.load_quotes)

    def _update_header(self) -> None:
        from datetime import datetime
        now = datetime.now()
        # Rough market hours check (ET): Mon–Fri, 9:30–16:00
        weekday = now.weekday()  # 0=Mon
        hour = now.hour
        minute = now.minute
        is_open = (weekday < 5) and (
            (hour == 9 and minute >= 30) or (10 <= hour <= 15) or (hour == 16 and minute == 0)
        )
        status = Text()
        status.append("📈  Stock Watchlist  ", style="bold #e2e8f0")
        if is_open:
            status.append("● MARKET OPEN", style="bold #10b981")
        else:
            status.append("● MARKET CLOSED", style="bold #64748b")
        status.append("  (approx. ET)", style="dim")
        self.query_one("#stocks-header", Static).update(status)

    @work(exclusive=True, thread=False)
    async def load_quotes(self) -> None:
        config = load_config()
        tickers = config["stocks"].get("tickers", [])

        table = self.query_one(DataTable)
        table.clear()
        status = self.query_one("#stocks-status", Static)
        status.update("[dim]⟳ Fetching stock quotes…[/dim]")

        if not tickers:
            table.add_row(
                "", Text("No tickers configured. Press S to open Settings.", style="#f59e0b"),
                "", "", "", "", "",
            )
            status.update("")
            return

        quotes = await fetch_quotes(tickers)
        self._quotes = quotes

        for i, q in enumerate(quotes):
            ticker = Text(q["ticker"], style="bold #e2e8f0")

            if "error" in q:
                table.add_row(ticker, Text("Error", style="#ef4444"), Text(q["error"], style="#64748b"), "", "", "", "", key=str(i))
                continue

            price = Text(f"${q['price']:,.2f}", style="#e2e8f0", justify="right")

            chg = q["change"]
            chg_pct = q["change_pct"]
            color = "#22c55e" if chg >= 0 else "#ef4444"
            arrow = "▲" if chg >= 0 else "▼"
            change_t = Text(f"{arrow} {abs(chg):.2f}", style=color, justify="right")
            chg_pct_t = Text(f"{'+' if chg >= 0 else ''}{chg_pct:.2f}%", style=color, justify="right")

            spark = Text(q.get("sparkline", "───────"), style=color)

            cap = Text(q.get("market_cap", ""), style="#64748b")

            low52 = q.get("week_52_low", 0)
            high52 = q.get("week_52_high", 0)
            range_t = Text(f"${low52:.0f} – ${high52:.0f}", style="#475569")

            table.add_row(ticker, price, change_t, chg_pct_t, spark, cap, range_t, key=str(i))

        status.update(
            "[dim] 📈 Stocks · Auto-refresh every 60s · "
            "[bold]Enter[/bold] open Yahoo Finance · [bold]R[/bold] refresh now[/dim]"
        )
        self._update_header()

    def action_open_yahoo(self) -> None:
        table = self.query_one(DataTable)
        quotes = getattr(self, "_quotes", [])
        if table.cursor_row is not None and table.cursor_row < len(quotes):
            ticker = quotes[table.cursor_row].get("ticker", "")
            if ticker:
                url = f"https://finance.yahoo.com/quote/{ticker}"
                webbrowser.open(url)
                self.notify(f"Opened {ticker} on Yahoo Finance", severity="information")

    def action_cursor_down(self) -> None:
        self.query_one(DataTable).action_scroll_down()

    def action_cursor_up(self) -> None:
        self.query_one(DataTable).action_scroll_up()

    def action_refresh(self) -> None:
        self.load_quotes()
