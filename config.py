"""
Configuration management for Pulse CLI dashboard.
Config is stored at ~/.config/pulse/config.toml
"""

import toml
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".config" / "pulse"
CONFIG_FILE = CONFIG_DIR / "config.toml"

DEFAULT_CONFIG: Dict[str, Any] = {
    # General application settings
    "general": {
        "refresh_interval": 300,  # seconds
        "theme": "dark",
    },
    "tabs": {
        "weather": True,
        "news": True,
        "youtube": True,
        "hackernews": True,
        "github": True,
        "stocks": True,
        "system": True,
        "crypto": True,
        "aimodels": True,
        "calendar": True,
        "github_prs": True,
        "files": True,
        "qrgen": True,
        "packages": True,
        "ping": True,
        "rss": True,
    },
    "tv_mode": {
        "main_1": "news",
        "main_2": "youtube",
        "side_1": "calendar",
        "side_2": "system",
        "qr_spot": "qr",
    },
    "weather": {
        "api_key": "",
        "location": "New York",
        "units": "imperial",  # "imperial" (°F) or "metric" (°C)
    },
    "news": {
        "api_key": "",
        "country": "us",
        "category": "general",
        "page_size": 25,
    },
    "youtube": {
        "api_key": "",
        "region_code": "US",
        "limit": 25,
    },
    "hackernews": {
        "type": "top",
        "limit": 30,
    },
    "github": {
        "language": "",
        "since": "daily",
    },
    "stocks": {
        "tickers": ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA", "AMZN", "META"],
        "refresh_interval": 60,
    },
    "crypto": {
        "tickers": ["BTC-USD", "ETH-USD", "SOL-USD", "DOGE-USD"],
        "refresh_interval": 60,
    },
    "calendar": {
        "ics_url": "",
    },
    "github_prs": {
        "username": "",
        "token": "",
    },
    "ping": {
        "targets": [
            {"name": "Google DNS", "host": "8.8.8.8"},
            {"name": "Cloudflare", "host": "1.1.1.1"},
            {"name": "Localhost", "host": "127.0.0.1"}
        ]
    },
    "rss": {
        "url": "https://news.ycombinator.com/rss",
        "title": "Hacker News RSS",
        "limit": 25
    }
}


def load_config() -> Dict[str, Any]:
    """
    Load configuration from the user's config file.
    
    If the file does not exist, it creates one with the default settings.
    If the file exists, it reads the user's settings and merges them with
    the defaults, ensuring any missing keys are populated.
    
    Returns:
        Dict[str, Any]: The fully populated configuration dictionary.
    """
    # Ensure the directory exists before trying to access or create the file
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return _deep_copy(DEFAULT_CONFIG)

    try:
        with open(CONFIG_FILE, "r") as f:
            user_config = toml.load(f)
        return _deep_merge(_deep_copy(DEFAULT_CONFIG), user_config)
    except Exception:
        return _deep_copy(DEFAULT_CONFIG)


def save_config(config: Dict[str, Any]) -> None:
    """
    Save the provided configuration dictionary to the config file on disk.
    
    Args:
        config (Dict[str, Any]): The configuration to save, typically modified by the user.
    """
    # Create the directory if it's not already there
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Write the dictionary as TOML format to the file
    with open(CONFIG_FILE, "w") as f:
        toml.dump(config, f)


def _deep_copy(d: Dict) -> Dict:
    """Deep copy a dict."""
    import copy
    return copy.deepcopy(d)


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Recursively merge an override dictionary into a base dictionary.
    
    This ensures that nested dictionaries (like 'weather' or 'news' settings)
    are properly merged rather than entirely replaced if the user only provides
    a partial configuration.
    
    Args:
        base (Dict): The default configuration dict.
        override (Dict): The user's configuration dict.
        
    Returns:
        Dict: A new dictionary containing the merged result.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
