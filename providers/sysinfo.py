"""
System information provider for Pulse.
Uses psutil — no API key required.
"""

import platform
from typing import Any, Dict, Optional

import psutil

# Unicode progress bar characters
BAR_FULL = "█"
BAR_EMPTY = "░"


def make_bar(percent: float, width: int = 20) -> str:
    """Create a Unicode progress bar string."""
    filled = int(width * min(percent, 100) / 100)
    empty = width - filled
    return BAR_FULL * filled + BAR_EMPTY * empty


def bar_color(percent: float) -> str:
    """Return a Rich color string based on percent value."""
    if percent >= 90:
        return "bright_red"
    if percent >= 70:
        return "bright_yellow"
    if percent >= 50:
        return "yellow"
    return "bright_green"


def _fmt_bytes(n: float) -> str:
    """Format bytes into human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def get_system_info() -> Dict[str, Any]:
    """Gather current system stats. Returns a nested dict."""
    # --- CPU ---
    cpu_pct = psutil.cpu_percent(interval=0.2)
    per_core = psutil.cpu_percent(interval=0.1, percpu=True)
    cpu_count_logical = psutil.cpu_count(logical=True)
    cpu_count_physical = psutil.cpu_count(logical=False)
    freq = psutil.cpu_freq()

    # --- Memory ---
    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    # --- Disk ---
    try:
        disk = psutil.disk_usage("/")
        disk_data = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent,
        }
    except Exception:
        disk_data = {"total": 0, "used": 0, "free": 0, "percent": 0}

    # --- Network ---
    net = psutil.net_io_counters()

    # --- Battery ---
    battery: Optional[Dict] = None
    try:
        bat = psutil.sensors_battery()
        if bat:
            battery = {
                "percent": bat.percent,
                "plugged": bat.power_plugged,
                "secs_left": bat.secsleft if bat.secsleft > 0 else None,
            }
    except Exception:
        pass

    # --- Platform ---
    uname = platform.uname()

    return {
        "cpu": {
            "percent": cpu_pct,
            "per_core": per_core or [],
            "logical_cores": cpu_count_logical,
            "physical_cores": cpu_count_physical,
            "freq_mhz": round(freq.current) if freq else 0,
            "freq_max_mhz": round(freq.max) if freq and freq.max else 0,
        },
        "memory": {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": mem.percent,
        },
        "swap": {
            "total": swap.total,
            "used": swap.used,
            "percent": swap.percent,
        },
        "disk": disk_data,
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
        },
        "battery": battery,
        "platform": {
            "system": uname.system,
            "node": uname.node,
            "release": uname.release,
            "machine": uname.machine,
            "python": platform.python_version(),
        },
    }
