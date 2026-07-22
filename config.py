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
    "general": {
        "refresh_interval": 300,  # seconds
        "theme": "dark",
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
}


def load_config() -> Dict[str, Any]:
    """Load configuration from file, creating defaults if needed."""
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
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        toml.dump(config, f)


def _deep_copy(d: Dict) -> Dict:
    """Deep copy a dict."""
    import copy
    return copy.deepcopy(d)


def _deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge override into base dict, returning merged result."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
