# FinBot - AI-Powered Financial Investment Assistant

## 🚀 Overview
FinBot is an advanced AI-powered financial investment tool designed for both American and Brazilian markets. It leverages local, open-source language models through Ollama to provide personalized investment recommendations without relying on external cloud services.

## 🔑 Key Features
- **Dual Market Coverage**: Analyze and recommend investments in both US (NYSE, NASDAQ) and Brazilian (B3) markets
- **Diverse Investment Options**: Stocks, ETFs, bonds, and traditional savings in both markets
- **Personalized Recommendations**: Based on investment amount, timeline, and risk tolerance
- **Offline Capability**: Functions with locally cached data when internet access is unavailable
- **AI-Powered Analysis**: Utilizes Ollama with open-source language models for decision-making
- **Self-Sufficient**: Operates entirely on a local server without external dependencies
- **Command-Line Interface**: User-friendly CLI for investment planning and analysis

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Ollama installed and configured

### Setup
1. Clone this repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Configure Ollama settings in `config.yaml`

## 💻 Usage
Basic commands:

```bash
# Plan a long-term investment
python finbot.py invest --amount 1000 --market US --type stocks --goal 1000000 --years 30

# Analyze Brazilian bond options
python finbot.py analyze --market BR --type bonds

# Update market data
python finbot.py update-data
```

## 📊 Architecture
FinBot follows a modular architecture:
- **Data Module**: Fetches and stores market data
- **Analysis Module**: Processes data and generates insights
- **AI Module**: Integrates with Ollama for advanced analysis
- **CLI Module**: Handles user interaction

## 📝 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
