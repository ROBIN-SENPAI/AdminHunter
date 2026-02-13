<p align="center">
  <img src="AdminHunter.png" width="650">
</p>

<h1 align="center">🎯 AdminHunter Elite Pro v4.0 (Enhanced)</h1>

**AdminHunter Elite Pro** is a professional-grade reconnaissance framework...


**AdminHunter Elite Pro** is a professional-grade reconnaissance framework designed for identifying administrative panels and sensitive file exposures. This enhanced version features modular architecture, intelligent detection logic, and advanced WAF evasion techniques.

## ⚡ Elite Features

- **Intelligent Detection Engine**: Goes beyond status codes by analyzing page titles, content keywords, and form inputs to eliminate false positives.
- **Advanced WAF Evasion**: Rotates a massive list of User-Agents and injects sophisticated HTTP headers (e.g., `X-Forwarded-For`, `X-Real-IP`) to bypass security filters.
- **Reconnaissance Module**: Automatically fingerprints server technologies (WordPress, Laravel, etc.) and gathers infrastructure details.
- **Technology-Aware Wordlists**: Dynamically handles path extensions and prioritizes sensitive files based on the detected environment.
- **High-Performance Multi-Threading**: Optimized for speed with a robust queuing system and thread-safe statistics.
- **Professional CLI**: A clean, modular interface with detailed progress tracking and result reporting.

## 🚀 Getting Started

### Installation
1. Ensure you have Python 3.8+ installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Usage
Run the tool with the default settings:
```bash
python3 main.py
```

Or use advanced command-line arguments:
```bash
python3 main.py --target example.com --threads 50 --output results.json
```

### Arguments
- `-t, --target`: The target URL to scan.
- `-w, --wordlist`: Path to a custom wordlist file.
- `--threads`: Number of concurrent threads (default: 30).
- `--timeout`: Request timeout in seconds (default: 10).
- `--no-stop`: Continue scanning even after finding an admin panel.
- `-o, --output`: Save the discovery results to a JSON file.

## 🛠 Project Structure
- `main.py`: Entry point and CLI logic.
- `core/`: Core scanning and reconnaissance engines.
- `utils/`: UI components, WAF evasion, and helper functions.
- `data/`: Comprehensive wordlists and configuration files.
- `docs/`: Technical documentation and design notes.

## 👨‍💻 Developer
- **Name**: ROBIN ABU IBRAHIM
- **Telegram**: [xFFBI](https://t.me/xFFBI)

---
*Disclaimer: This tool is strictly for educational purposes and authorized security assessments. Unauthorized use against systems without prior consent is illegal.*


