"""
YouTube Trending widget for Pulse.
Displays trending videos using the YouTube Data API.
"""

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import DataTable, Static, Button, Select, Label
from textual.widget import Widget
from textual.message import Message
from textual import work
import webbrowser

from config import load_config
from providers.youtube import fetch_trending_videos, _format_count

class YoutubeWidget(Widget):
    """YouTube Trending browser."""
    
    DEFAULT_CSS = """
    YoutubeWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    
    #youtube-toolbar {
        height: 3;
        width: 1fr;
        layout: horizontal;
        background: #1a1d2e;
        padding: 0 1;
        align: left middle;
    }
    
    #youtube-region {
        width: 20;
    }
    
    #youtube-table {
        height: 1fr;
    }
    
    #youtube-status {
        height: 1;
        background: #1a1d2e;
        color: #94a3b8;
        padding: 0 2;
        text-align: right;
    }
    """

    class OpenLink(Message):
        """Message emitted when a link should be opened."""
        def __init__(self, url: str) -> None:
            self.url = url
            super().__init__()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._videos = []
        
    def compose(self) -> ComposeResult:
        config = load_config()
        self._region = config.get("youtube", {}).get("region_code", "US")
        
        with Horizontal(id="youtube-toolbar"):
            yield Label("Region: ", classes="toolbar-label")
            region_options = [
                ("US", "US"), ("GB", "GB"), ("IN", "IN"), ("JP", "JP"), 
                ("CA", "CA"), ("AU", "AU"), ("DE", "DE"), ("FR", "FR"), 
                ("BR", "BR"), ("MX", "MX")
            ]
            # Ensure the configured region is in the options
            if self._region not in [opt[0] for opt in region_options]:
                region_options.append((self._region, self._region))
                
            yield Select(region_options, id="youtube-region", value=self._region)

        yield DataTable(id="youtube-table", cursor_type="row", zebra_stripes=True)
        yield Static("", id="youtube-status")

    def on_mount(self) -> None:
        table = self.query_one("#youtube-table", DataTable)
        table.add_columns("Title", "Channel", "Views", "Likes", "Published At")
        self.load_trending()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "youtube-region":
            self._region = str(event.value)
            self.load_trending()

    @work(exclusive=True, thread=False)
    async def load_trending(self) -> None:
        table = self.query_one("#youtube-table", DataTable)
        status = self.query_one("#youtube-status", Static)
        
        table.clear()
        table.loading = True
        status.update("Fetching trending videos...")
        
        config = load_config()
        yt_config = config.get("youtube", {})
        api_key = yt_config.get("api_key", "")
        limit = yt_config.get("limit", 25)
        
        if not api_key:
            table.loading = False
            status.update("⚠️ YouTube API Key Required")
            table.add_row(
                "🔑 YouTube requires an API key. Press S → open Settings → add API Key.",
                "", "", "", ""
            )
            return

        videos = await fetch_trending_videos(api_key, self._region, limit)
        table.loading = False
        
        if not videos:
            status.update("No videos found.")
            return
            
        if isinstance(videos, dict) and "error" in videos:
            error_msg = videos["error"]
            status.update(f"Error: {error_msg}")
            table.add_row(f"Error: {error_msg}", "", "", "", "")
            return
            
        if len(videos) > 0 and "error" in videos[0]:
            error_msg = videos[0]["error"]
            status.update(f"Error: {error_msg}")
            table.add_row(f"Error: {error_msg}", "", "", "", "")
            return

        self._videos = videos
        for vid in videos:
            table.add_row(
                vid.get("title", ""),
                vid.get("channel_title", ""),
                _format_count(vid.get("view_count", 0)),
                _format_count(vid.get("like_count", 0)),
                vid.get("published_at", "")[:10]  # Just the date part
            )
            
        status.update(f"Loaded {len(videos)} videos (Region: {self._region})")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        idx = event.cursor_row
        if 0 <= idx < len(self._videos):
            url = self._videos[idx].get("url")
            if url:
                self.post_message(self.OpenLink(url))
