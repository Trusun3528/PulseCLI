"""
Cross-platform local package manager provider.
Checks for upgradable packages on the system.
"""

import subprocess
import shutil
import sys
import json
from typing import Dict, List, Any


def get_update_command(manager: str) -> List[str]:
    """Returns the interactive terminal command to perform a system update."""
    if manager in ["checkupdates", "pacman", "yay", "paru"]:
        # Prefer yay or paru if installed for Arch, otherwise pacman
        if shutil.which("yay"):
            return ["yay", "-Syu"]
        if shutil.which("paru"):
            return ["paru", "-Syu"]
        return ["sudo", "pacman", "-Syu"]
    elif manager in ["apt", "apt-get"]:
        # Use shell execution since we need &&
        return ["sudo apt update && sudo apt upgrade"]
    elif manager == "dnf":
        return ["sudo", "dnf", "upgrade"]
    elif manager == "zypper":
        return ["sudo", "zypper", "update"]
    elif manager == "brew":
        return ["brew", "upgrade"]
    elif manager == "winget":
        return ["winget", "upgrade", "--all"]
    return []

def get_upgradable_packages() -> Dict[str, Any]:
    """
    Detects the system's package manager and returns a list of upgradable packages.
    Returns:
        Dict: {"manager": str, "packages": List[Dict], "error": Optional[str]}
    """
    manager = None
    packages = []
    
    # Define detection order based on platform
    if sys.platform == "win32":
        managers = ["winget"]
    elif sys.platform == "darwin":
        managers = ["brew"]
    else:
        # Linux / Unix
        # We explicitly require checkupdates for Arch to avoid inaccurate pacman -Qu results.
        managers = ["checkupdates", "zypper", "dnf", "apt-get", "apt"]

    for m in managers:
        if shutil.which(m):
            manager = m
            break
            
    if not manager:
        # Fallback check for Arch linux without pacman-contrib
        if shutil.which("pacman"):
            return {"manager": "pacman", "packages": [], "error": "pacman-contrib is required! Please run: sudo pacman -S pacman-contrib"}
        return {"manager": "Unknown", "packages": [], "error": "No supported package manager found."}
        
    try:
        if manager == "apt" or manager == "apt-get":
            # apt list --upgradable
            # Output: bash/jammy-updates 5.1-6ubuntu1 amd64 [upgradable from: 5.1-6]
            result = subprocess.run(["apt", "list", "--upgradable"], capture_output=True, text=True, check=False)
            for line in result.stdout.splitlines():
                if not line or "/" not in line or "Listing..." in line:
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    name = parts[0].split("/")[0]
                    new_ver = parts[1]
                    old_ver = "Unknown"
                    if "upgradable from:" in line:
                        try:
                            old_ver = line.split("upgradable from:")[1].strip().strip("]")
                        except:
                            pass
                    packages.append({"name": name, "current": old_ver, "available": new_ver})
                    
        elif manager == "dnf":
            # dnf check-update
            # Output: bash.x86_64   5.2-1.fc37   updates
            result = subprocess.run(["dnf", "check-update"], capture_output=True, text=True, check=False)
            for line in result.stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                if "Last metadata expiration check" in line:
                    continue
                parts = line.split()
                if len(parts) >= 3 and not line.startswith("Obsoleting Packages"):
                    name = parts[0]
                    new_ver = parts[1]
                    packages.append({"name": name, "current": "Installed", "available": new_ver})
                    
        elif manager == "zypper":
            # zypper lu
            result = subprocess.run(["zypper", "lu"], capture_output=True, text=True, check=False)
            for line in result.stdout.splitlines():
                if "|" not in line or "Repository" in line or "--+--" in line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 5:
                    name = parts[2]
                    old_ver = parts[3]
                    new_ver = parts[4]
                    if name:
                        packages.append({"name": name, "current": old_ver, "available": new_ver})
                        
        elif manager == "checkupdates":
            result = subprocess.run(["checkupdates"], capture_output=True, text=True, check=False)
            for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 4 and parts[2] == "->":
                    packages.append({"name": parts[0], "current": parts[1], "available": parts[3]})
                    
        elif manager == "brew":
            # brew outdated --json
            result = subprocess.run(["brew", "outdated", "--json"], capture_output=True, text=True, check=False)
            try:
                data = json.loads(result.stdout)
                for item in data.get("formulae", []):
                    packages.append({
                        "name": item.get("name", ""),
                        "current": item.get("installed_versions", [""])[0] if item.get("installed_versions") else "",
                        "available": item.get("current_version", "")
                    })
                for item in data.get("casks", []):
                    packages.append({
                        "name": item.get("name", ""),
                        "current": item.get("installed_versions", [""])[0] if item.get("installed_versions") else "",
                        "available": item.get("current_version", "")
                    })
            except json.JSONDecodeError:
                pass
                
        elif manager == "winget":
            # winget upgrade
            result = subprocess.run(["winget", "upgrade"], capture_output=True, text=True, check=False)
            lines = result.stdout.splitlines()
            if len(lines) > 2:
                for i, line in enumerate(lines):
                    if line.startswith("Name") and "Id" in line and "Version" in line and "Available" in line:
                        start_idx = i + 2
                        for item_line in lines[start_idx:]:
                            if not item_line.strip():
                                break
                            import re
                            parts = re.split(r'\s{2,}', item_line.strip())
                            if len(parts) >= 4:
                                packages.append({"name": parts[0], "current": parts[2], "available": parts[3]})
                        break
                        
        return {"manager": manager, "packages": packages, "error": None}
    except Exception as e:
        return {"manager": manager, "packages": [], "error": str(e)}
