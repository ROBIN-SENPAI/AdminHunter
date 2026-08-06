import os
import re
import sys
import ctypes
from datetime import datetime


class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'
    BG_GREEN = '\033[42m'
    BG_CYAN = '\033[46m'
    BG_YELLOW = '\033[43m'
    BG_RED = '\033[41m'
    BG_MAGENTA = '\033[45m'


def init_terminal():
    if os.name == 'nt':
        os.system('color')
        try:
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)  # enable VT processing
        except Exception:
            pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, OSError):
            pass


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


# ─────────────────────────── BOX PRIMITIVES ───────────────────────────

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def _vlen(s):
    return len(_ANSI_RE.sub('', s))


def _pad(s, width):
    return s + ' ' * max(0, width - _vlen(s))


def _center(s, width):
    diff = max(0, width - _vlen(s))
    return ' ' * (diff // 2) + s + ' ' * (diff - diff // 2)


def _borders(style):
    if style == 'double':
        return '╔', '╗', '╚', '╝', '═', '║'
    return '┌', '┐', '└', '┘', '─', '│'


def box(rows, title=None, color=Colors.CYAN, style='round', width=80):
    """Render a framed box with padded, ANSI-safe rows."""
    tl, tr, bl, br, h, v = _borders(style)
    inner = width - 2
    out = [f"{color}{tl}{h * inner}{tr}{Colors.RESET}"]
    if title:
        t = f" {Colors.BOLD}{color}{title}{Colors.RESET} "
        dashes = h * max(0, (inner - 2) - _vlen(t))
        out.append(f"{color}{v}{Colors.RESET}{t}{dashes}{color}{v}{Colors.RESET}")
    for r in rows:
        out.append(f"{color}{v}{Colors.RESET} {_pad(r, inner - 2)} {color}{v}{Colors.RESET}")
    out.append(f"{color}{bl}{h * inner}{br}{Colors.RESET}")
    print('\n'.join(out))


def _info(label, value, vcolor=Colors.YELLOW):
    return f"{Colors.WHITE}{label:<11}{Colors.CYAN}: {vcolor}{value}{Colors.RESET}"


# ─────────────────────────── BANNER ───────────────────────────

def print_banner(version, developer):
    clear_screen()
    art = [
        '█████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗',
        '██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗',
        '███████║██║  ██║██╔████╔██║██║██╔██╗ ██║███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝',
        '██╔══██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗',
        '██║  ██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║',
        '╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝',
    ]
    art = [line.rstrip() for line in art]
    maxw = max(len(line) for line in art)
    art = [line + ' ' * (maxw - len(line)) for line in art]
    rows = [_center(f"{Colors.GREEN}{line}{Colors.RESET}", 96) for line in art]
    rows.append('')
    rows.append(_center(f"{Colors.BOLD}{Colors.WHITE}THE ULTIMATE SENSITIVE INFORMATION GATHERING FRAMEWORK{Colors.RESET}", 96))
    rows.append(_center(f"{Colors.DIM}{Colors.GRAY}SECURITY RESEARCH  •  AUTHORIZED TESTING ONLY  •  ADVANCED RECON ENGINE{Colors.RESET}", 96))
    rows.append('')
    rows.append(f"{Colors.CYAN}{'─' * 96}{Colors.RESET}")
    rows += [
        _info('Version', version, Colors.GREEN) + '  │  ' + _info('Engine', 'Async (asyncio)', Colors.MAGENTA),
        _info('Developer', developer, Colors.MAGENTA) + '  │  ' + _info('Telegram', '@xFFBI', Colors.BLUE),
        _info('Wordlist', 'Ultra Massive', Colors.YELLOW) + '  │  ' + _info('Status', 'READY', Colors.GREEN),
    ]
    box(rows, color=Colors.CYAN, width=100)


# ─────────────────────────── SECTIONS ───────────────────────────

def print_target_box(target):
    box([
        f"{Colors.WHITE}Target  {Colors.CYAN}: {Colors.GREEN}{target}",
        f"{Colors.WHITE}Started {Colors.CYAN}: {Colors.YELLOW}{datetime.now():%Y-%m-%d %H:%M:%S}",
    ], title='TARGET', style='double', color=Colors.CYAN)


def print_recon_box(recon_info):
    badges = ' '.join(f"{Colors.GREEN}[{t}]{Colors.RESET}" for t in recon_info['tech'])
    badges = badges or f"{Colors.GRAY}None detected{Colors.RESET}"
    box([
        f"{Colors.WHITE}IP Address {Colors.CYAN}: {Colors.GREEN}{recon_info['ip']}",
        f"{Colors.WHITE}Web Server {Colors.CYAN}: {Colors.GREEN}{recon_info['server']}",
        f"{Colors.WHITE}Powered-By {Colors.CYAN}: {Colors.GREEN}{recon_info['powered_by']}",
        f"{Colors.WHITE}Platforms  {Colors.CYAN}: {badges}",
    ], title='TARGET RECONNAISSANCE', style='double', color=Colors.CYAN)


def print_config_box(cfg):
    wl = f"{cfg['paths']:,} paths"
    if cfg.get('tech_paths'):
        wl += f" (+{cfg['tech_paths']:,} tech)"
    box([
        _info('Wordlist', wl) + '  │  ' + _info('Concurrency', cfg['concurrency'], Colors.GREEN),
        _info('Timeout', f"{cfg['timeout']}s adaptive") + '  │  ' + _info('Delay', f"{cfg['delay']}s", Colors.GREEN),
        _info('Recursion', f"ON (depth {cfg['depth']})" if cfg['recursive'] else 'OFF') + '  │  ' + _info('Extraction', 'ON' if cfg['extract'] else 'OFF', Colors.GREEN),
        _info('Proxies', cfg['proxies'] or 'None') + '  │  ' + _info('Stop on first', 'YES' if cfg['stop_on_found'] else 'NO', Colors.GREEN),
    ], title='SCAN CONFIGURATION', style='double', color=Colors.CYAN)


def print_summary_box(stats, duration, rate):
    def kv(label, value, vcolor=Colors.WHITE):
        return f"{Colors.WHITE}{label:<15}{Colors.CYAN}: {vcolor}{str(value)}{Colors.RESET}"
    box([
        kv('Total Requests', f"{stats['total_requests']:,}") + '  │  ' + kv('Scan Time', duration, Colors.GREEN),
        kv('Admin Panels', stats['found_panels'], Colors.GREEN) + '  │  ' + kv('Rate', f"{rate:.0f} req/s", Colors.CYAN),
        kv('Sensitive Files', stats['sensitive_files'], Colors.YELLOW) + '  │  ' + kv('Auth Endpoints', stats['auth'], Colors.MAGENTA),
        kv('Secrets', stats.get('secrets', 0), Colors.MAGENTA) + '  │  ' + kv('Retries', stats['retries'], Colors.GRAY),
        kv('Failed', stats['failed'], Colors.RED),
    ], title='FINAL SCANNING STATISTICS', style='double', color=Colors.CYAN)


# ─────────────────────────── LOGGING ───────────────────────────

def log_success(msg):
    print(f"{Colors.BOLD}{Colors.GREEN}[+] {msg}{Colors.RESET}")


def log_error(msg):
    print(f"{Colors.BOLD}{Colors.RED}[-] {msg}{Colors.RESET}")


def log_info(msg):
    print(f"{Colors.BOLD}{Colors.CYAN}[*] {msg}{Colors.RESET}")


def log_warning(msg):
    print(f"{Colors.BOLD}{Colors.YELLOW}[!] {msg}{Colors.RESET}")


_TYPE_STYLE = {
    'ADMIN': (Colors.BG_GREEN, Colors.GREEN),
    'AUTH': (Colors.BG_YELLOW, Colors.YELLOW),
    'SENSITIVE': (Colors.BG_CYAN, Colors.CYAN),
    'SECRET': (Colors.BG_MAGENTA, Colors.MAGENTA),
}


def log_found(url, code, type_label, title="N/A", reasons=None, score=0, details=None):
    bg, fg = _TYPE_STYLE.get(type_label, (Colors.BG_RED, Colors.RED))
    stamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n{bg}{Colors.BOLD}{Colors.WHITE}  {type_label} DISCOVERED!  {Colors.RESET}")
    rows = [
        f"{Colors.GRAY}[{stamp}]{Colors.RESET} {fg}{url}{Colors.RESET}",
        f"Status: {Colors.BOLD}{code}{Colors.RESET} │ Type: {Colors.MAGENTA}{title}{Colors.RESET}"
        + (f" │ Score: {Colors.MAGENTA}{score}{Colors.RESET}" if type_label == 'ADMIN' else ''),
    ]
    if reasons:
        rows.append(f"Reasons: {Colors.GRAY}{', '.join(reasons)}{Colors.RESET}")
    for label, value in (details or []):
        rows.append(f"{Colors.WHITE}{label}{Colors.CYAN}: {Colors.YELLOW}{value}{Colors.RESET}")
    box(rows, color=fg, width=80)
    print()
