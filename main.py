#!/usr/bin/env python3
"""
Pulse — A beautiful, interactive terminal dashboard.
Weather, News, YouTube, Hacker News, GitHub Trending, Stocks & System Monitor.

Usage:
    python main.py              # Launch dashboard
    python main.py --tab news   # Start on a specific tab
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="pulse",
        description="Pulse — your personal terminal dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tabs:  weather | news | youtube | hackernews | github | stocks | system

Key bindings (inside the app):
  1-7     Switch tabs
  S       Open Settings
  R       Refresh current tab
  Q       Quit

Configure API keys by pressing S inside the app, or edit:
  ~/.config/pulse/config.toml
        """,
    )
    parser.add_argument(
        "--tab",
        choices=["weather", "news", "youtube", "hackernews", "github", "stocks", "system"],
        default="weather",
        help="Start on this tab (default: weather)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="Pulse 1.0.0",
    )

    args = parser.parse_args()

    try:
        from app import PulseApp
        from textual.widgets import TabbedContent
    except ImportError as e:
        print(f"Error: Missing dependency — {e}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)

    app = PulseApp()

    # Override initial tab if specified
    if args.tab != "weather":
        original_compose = app.compose

        def patched_compose():
            result = original_compose()
            return result

        # We'll switch tab on mount instead
        original_mount = app.on_mount

        async def patched_mount():
            await original_mount() if original_mount else None
            try:
                app.query_one(TabbedContent).active = args.tab
            except Exception:
                pass

        app.on_mount = patched_mount

    app.run()


if __name__ == "__main__":
    main()
