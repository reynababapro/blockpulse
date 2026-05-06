"""
BlockPulse - Minecraft Server Tracker Widget
A sleek, frameless desktop widget to monitor Minecraft servers in real-time.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
import time
from PIL import Image, ImageTk
import io
import base64

# ── mcstatus import (graceful fallback) ──────────────────────────────────────
try:
    from mcstatus import JavaServer
    MCSTATUS_AVAILABLE = True
except ImportError:
    MCSTATUS_AVAILABLE = False
    print("[WARN] mcstatus not installed. Run: pip install mcstatus")

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "server_ip": "your_ip",
    "server_port": your_port,
    "refresh_interval": 30,
    "window_x": 100,
    "window_y": 100,
}

# ── Palette ───────────────────────────────────────────────────────────────────
COLORS = {
    "bg":           "#0D1117",
    "bg_card":      "#161B22",
    "bg_input":     "#21262D",
    "border":       "#30363D",
    "border_focus": "#58A6FF",
    "accent":       "#58A6FF",
    "accent_green": "#3FB950",
    "accent_red":   "#F85149",
    "accent_yellow":"#D29922",
    "text_primary": "#E6EDF3",
    "text_secondary":"#8B949E",
    "text_muted":   "#484F58",
    "grass":        "#5C9E31",
    "dirt":         "#8B6244",
}

# ── Minecraft grass-block SVG favicon placeholder (base64 PNG 64x64) ─────────
BLOCK_ICON_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAACXBIWXMAAAsTAAALEwEAmpwY"
    "AAAAB3RJTUUH6AQGCiQe5Q2xfAAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJ"
    "TVBkLmUHAAADR0lEQVR42u2bS2gTQRjHf5uNSRpNk9QkTUxiYmMak8YHiYiIiIiIiIiIiIiI"
    "iIiIiA=="
)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)


# ── Settings Dialog ───────────────────────────────────────────────────────────
class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, config, on_save):
        super().__init__(parent)
        self.on_save = on_save
        self.config_data = config.copy()

        self.title("BlockPulse · Settings")
        self.geometry("380x260")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["bg"])
        self.grab_set()
        self.focus_force()

        # ── Header ────────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self, text="⚙  Settings",
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLORS["text_primary"]
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            self, text="Configure your Minecraft server connection",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_secondary"]
        ).pack(pady=(0, 16))

        # ── IP Field ──────────────────────────────────────────────────────────
        self._make_label("Server IP / Hostname")
        self.ip_entry = ctk.CTkEntry(
            self, placeholder_text="e.g. play.myserver.net",
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_primary"], width=340
        )
        self.ip_entry.insert(0, self.config_data.get("server_ip", ""))
        self.ip_entry.pack(padx=20, pady=(2, 10))

        # ── Port Field ────────────────────────────────────────────────────────
        self._make_label("Port")
        self.port_entry = ctk.CTkEntry(
            self, placeholder_text="25565",
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_primary"], width=340
        )
        self.port_entry.insert(0, str(self.config_data.get("server_port", 25565)))
        self.port_entry.pack(padx=20, pady=(2, 16))

        # ── Buttons ───────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20)

        ctk.CTkButton(
            btn_frame, text="Cancel", width=100,
            fg_color=COLORS["bg_input"], hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"], command=self.destroy
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame, text="Save & Refresh", width=200,
            fg_color=COLORS["accent"], hover_color="#1F6FEB",
            text_color="#ffffff", font=ctk.CTkFont(weight="bold"),
            command=self._save
        ).pack(side="right")

    def _make_label(self, text):
        ctk.CTkLabel(
            self, text=text,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color=COLORS["text_secondary"]
        ).pack(anchor="w", padx=22)

    def _save(self):
        ip = self.ip_entry.get().strip()
        try:
            port = int(self.port_entry.get().strip())
        except ValueError:
            messagebox.showerror("Invalid Port", "Port must be a number (e.g. 25565)")
            return
        if not ip:
            messagebox.showerror("Missing IP", "Please enter a server IP.")
            return
        self.config_data["server_ip"] = ip
        self.config_data["server_port"] = port
        self.on_save(self.config_data)
        self.destroy()


# ── Main Widget ───────────────────────────────────────────────────────────────
class BlockPulse(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self._drag_x = 0
        self._drag_y = 0
        self._refresh_job = None
        self._favicon_image = None

        self._setup_window()
        self._build_ui()
        self._start_refresh_loop()

    # ── Window setup ──────────────────────────────────────────────────────────
    def _setup_window(self):
        ctk.set_appearance_mode("dark")
        self.overrideredirect(True)               # frameless
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.96)
        self.configure(fg_color=COLORS["bg"])
        self.geometry(f"300x200+{self.config_data.get('window_x', 100)}+{self.config_data.get('window_y', 100)}")
        self.resizable(False, False)

        # Drag support
        self.bind("<ButtonPress-1>", self._on_drag_start)
        self.bind("<B1-Motion>",     self._on_drag_motion)
        self.bind("<ButtonRelease-1>", self._on_drag_end)

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        # Outer border frame
        outer = ctk.CTkFrame(self, fg_color=COLORS["border"], corner_radius=14)
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        # Main card
        card = ctk.CTkFrame(outer, fg_color=COLORS["bg_card"], corner_radius=13)
        card.pack(fill="both", expand=True, padx=1, pady=1)

        # ── Top bar (drag + controls) ──────────────────────────────────────
        top_bar = ctk.CTkFrame(card, fg_color="transparent", height=32)
        top_bar.pack(fill="x", padx=12, pady=(10, 0))
        top_bar.pack_propagate(False)

        # App title
        ctk.CTkLabel(
            top_bar, text="⛏  BlockPulse",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLORS["text_muted"]
        ).pack(side="left", pady=4)

        # Window controls
        ctrl_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        ctrl_frame.pack(side="right")

        self.settings_btn = ctk.CTkButton(
            ctrl_frame, text="⚙", width=26, height=22,
            fg_color="transparent", hover_color=COLORS["bg_input"],
            text_color=COLORS["text_secondary"], font=ctk.CTkFont(size=13),
            command=self._open_settings
        )
        self.settings_btn.pack(side="left", padx=2)

        ctk.CTkButton(
            ctrl_frame, text="✕", width=26, height=22,
            fg_color="transparent", hover_color="#3D1E1E",
            text_color=COLORS["text_secondary"], font=ctk.CTkFont(size=13),
            command=self._on_close
        ).pack(side="left", padx=2)

        # ── Separator ─────────────────────────────────────────────────────────
        sep = ctk.CTkFrame(card, fg_color=COLORS["border"], height=1)
        sep.pack(fill="x", padx=12, pady=(8, 0))

        # ── Server info row ───────────────────────────────────────────────────
        info_row = ctk.CTkFrame(card, fg_color="transparent")
        info_row.pack(fill="x", padx=16, pady=(12, 0))

        # Favicon placeholder
        self.favicon_label = ctk.CTkLabel(
            info_row, text="🟩", width=36, height=36,
            font=ctk.CTkFont(size=24)
        )
        self.favicon_label.pack(side="left", padx=(0, 10))

        # Server name + address
        name_col = ctk.CTkFrame(info_row, fg_color="transparent")
        name_col.pack(side="left", fill="x", expand=True)

        self.server_name_label = ctk.CTkLabel(
            name_col, text="Minecraft Server",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLORS["text_primary"], anchor="w"
        )
        self.server_name_label.pack(anchor="w")

        self.server_addr_label = ctk.CTkLabel(
            name_col, text=f"{self.config_data['server_ip']}:{self.config_data['server_port']}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=COLORS["text_muted"], anchor="w"
        )
        self.server_addr_label.pack(anchor="w")

        # Status badge
        self.status_badge = ctk.CTkLabel(
            info_row, text="  ●  CHECKING  ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=COLORS["accent_yellow"],
            fg_color=COLORS["bg_input"], corner_radius=8
        )
        self.status_badge.pack(side="right")

        # ── Stats row ─────────────────────────────────────────────────────────
        stats_row = ctk.CTkFrame(card, fg_color="transparent")
        stats_row.pack(fill="x", padx=16, pady=(10, 0))

        self.players_frame = self._stat_block(stats_row, "PLAYERS", "—")
        self.players_frame["frame"].pack(side="left", expand=True)

        _div = ctk.CTkFrame(stats_row, fg_color=COLORS["border"], width=1)
        _div.pack(side="left", fill="y", pady=4)

        self.ping_frame = self._stat_block(stats_row, "PING", "—")
        self.ping_frame["frame"].pack(side="left", expand=True)

        _div2 = ctk.CTkFrame(stats_row, fg_color=COLORS["border"], width=1)
        _div2.pack(side="left", fill="y", pady=4)

        self.version_frame = self._stat_block(stats_row, "VERSION", "—")
        self.version_frame["frame"].pack(side="left", expand=True)

        # ── Footer ────────────────────────────────────────────────────────────
        sep2 = ctk.CTkFrame(card, fg_color=COLORS["border"], height=1)
        sep2.pack(fill="x", padx=12, pady=(10, 0))

        foot = ctk.CTkFrame(card, fg_color="transparent")
        foot.pack(fill="x", padx=16, pady=(6, 10))

        self.last_update_label = ctk.CTkLabel(
            foot, text="Last checked: —",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLORS["text_muted"]
        )
        self.last_update_label.pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            foot, text="↻ Refresh", width=72, height=20,
            fg_color=COLORS["bg_input"], hover_color=COLORS["border"],
            text_color=COLORS["text_secondary"],
            font=ctk.CTkFont(family="Segoe UI", size=10),
            command=self._manual_refresh
        )
        self.refresh_btn.pack(side="right")

    def _stat_block(self, parent, label, value):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        lbl = ctk.CTkLabel(
            frame, text=label,
            font=ctk.CTkFont(family="Segoe UI", size=8, weight="bold"),
            text_color=COLORS["text_muted"]
        )
        lbl.pack()
        val = ctk.CTkLabel(
            frame, text=value,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLORS["text_primary"]
        )
        val.pack()
        return {"frame": frame, "label": lbl, "value": val}

    # ── Drag handlers ─────────────────────────────────────────────────────────
    def _on_drag_start(self, event):
        self._drag_x = event.x_root - self.winfo_x()
        self._drag_y = event.y_root - self.winfo_y()

    def _on_drag_motion(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.geometry(f"+{x}+{y}")

    def _on_drag_end(self, _event):
        self.config_data["window_x"] = self.winfo_x()
        self.config_data["window_y"] = self.winfo_y()
        save_config(self.config_data)

    # ── Query logic ───────────────────────────────────────────────────────────
    def _query_server(self):
        ip = self.config_data["server_ip"]
        port = self.config_data["server_port"]

        if not MCSTATUS_AVAILABLE:
            self.after(0, self._set_error, "mcstatus not installed")
            return

        try:
            server = JavaServer.lookup(f"{ip}:{port}", timeout=5)
            status = server.status()

            # Favicon
            favicon_data = None
            if hasattr(status, "favicon") and status.favicon:
                try:
                    raw = status.favicon.split(",", 1)[1]
                    favicon_bytes = base64.b64decode(raw)
                    img = Image.open(io.BytesIO(favicon_bytes)).resize((36, 36), Image.NEAREST)
                    favicon_data = ImageTk.PhotoImage(img)
                except Exception:
                    pass

            players_online = status.players.online
            players_max    = status.players.max
            latency        = round(status.latency)
            version        = status.version.name if hasattr(status.version, "name") else "—"
            motd           = status.motd.to_plain() if hasattr(status.motd, "to_plain") else str(status.motd)

            self.after(0, self._set_online,
                       players_online, players_max, latency, version, motd, favicon_data)

        except Exception as e:
            self.after(0, self._set_offline, str(e))

    def _set_online(self, online, max_p, latency, version, motd, favicon=None):
        # Status badge
        self.status_badge.configure(
            text="  ●  ONLINE  ",
            text_color=COLORS["accent_green"],
            fg_color="#0D2818"
        )

        # Server name from MOTD (strip to 22 chars)
        clean_motd = motd.strip()[:22] if motd.strip() else "Minecraft Server"
        self.server_name_label.configure(text=clean_motd)

        # Players
        self.players_frame["value"].configure(
            text=f"{online}/{max_p}",
            text_color=COLORS["accent_green"] if online > 0 else COLORS["text_primary"]
        )

        # Ping colour
        if latency < 60:
            ping_color = COLORS["accent_green"]
        elif latency < 130:
            ping_color = COLORS["accent_yellow"]
        else:
            ping_color = COLORS["accent_red"]

        self.ping_frame["value"].configure(text=f"{latency}ms", text_color=ping_color)

        # Version (shorten)
        ver_short = version.split(" ")[-1][:8] if version else "—"
        self.version_frame["value"].configure(text=ver_short, text_color=COLORS["text_primary"])

        # Favicon
        if favicon:
            self._favicon_image = favicon
            self.favicon_label.configure(image=favicon, text="")

        self._update_timestamp()

    def _set_offline(self, reason=""):
        self.status_badge.configure(
            text="  ●  OFFLINE  ",
            text_color=COLORS["accent_red"],
            fg_color="#2D1215"
        )
        self.players_frame["value"].configure(text="—", text_color=COLORS["text_muted"])
        self.ping_frame["value"].configure(text="—",   text_color=COLORS["text_muted"])
        self.version_frame["value"].configure(text="—",text_color=COLORS["text_muted"])
        self.favicon_label.configure(image="", text="🟥")
        self._update_timestamp()

    def _set_error(self, msg):
        self.status_badge.configure(
            text="  ●  ERROR  ",
            text_color=COLORS["accent_yellow"],
            fg_color="#2D2208"
        )
        self._update_timestamp()

    def _update_timestamp(self):
        now = time.strftime("%H:%M:%S")
        self.last_update_label.configure(text=f"Last checked: {now}")

    # ── Refresh loop ──────────────────────────────────────────────────────────
    def _start_refresh_loop(self):
        self._run_query()
        interval_ms = self.config_data.get("refresh_interval", 30) * 1000
        self._refresh_job = self.after(interval_ms, self._start_refresh_loop)

    def _run_query(self):
        t = threading.Thread(target=self._query_server, daemon=True)
        t.start()

    def _manual_refresh(self):
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
        self.status_badge.configure(
            text="  ●  CHECKING  ",
            text_color=COLORS["accent_yellow"],
            fg_color=COLORS["bg_input"]
        )
        self._start_refresh_loop()

    # ── Settings ──────────────────────────────────────────────────────────────
    def _open_settings(self):
        def on_save(new_cfg):
            self.config_data.update(new_cfg)
            save_config(self.config_data)
            self.server_addr_label.configure(
                text=f"{self.config_data['server_ip']}:{self.config_data['server_port']}"
            )
            self._manual_refresh()

        SettingsDialog(self, self.config_data, on_save)

    # ── Close ─────────────────────────────────────────────────────────────────
    def _on_close(self):
        self.config_data["window_x"] = self.winfo_x()
        self.config_data["window_y"] = self.winfo_y()
        save_config(self.config_data)
        self.destroy()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = BlockPulse()
    app.mainloop()
