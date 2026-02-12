#!/usr/bin/env python3
import argparse
import os
import sys
import json
from datetime import datetime
from core.recon import gather_recon
from core.scanner import Scanner
from utils.ui import init_terminal, print_banner, log_info, log_success, log_error, Colors

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

def main():
    parser = argparse.ArgumentParser(description="AdminHunter Elite Pro v5.0")
    parser.add_argument("-t", "--target", help="Target URL")
    parser.add_argument("-w", "--wordlist", help="Path to custom wordlist")
    parser.add_argument("--threads", type=int, default=40, help="Number of concurrent threads")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--no-stop", action="store_true", default=True, help="Don't stop when an admin panel is found")
    parser.add_argument("-o", "--output", help="Save results to a JSON file")
    
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
        
    log_info(f"Target: {target}")
    
    # Recon Phase
    recon_info = gather_recon(target)
    print(f"\n{Colors.BOLD}{Colors.WHITE}SERVER INFORMATION{Colors.RESET}")
    print(f"{Colors.CYAN}├─ IP: {Colors.GREEN}{recon_info['ip']}{Colors.RESET}")
    print(f"{Colors.CYAN}├─ Server: {Colors.GREEN}{recon_info['server']}{Colors.RESET}")
    print(f"{Colors.CYAN}└─ Tech: {Colors.GREEN}{', '.join(recon_info['tech']) if recon_info['tech'] else 'None detected'}{Colors.RESET}\n")
    
    # Load Paths
    paths = load_paths(args.wordlist)
    log_info(f"Loaded {len(paths)} paths for scanning.")
    
    # Start Scanner
    scanner = Scanner(
        target=target, 
        paths=paths, 
        threads=args.threads, 
        timeout=args.timeout, 
        stop_on_found=not args.no_stop
    )
    
    log_info("Starting scanning engine... (Real-time tracking enabled)")
    results = scanner.run()
    
    # Summary
    print(f"\n{Colors.BOLD}{Colors.CYAN}┌{'─' * 78}┐{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}│{Colors.RESET} {Colors.BOLD}{Colors.WHITE}FINAL SCANNING STATISTICS{Colors.CYAN}{' ' * 52}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}├{'─' * 78}┤{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}│{Colors.RESET} {Colors.WHITE}Total Requests:  {str(scanner.stats['total_requests']).ljust(58)}{Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}│{Colors.RESET} {Colors.WHITE}Admin Panels:    {str(scanner.stats['found_panels']).ljust(58)}{Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}│{Colors.RESET} {Colors.WHITE}Sensitive Files: {str(scanner.stats['sensitive_files']).ljust(58)}{Colors.CYAN}│{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}└{'─' * 78}┘{Colors.RESET}\n")
    
    # Auto-save results
    output_file = args.output if args.output else f"scan_{datetime.now().strftime('%H%M%S')}.json"
    try:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=4)
        log_success(f"Results saved to {output_file}")
    except Exception as e:
        log_error(f"Failed to save results: {e}")

    log_info("Scan completed.")
    input(f"\n{Colors.BOLD}{Colors.YELLOW}Press Enter to exit...{Colors.RESET}")

if __name__ == "__main__":
    main()
