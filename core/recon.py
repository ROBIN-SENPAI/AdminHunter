import socket
import requests
import urllib3
from urllib.parse import urlparse

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def gather_recon(target):
    info = {
        'ip': 'Unknown',
        'server': 'Unknown',
        'powered_by': 'Unknown',
        'tech': []
    }
    try:
        parsed = urlparse(target)
        domain = parsed.netloc
        info['ip'] = socket.gethostbyname(domain)
        
        response = requests.get(target, verify=False, timeout=10)
        headers = response.headers
        
        info['server'] = headers.get('Server', 'Unknown')
        info['powered_by'] = headers.get('X-Powered-By', 'Unknown')
        
        content = response.text.lower()
        if 'wp-content' in content: info['tech'].append('WordPress')
        if 'drupal' in content: info['tech'].append('Drupal')
        if 'joomla' in content: info['tech'].append('Joomla')
        if 'laravel' in content: info['tech'].append('Laravel')
        if 'django' in content: info['tech'].append('Django')
        if 'express' in content: info['tech'].append('Express')
        
    except Exception:
        pass
    return info
