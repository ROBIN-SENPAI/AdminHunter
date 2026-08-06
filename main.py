#!/usr/bin/env python3
import argparse
import os
import sys
import time
from datetime import datetime
from core.recon import gather_recon
from core.scanner import Scanner
from utils.ui import (init_terminal, print_banner, print_target_box, print_recon_box,
                      print_config_box, print_summary_box,
                      log_info, log_success, log_error, Colors)
from utils.logger import save_results, save_html_report

VERSION = "5.0 Elite Pro"
DEVELOPER = "ROBIN ABU IBRAHIM"

def load_paths(custom_file=None):
    paths = []
    # Default sensitive paths
    paths.extend(['.env', '.git/config', 'phpinfo.php', 'config.php', 'wp-config.php', 'backup.sql', '.htaccess'])
    
    file_to_load = custom_file if custom_file and os.path.exists(custom_file) else "data/magic_admin_paths.txt"
    
    if os.path.exists(file_to_load):
        try:
            with open(file_to_load, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'): continue
                    # Handle {ext} placeholder
                    if '{ext}' in line:
                        for ext in ['.php', '.asp', '.aspx', '.jsp', '.html']:
                            paths.append(line.replace('{ext}', ext))
                    else:
                        paths.append(line)
        except Exception as e:
            log_error(f"Error loading wordlist: {e}")
    return list(set(paths))

TECH_WORDLISTS = {
    'WordPress': 'wordpress.txt',
    'Drupal': 'drupal.txt',
    'Joomla': 'joomla.txt',
    'Laravel': 'laravel.txt',
    'Django': 'django.txt',
    'ASP.NET': 'aspnet.txt',
}


def load_lines(path):
    out = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                out.append(line)
    return out


def merge_unique(items):
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def load_tech_paths(tech_list):
    """Load tech-specific wordlists from data/tech/ for each detected technology."""
    joined = ' '.join(tech_list).lower()
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'tech')
    paths = []
    for key, fname in TECH_WORDLISTS.items():
        if key.lower() in joined:
            p = os.path.join(base, fname)
            if os.path.exists(p):
                paths.extend(load_lines(p))
    return paths


def load_proxies(path):
    """Load a list of proxies from a file (one per line, '#' = comment)."""
    if not path or not os.path.exists(path):
        return None
    proxies = []
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                proxies.append(line)
    return proxies or None


def main():
    parser = argparse.ArgumentParser(description="AdminHunter Elite Pro v5.0")
    parser.add_argument("-t", "--target", help="Target URL")
    parser.add_argument("-w", "--wordlist", help="Path to custom wordlist")
    parser.add_argument("--threads", "--concurrency", dest="concurrency", type=int, default=50,
                        help="Max concurrent requests (alias: --threads)")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--no-stop", action="store_true", default=False, help="Don't stop when an admin panel is found")
    parser.add_argument("--delay", type=float, default=0.0, help="Min delay between requests in seconds (jitter applied)")
    parser.add_argument("--proxy", help="Single HTTP/S proxy URL (e.g. http://user:pass@host:port)")
    parser.add_argument("--proxies", help="File with a list of proxies (one per line), rotated automatically with failover")
    parser.add_argument("--recursive", action="store_true", help="Recursively scan discovered directories")
    parser.add_argument("--depth", type=int, default=2, help="Max recursion depth (used with --recursive)")
    parser.add_argument("--no-extract", action="store_true", help="Disable automatic link/JS endpoint discovery")
    parser.add_argument("-o", "--output", help="Base name for the result files (JSON + TXT)")
    
    args = parser.parse_args()
    
    init_terminal()
    print_banner(VERSION, DEVELOPER)
    
    # Automatic Interactive Mode
    target = args.target
    if not target:
        print(f"\n{Colors.BOLD}{Colors.GREEN}[!] Automation Enabled: Enter the URL and I'll do the rest...{Colors.RESET}")
        target = input(f"{Colors.BOLD}{Colors.CYAN}┌─[ Enter Target URL ]\n└─╼ {Colors.YELLOW}").strip()
    
    if not target:
        log_error("No target specified. Exiting.")
        return

    if not target.startswith('http'):
        target = 'https://' + target

    # Target + Recon Phase
    print_target_box(target)
    log_info("Performing initial reconnaissance...")
    recon_info = gather_recon(target)
    print_recon_box(recon_info)

    # Load Paths (tech-specific wordlists get priority)
    paths = load_paths(args.wordlist)
    tech_paths = load_tech_paths(recon_info['tech'])
    paths = merge_unique(tech_paths + paths)
    log_info(f"Loaded {len(paths)} paths for scanning ({len(tech_paths)} tech-specific).")

    print_config_box({
        'paths': len(paths),
        'tech_paths': len(tech_paths),
        'concurrency': args.concurrency,
        'timeout': args.timeout,
        'delay': args.delay,
        'recursive': args.recursive,
        'depth': args.depth,
        'extract': not args.no_extract,
        'proxies': len(load_proxies(args.proxies)) if load_proxies(args.proxies) else 0,
        'stop_on_found': not args.no_stop,
    })

    # Start Scanner (async engine — Phase 2/3)
    scanner = Scanner(
        target=target,
        paths=paths,
        concurrency=args.concurrency,
        timeout=args.timeout,
        stop_on_found=not args.no_stop,
        proxy=args.proxy,
        proxies=load_proxies(args.proxies),
        delay=args.delay,
        recursive=args.recursive,
        max_depth=args.depth,
        extract_links=not args.no_extract
    )
    
    log_info("Starting scanning engine... (Real-time tracking enabled)")
    results = scanner.run()
    
    # Summary
    elapsed = max(0.001, time.time() - scanner.started_at)
    duration = time.strftime('%H:%M:%S', time.gmtime(elapsed))
    rate = scanner.stats['total_requests'] / elapsed
    print_summary_box(scanner.stats, duration, rate)
    
    # Auto-save results (JSON + TXT + HTML)
    output_base = args.output if args.output else f"scan_{datetime.now().strftime('%H%M%S')}"
    try:
        json_path, txt_path = save_results(results, output_base)
        log_success(f"Results saved to {json_path} and {txt_path}")
        html_path = save_html_report(results, output_base, target=target, stats=scanner.stats, version=VERSION)
        log_success(f"HTML report saved to {html_path}")
    except Exception as e:
        log_error(f"Failed to save results: {e}")

    log_info("Scan completed.")
    try:
        input(f"\n{Colors.BOLD}{Colors.YELLOW}Press Enter to exit...{Colors.RESET}")
    except EOFError:
        pass

if __name__ == "__main__":
    main()
