"""
System information widget for Pulse — live CPU, RAM, disk, and network stats.
"""

from typing import Any, Dict, Optional

from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.text import Text
from textual.binding import Binding
from textual.widgets import Static
from textual import work

from providers.sysinfo import bar_color, get_system_info, make_bar, _fmt_bytes


class SysInfoWidget(Static):
    """Live system resource monitor."""

    BINDINGS = [
        Binding("r", "refresh", "Refresh"),
    ]

    DEFAULT_CSS = """
    SysInfoWidget {
        height: 1fr;
        width: 1fr;
    }
    """

    def on_mount(self) -> None:
        self.load_data()
        self.set_interval(3.0, self.load_data)

    @work(exclusive=True)
    async def load_data(self) -> None:
        import asyncio
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, get_system_info)
        self.update(self._build_content(data))

    def _build_content(self, d: Dict[str, Any]):
        sections = [
            self._cpu_section(d["cpu"]),
            Text(""),
            self._mem_section(d["memory"], d["swap"]),
            Text(""),
            self._disk_section(d["disk"]),
            Text(""),
            self._net_section(d["network"]),
        ]
        if d.get("battery"):
            sections += [Text(""), self._battery_section(d["battery"])]
        sections += [Text(""), self._platform_section(d["platform"])]

        return Panel(
            Group(*sections),
            title="[bold #06b6d4]🖥  System Monitor[/]",
            border_style="#7c3aed",
            padding=(1, 2),
        )

    def _cpu_section(self, cpu: Dict) -> Group:
        header = Text()
        header.append("── CPU ", style="#7c3aed bold")
        header.append(f"{cpu['logical_cores']} cores", style="#94a3b8")
        if cpu["freq_mhz"]:
            header.append(f" @ {cpu['freq_mhz']} MHz", style="#64748b")

        overall = self._bar_line("Overall", cpu["percent"])

        core_lines = []
        for i, pct in enumerate(cpu["per_core"] or []):
            core_lines.append(self._bar_line(f"Core {i}", pct, width=12))

        # Arrange cores in 2 columns
        if core_lines:
            half = (len(core_lines) + 1) // 2
            col_a = Group(*core_lines[:half])
            col_b = Group(*core_lines[half:])
            cores_display = Columns([col_a, col_b])
            return Group(header, overall, cores_display)
        return Group(header, overall)

    def _mem_section(self, mem: Dict, swap: Dict) -> Group:
        header = Text("── Memory", style="#06b6d4 bold")
        ram_bar = self._bar_line(
            "RAM",
            mem["percent"],
            suffix=f"{_fmt_bytes(mem['used'])} / {_fmt_bytes(mem['total'])}",
        )
        swap_bar = self._bar_line(
            "Swap",
            swap["percent"],
            suffix=f"{_fmt_bytes(swap['used'])} / {_fmt_bytes(swap['total'])}",
        ) if swap["total"] > 0 else Text("")
        return Group(header, ram_bar, swap_bar)

    def _disk_section(self, disk: Dict) -> Group:
        header = Text("── Disk  /", style="#10b981 bold")
        bar = self._bar_line(
            "Used",
            disk["percent"],
            suffix=f"{_fmt_bytes(disk['used'])} / {_fmt_bytes(disk['total'])}  ({_fmt_bytes(disk['free'])} free)",
        )
        return Group(header, bar)

    def _net_section(self, net: Dict) -> Group:
        header = Text("── Network", style="#f59e0b bold")
        t = Text()
        t.append(f"  ↑ Sent:     ", style="#94a3b8")
        t.append(f"{_fmt_bytes(net['bytes_sent'])}", style="#22c55e")
        t.append(f"    ↓ Received: ", style="#94a3b8")
        t.append(f"{_fmt_bytes(net['bytes_recv'])}", style="#60a5fa")
        return Group(header, t)

    def _battery_section(self, bat: Dict) -> Group:
        header = Text("── Battery", style="#fbbf24 bold")
        pct = bat["percent"]
        plugged = bat.get("plugged", False)
        plug_icon = "🔌" if plugged else "🔋"
        bar = self._bar_line(
            f"{plug_icon} Charge",
            pct,
            suffix=f"{'Charging' if plugged else 'On battery'}",
        )
        return Group(header, bar)

    def _platform_section(self, plat: Dict) -> Group:
        t = Text()
        t.append("── System  ", style="#64748b bold")
        t.append(f"{plat['system']} {plat['release']}  ", style="#94a3b8")
        t.append(f"Host: {plat['node']}  ", style="#64748b")
        t.append(f"Python {plat['python']}", style="#64748b")
        return Group(t)

    def _bar_line(
        self,
        label: str,
        percent: float,
        width: int = 24,
        suffix: str = "",
    ) -> Text:
        color = bar_color(percent)
        bar = make_bar(percent, width)
        t = Text()
        t.append(f"  {label:<12}", style="#94a3b8")
        t.append(f"[{bar}]", style=color)
        t.append(f"  {percent:5.1f}%", style=f"bold {color}")
        if suffix:
            t.append(f"  {suffix}", style="#64748b")
        return t

    def action_refresh(self) -> None:
        self.load_data()
