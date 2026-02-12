import os
import ctypes
from datetime import datetime

class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
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

def init_terminal():
    if os.name == 'nt':
        os.system('color')
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception: pass

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner(version, developer):
    clear_screen()
    banner = f"""
{Colors.BOLD}{Colors.CYAN}┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                    │
│      {Colors.GREEN}█████╗ ██████╗ ███╗   ███╗██╗███╗   ██╗██╗  ██╗██╗   ██╗███╗   ██╗████████╗███████╗██████╗{Colors.CYAN}      │
│     {Colors.GREEN}██╔══██╗██╔══██╗████╗ ████║██║████╗  ██║██║  ██║██║   ██║████╗  ██║╚══██╔══╝██╔════╝██╔══██╗{Colors.CYAN}     │
│     {Colors.GREEN}███████║██║  ██║██╔████╔██║██║██╔██╗ ██║███████║██║   ██║██╔██╗ ██║   ██║   █████╗  ██████╔╝{Colors.CYAN}     │
│     {Colors.GREEN}██╔══██║██║  ██║██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║   ██║██║╚██╗██║   ██║   ██╔══╝  ██╔══██╗{Colors.CYAN}     │
│     {Colors.GREEN}██║  ██║██████╔╝██║ ╚═╝ ██║██║██║ ╚████║██║  ██║╚██████╔╝██║ ╚████║   ██║   ███████╗██║  ██║{Colors.CYAN}     │
│     {Colors.GREEN}╚═╝  ╚═╝╚═════╝ ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝{Colors.CYAN}     │
│                                                                                                    │
│                     {Colors.MAGENTA}THE ULTIMATE SENSITIVE INFORMATION GATHERING FRAMEWORK{Colors.CYAN}                        │
│                                                                                                    │
├────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  {Colors.WHITE}Version   : {Colors.GREEN}{version.ljust(20)}{Colors.CYAN} │  {Colors.WHITE}Developer : {Colors.MAGENTA}{developer.ljust(20)}{Colors.CYAN} │
│  {Colors.WHITE}Telegram  : {Colors.BLUE}{'@xFFBI'.ljust(20)}{Colors.CYAN} │  {Colors.WHITE}Wordlist  : {Colors.YELLOW}{'Ultra Massive'.ljust(20)}{Colors.CYAN} │
└────────────────────────────────────────────────────────────────────────────────────────────────────┘
{Colors.RESET}"""
    print(banner)

def log_success(msg):
    print(f"{Colors.BOLD}{Colors.GREEN}[+] {msg}{Colors.RESET}")

def log_error(msg):
    print(f"{Colors.BOLD}{Colors.RED}[-] {msg}{Colors.RESET}")

def log_info(msg):
    print(f"{Colors.BOLD}{Colors.CYAN}[*] {msg}{Colors.RESET}")

def log_warning(msg):
    print(f"{Colors.BOLD}{Colors.YELLOW}[!] {msg}{Colors.RESET}")

def log_found(url, code, type_label, title="N/A"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    bg = Colors.BG_GREEN if type_label == "ADMIN" else Colors.BG_CYAN
    print(f"\n{bg}{Colors.BOLD}{Colors.WHITE}  {type_label} DISCOVERED!  {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}┌{'─' * 78}┐{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}│{Colors.RESET} {Colors.BOLD}{Colors.WHITE}[{timestamp}] {Colors.GREEN}{url}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}│{Colors.RESET} {Colors.WHITE}Status: {Colors.YELLOW}{code}{Colors.RESET} | {Colors.WHITE}Title: {Colors.CYAN}{title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.GREEN}└{'─' * 78}┘{Colors.RESET}\n")
