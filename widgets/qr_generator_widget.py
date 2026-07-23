"""
QR Generator Widget for Pulse.
Allows users to create custom QR codes (Text, URL, WiFi, SMS).
"""

from typing import Iterable

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Input, Select, Static, Label

from widgets.qr_widget import QrWidget

class QrGeneratorWidget(Widget):
    """Interactive QR Code generator."""

    DEFAULT_CSS = """
    QrGeneratorWidget {
        height: 1fr;
        width: 1fr;
        layout: vertical;
    }
    #qrg-header {
        height: 3;
        background: #1a1d2e;
        color: #94a3b8;
        padding: 0 2;
        content-align: left middle;
    }
    #qrg-controls {
        height: auto;
        padding: 1 2;
        background: #0d0f14;
        border-bottom: tall #2d3057;
    }
    #qrg-format-row {
        height: 3;
        margin-bottom: 1;
    }
    .qrg-input-container {
        height: auto;
        display: none;
        layout: vertical;
    }
    .qrg-input-container.-active {
        display: block;
    }
    Input {
        width: 1fr;
        margin-bottom: 1;
    }
    #qrg-wifi-row {
        height: auto;
        layout: horizontal;
    }
    #qrg-wifi-row > * {
        width: 1fr;
        margin-right: 1;
    }
    #qrg-display-container {
        height: 1fr;
        width: 1fr;
        background: #000000;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("📱 QR Code Generator", id="qrg-header")
        
        with Container(id="qrg-controls"):
            with Horizontal(id="qrg-format-row"):
                yield Label("Format: ", classes="label", id="qrg-format-label")
                yield Select(
                    [("Text / URL", "text"), ("WiFi Network", "wifi"), ("SMS / Text Message", "sms")],
                    value="text",
                    id="qrg-format-select"
                )
            
            # Text/URL Inputs
            with Container(id="qrg-inputs-text", classes="qrg-input-container -active"):
                yield Input(placeholder="Enter Text or URL...", id="input-text")
                
            # WiFi Inputs
            with Container(id="qrg-inputs-wifi", classes="qrg-input-container"):
                with Horizontal(id="qrg-wifi-row"):
                    yield Input(placeholder="SSID (Network Name)", id="input-wifi-ssid")
                    yield Select(
                        [("WPA/WPA2/WPA3", "WPA"), ("WEP", "WEP"), ("No Password", "nopass")],
                        value="WPA",
                        id="input-wifi-type"
                    )
                yield Input(placeholder="Password", password=True, id="input-wifi-pass")
                
            # SMS Inputs
            with Container(id="qrg-inputs-sms", classes="qrg-input-container"):
                yield Input(placeholder="Phone Number", id="input-sms-phone")
                yield Input(placeholder="Message (optional)", id="input-sms-msg")

        with Container(id="qrg-display-container"):
            yield QrWidget(id="qrg-qr")

    def on_mount(self) -> None:
        self.update_qr()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "qrg-format-select":
            # Hide all
            for c in self.query(".qrg-input-container"):
                c.remove_class("-active")
            # Show active
            fmt = event.value
            active_container = self.query_one(f"#qrg-inputs-{fmt}")
            active_container.add_class("-active")
            
        self.update_qr()

    def on_input_changed(self, event: Input.Changed) -> None:
        self.update_qr()

    def update_qr(self) -> None:
        fmt_select = self.query_one("#qrg-format-select", Select)
        fmt = fmt_select.value
        
        data = ""
        
        if fmt == "text":
            data = self.query_one("#input-text", Input).value
        elif fmt == "wifi":
            ssid = self.query_one("#input-wifi-ssid", Input).value
            enc = self.query_one("#input-wifi-type", Select).value
            pwd = self.query_one("#input-wifi-pass", Input).value
            
            # Escape special chars per WIFI string spec
            ssid = ssid.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace('"', '\\"')
            pwd = pwd.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace('"', '\\"')
            
            if ssid:
                data = f"WIFI:T:{enc};S:{ssid};P:{pwd};;"
        elif fmt == "sms":
            phone = self.query_one("#input-sms-phone", Input).value
            msg = self.query_one("#input-sms-msg", Input).value
            if phone:
                data = f"smsto:{phone}:{msg}"
                
        qr_widget = self.query_one("#qrg-qr", QrWidget)
        if data:
            qr_widget.update_url(data)
        else:
            qr_widget.update_url("")
