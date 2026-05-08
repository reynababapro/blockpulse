# ⛏ BlockPulse

> A sleek, frameless Minecraft server monitor widget for your Windows desktop.

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?style=flat-square&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=flat-square&logo=windows)

---

## ✨ Features

- **Always-on-top, frameless widget** — stays visible without cluttering your taskbar
- **Real-time server status** — Online / Offline badge with color coding
- **Live stats** — Player count, ping latency (with color grading), server version
- **Favicon support** — Automatically fetches and displays the server's icon
- **Persistent settings** — Server IP/port saved to `config.json`
- **Drag to reposition** — Window position is remembered between sessions
- **Auto-refresh every 30 seconds** — Or hit the manual ↻ button

---

## 📸 Preview

```
┌──────────────────────────────────┐
│ ⛏ BlockPulse          ⚙  ✕     │
│──────────────────────────────────│
│ 🟩  Rey Network  ● ONLINE   │
│     reynw.mcsh.io            │
│──────────────────────────────────│
│   PLAYERS   │   PING   │ VERSION │
│   4201/9000 │   48ms   │  1.21.1 │
│──────────────────────────────────│
│ Last checked: 14:32:07  ↻ Refresh│
└──────────────────────────────────┘
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/reynababapro/blockpulse.git
cd blockpulse
```

### 2. Install dependencies

```bash
pip install customtkinter mcstatus Pillow
```

> **Python 3.9 or higher** is required.

| Package | Purpose |
|---|---|
| `customtkinter` | Modern dark-themed UI framework |
| `mcstatus` | Minecraft server query (Java Edition) |
| `Pillow` | Favicon image processing |

### 3. Run

```bash
python blockpulse.py
```

---

## ⚙️ Configuration

Click the **⚙** gear icon on the widget to open Settings. Enter your server's IP and port, then click **Save & Refresh**.

Settings are stored in `config.json` next to the script:

```json
{
  "server_ip": "hypixel.net",
  "server_port": 25565,
  "refresh_interval": 30,
  "window_x": 100,
  "window_y": 100
}
```

You can also edit this file directly.

---

## 🖥️ Run on Startup (Windows)

To launch BlockPulse automatically when Windows starts:

1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `blockpulse.py` (or a `.bat` file) in that folder

**Example `start_blockpulse.bat`:**
```bat
@echo off
pythonw "C:\path\to\blockpulse.py"
```

Using `pythonw` instead of `python` prevents a console window from appearing.

---

## 📋 Requirements

- Windows 10 / 11
- Python 3.9+
- Target server must support the **Java Edition** status protocol

> **Bedrock Edition** servers are not currently supported.

---

## 🗺️ Roadmap

- [ ] Bedrock Edition support (`mcstatus` `BedrockServer`)
- [ ] Multiple server tabs / switching
- [ ] Player list popup on click
- [ ] Sound notification on server going offline
- [ ] System tray icon integration

---

## 🤝 Contributing

Pull requests are welcome! Please open an issue first to discuss major changes.

---

## 📄 License

[MIT](LICENSE) — free to use, modify, and distribute.

---

*Built with ❤️ and `customtkinter`*
