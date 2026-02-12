import requests
import re
import random
import time
import sys
from threading import Thread, Lock, Event
from queue import Queue
from urllib.parse import urljoin
from utils.waf import get_advanced_headers
from utils.ui import log_found, Colors

class Scanner:
    def __init__(self, target, paths, threads=30, timeout=10, stop_on_found=True):
        self.target = target
        self.paths = paths
        self.threads_count = threads
        self.timeout = timeout
        self.stop_on_found = stop_on_found
        
        self.q = Queue()
        for p in paths: self.q.put(p)
        
        self.total_paths = len(paths)
        self.stats = {
            'total_requests': 0,
            'found_panels': 0,
            'sensitive_files': 0,
            'failed': 0
        }
        self.stats_lock = Lock()
        self.stop_event = Event()
        self.results = []
        self.current_path = ""
        
        # Detection keywords
        self.admin_keywords = ['login', 'password', 'username', 'admin panel', 'dashboard', 'sign in', 'authenticate']
        self.sensitive_exts = ['.env', '.git', '.sql', '.zip', '.bak', 'config.php', 'phpinfo.php', '.htaccess']

    def extract_title(self, html):
        title = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
        return title.group(1).strip() if title else "N/A"

    def is_admin_page(self, response):
        content = response.text.lower()
        keyword_match = any(kw in content for kw in self.admin_keywords)
        input_match = '<input' in content and 'type="password"' in content
        return keyword_match or input_match

    def worker(self):
        while not self.q.empty() and not self.stop_event.is_set():
            path = self.q.get()
            self.current_path = path # For real-time display
            url = urljoin(self.target, path)
            try:
                headers = get_advanced_headers()
                response = requests.get(url, headers=headers, timeout=self.timeout, verify=False, allow_redirects=True)
                
                with self.stats_lock: self.stats['total_requests'] += 1
                
                if response.status_code == 200:
                    if len(response.text) < 200 and "not found" in response.text.lower():
                        continue

                    is_sensitive = any(ext in url for ext in self.sensitive_exts)
                    type_label = "SENSITIVE" if is_sensitive else "ADMIN"
                    
                    if type_label == "ADMIN" and not self.is_admin_page(response):
                        continue

                    title = self.extract_title(response.text)
                    log_found(url, response.status_code, type_label, title)
                    
                    result = {'url': url, 'code': response.status_code, 'type': type_label, 'title': title}
                    self.results.append(result)
                    
                    with self.stats_lock:
                        if type_label == "ADMIN": self.stats['found_panels'] += 1
                        else: self.stats['sensitive_files'] += 1
                    
                    if type_label == "ADMIN" and self.stop_on_found:
                        self.stop_event.set()
                
            except Exception:
                with self.stats_lock: self.stats['failed'] += 1
            finally:
                self.q.task_done()

    def run(self):
        threads = []
        for _ in range(self.threads_count):
            t = Thread(target=self.worker)
            t.daemon = True
            t.start()
            threads.append(t)
        
        try:
            while any(t.is_alive() for t in threads) and not self.stop_event.is_set():
                # Real-time progress bar and live path
                with self.stats_lock:
                    progress = (self.stats['total_requests'] / self.total_paths) * 100 if self.total_paths > 0 else 0
                    bar_len = 30
                    filled_len = int(bar_len * progress / 100)
                    bar = '█' * filled_len + '░' * (bar_len - filled_len)
                    
                    # Clear line and print status
                    sys.stdout.write(f"\r{Colors.BOLD}{Colors.CYAN}[SCANNING] {Colors.WHITE}|{bar}| {progress:.1f}% {Colors.YELLOW}Testing: {Colors.GRAY}{self.current_path[:30].ljust(30)}{Colors.RESET}")
                    sys.stdout.flush()
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_event.set()
        
        return self.results
