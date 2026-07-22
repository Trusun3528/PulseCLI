# Pulse 🚀

**Pulse** is a beautiful, interactive, and highly customizable terminal dashboard built with Python and [Textual](https://textual.textualize.io/). Keep your finger on the pulse of the digital world—all from the comfort of your terminal.

## 🌟 Features

- **🌤️ Weather**: Current conditions and 5-day forecast (OpenWeatherMap).
- **📰 News**: Top headlines with category filters (NewsAPI).
- **▶️ YouTube**: Trending videos filtered by region (YouTube Data API v3).
- **🔥 Hacker News**: Browse Top, New, Best, Ask, and Show stories seamlessly.
- **🐙 GitHub**: Discover trending repositories by language and time range.
- **📈 Stocks**: Live stock ticker tracking powered by Yahoo Finance.
- **🖥️ System**: Real-time monitoring for CPU, Memory, Disk, and Network usage.
- **🪙 Crypto**: Live cryptocurrency tracking powered by Yahoo Finance.
- **🤖 AI Models**: Discover top trending models via Hugging Face.
- **📅 Calendar**: Track upcoming events via ICS links or world public holidays.
- **🐙 Pull Requests**: Monitor your open GitHub Pull Requests.
- **📂 File Explorer**: Browse and open local files directly from the dashboard.

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Trusun3528/PulseCLI.git
   cd pulse
   ```

2. **Set up a virtual environment** (optional but recommended):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🚀 Usage

Launch the dashboard by running:

```bash
python main.py
```

You can also start Pulse directly on a specific tab:
```bash
python main.py --tab news
```

### ⌨️ Key Bindings
- `1-7`, `8`, `9`, `0`, `-`, `=`: Switch between tabs (Weather, News, YouTube, Hacker News, GitHub, Stocks, System, Crypto, AI Models, Calendar, PRs, Files)
- `S`: Open Settings
- `R` or `Ctrl+R`: Refresh current tab
- `Enter`: Open selected article/link in your browser
- `Q`: Quit the application

## ⚙️ Configuration & API Keys

Many of Pulse's widgets require API keys to function. Pulse includes a built-in UI for managing your configuration!

1. Press `S` inside the app to open the **Settings** screen.
2. Enter your API keys and customize your region, stock tickers, and refresh intervals.
3. Press `Ctrl+S` to save.

Your configuration is saved securely to `~/.config/pulse/config.toml`.

### Required APIs:
- **Weather**: [OpenWeatherMap API](https://openweathermap.org/api) (Free tier)
- **News**: [NewsAPI](https://newsapi.org/) (Free tier)
- **YouTube**: [YouTube Data API v3](https://console.cloud.google.com/) (Free tier)

### Optional APIs:
- **GitHub PRs**: Optional Personal Access Token for higher rate limits.

*(Hacker News, GitHub, Stocks, Crypto, AI Models, Calendar, Files, and System Monitor work out of the box!)*

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

## 📝 License

This project is open-source and available under the MIT License.
