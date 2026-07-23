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
    """
    Main entry point for the Pulse CLI application.
    Parses command-line arguments and starts the Textual application.
    """
    # Set up the argument parser to handle command-line options
    parser = argparse.ArgumentParser(
        prog="pulse",
        description="Pulse — your personal terminal dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Tabs:  weather | news | youtube | hackernews | github | stocks | system | crypto | aimodels | calendar | github_prs | files

Key bindings (inside the app):
  1-7, 8, 9, 0, -, =  Switch tabs
  S                   Open Settings
  R       Refresh current tab
  Q       Quit

Configure API keys by pressing S inside the app, or edit:
  ~/.config/pulse/config.toml
        """,
    )
    
    # Allow the user to specify which tab opens first
    parser.add_argument(
        "--tab",
        choices=["weather", "news", "youtube", "hackernews", "github", "stocks", "system", "crypto", "aimodels", "calendar", "github_prs", "files"],
        default="weather",
        help="Start on this tab (default: weather)",
    )
    
    # Allow the user to check the current version of the app
    parser.add_argument(
        "--version",
        action="version",
        version="Pulse 1.0.0",
    )

    args = parser.parse_args()

    # Try importing the main app components; fail gracefully if dependencies are missing
    try:
        from app import PulseApp
        from textual.widgets import TabbedContent
    except ImportError as e:
        print(f"Error: Missing dependency — {e}")
        print("Run: pip install -r requirements.txt")
        sys.exit(1)

    # Initialize the textual application
    app = PulseApp()

    # Override initial tab if specified by the user via command-line
    if args.tab != "weather":
        original_compose = app.compose

        def patched_compose():
            # Call the original compose method to build the UI
            result = original_compose()
            return result

        # We'll switch tab on mount instead of during compose
        original_mount = app.on_mount

        async def patched_mount():
            # Run the original mount logic if it exists
            await original_mount() if original_mount else None
            try:
                # Find the main tabs container and set the active tab to the user's choice
                app.query_one(TabbedContent).active = args.tab
            except Exception:
                # Ignore errors if the tab cannot be switched
                pass

        # Apply the patched mount method to the app
        app.on_mount = patched_mount

    # Start the application loop
    app.run()


if __name__ == "__main__":
    # Execute the main function if this script is run directly
    main()
