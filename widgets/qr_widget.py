"""
QR Code widget for TV Mode.
Displays a QR code for the current article or video.
"""

import io
import segno
from textual.widget import Widget
from textual.widgets import Static
from rich.text import Text

class QrWidget(Widget):
    """A QR code display."""

    DEFAULT_CSS = """
    QrWidget {
        height: 1fr;
        width: 1fr;
        content-align: center middle;
        border-bottom: tall #2d3057;
        background: #000000;
        overflow: hidden;
    }
    #qr-text {
        color: #ffffff;
        background: #000000;
        width: auto;
    }
    """

    def compose(self):
        yield Static("Scan to Open\nLoading...", id="qr-text")

    def update_url(self, url: str):
        if not url:
            self.query_one("#qr-text", Static).update("No URL")
            return
            
        try:
            qr = segno.make(url, micro=False, error="L")
            matrix = qr.matrix
            qz = 2
            width = len(matrix[0])
            full_width = width + (qz * 2)
            
            lines = []
            for y in range(-qz, len(matrix) + qz, 2):
                line = ""
                for x in range(-qz, full_width - qz):
                    top_dark = False
                    if 0 <= y < len(matrix) and 0 <= x < width:
                        top_dark = matrix[y][x]
                    bottom_dark = False
                    if y+1 >= 0 and y+1 < len(matrix) and 0 <= x < width:
                        bottom_dark = matrix[y+1][x]
                        
                    if not top_dark and not bottom_dark: line += "█"
                    elif not top_dark and bottom_dark: line += "▀"
                    elif top_dark and not bottom_dark: line += "▄"
                    else: line += " "
                lines.append(line)
            
            final_text = "Scan to Open\n\n" + "\n".join(lines)
            self.query_one("#qr-text", Static).update(final_text)
            
        except Exception as e:
            self.query_one("#qr-text", Static).update(f"QR Error\n{e}")
