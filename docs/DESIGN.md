# AdminHunter Elite Pro v4.0 - Enhanced Architecture

## 1. Modular Structure
- `main.py`: Entry point, argument parsing, and UI initialization.
- `core/scanner.py`: Multi-threaded scanning engine with advanced detection logic.
- `core/recon.py`: Initial server fingerprinting and technology detection.
- `utils/waf.py`: Sophisticated header and User-Agent rotation for WAF evasion.
- `utils/ui.py`: Professional terminal interface components.
- `utils/logger.py`: Result logging and export (JSON/TXT).

## 2. Key Enhancements
### A. Advanced Detection Logic
- **Keyword Matching**: Search for login-related terms in response body.
- **Form Detection**: Identify password input fields and login forms.
- **Title Extraction**: Capture the `<title>` tag for quick validation.
- **Soft 404 Detection**: Compare response content length to detect false positives.

### B. Stealth & WAF Evasion
- **Header Rotation**: Inject `X-Forwarded-For`, `X-Real-IP`, etc., with randomized IPs.
- **User-Agent Rotation**: Use a massive, up-to-date list of browsers.
- **Smart Delays**: Optional random sleep between requests.

### C. Technology-Aware Scanning
- **Fingerprinting**: Detect WordPress, Laravel, Drupal, etc.
- **Dynamic Paths**: Prioritize paths based on detected technologies.
- **Extension Handling**: Replace `{ext}` with common web extensions (.php, .asp, .html).

### D. Usability
- **Argument Parsing**: Support for `--target`, `--threads`, `--timeout`, `--proxy`, `--output`.
- **Exporting**: Save results to JSON and plain text.
- **Progress Bar**: Real-time scan progress with detailed stats.

## 3. Data Management
- Optimized wordlists categorized by technology.
- Support for custom wordlists via CLI.
