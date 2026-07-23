"""
Ping monitor provider.
Pings a list of hosts to check their status and latency.
"""

import subprocess
import sys
import re
from typing import List, Dict, Any

def ping_host(host: str) -> Dict[str, Any]:
    """
    Pings a single host and returns its status and latency.
    """
    is_windows = sys.platform == "win32"
    
    # -c 1 for Linux/Mac, -n 1 for Windows
    # -W 2 (timeout 2s) for Linux/Mac, -w 2000 for Windows
    if is_windows:
        cmd = ["ping", "-n", "1", "-w", "2000", host]
    else:
        cmd = ["ping", "-c", "1", "-W", "2", host]
        
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = result.stdout
        
        # Determine status
        is_online = result.returncode == 0
        
        # Parse latency
        latency_str = "-"
        if is_online:
            if is_windows:
                # e.g., time=15ms
                match = re.search(r"time[=<](\d+)ms", output, re.IGNORECASE)
                if match:
                    latency_str = f"{match.group(1)}ms"
            else:
                # e.g., time=15.2 ms
                match = re.search(r"time=([\d.]+)\s*ms", output, re.IGNORECASE)
                if match:
                    latency_str = f"{match.group(1)}ms"
                    
        return {
            "status": "Online" if is_online else "Offline",
            "latency": latency_str
        }
    except Exception as e:
        return {
            "status": "Error",
            "latency": "-"
        }

def ping_targets(targets: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    Pings multiple targets.
    Note: For a large number of targets, this is synchronous and blocking.
    A threaded/async approach in the widget is recommended to prevent UI freezing.
    """
    results = []
    for t in targets:
        host = t.get("host", "")
        name = t.get("name", host)
        
        if not host:
            continue
            
        res = ping_host(host)
        results.append({
            "name": name,
            "host": host,
            "status": res["status"],
            "latency": res["latency"]
        })
        
    return results
