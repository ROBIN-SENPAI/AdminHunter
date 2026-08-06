import json
from datetime import datetime


def _timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def save_results(results, output_base):
    """Save scan results to JSON and plain-text report files.

    Returns a tuple of the generated paths (json_path, txt_path).
    """
    if not output_base.endswith(('.json', '.txt')):
        output_base = output_base.rstrip('.') or 'scan'

    json_path = f"{output_base}.json"
    txt_path = f"{output_base}.txt"

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"AdminHunter Elite Pro — Scan Report\n")
        f.write(f"Generated: {_timestamp()}\n")
        f.write(f"Total findings: {len(results)}\n")
        f.write("=" * 60 + "\n\n")
        for i, r in enumerate(results, 1):
            f.write(f"[{i}] [{r.get('type', '?')}] {r.get('url', '?')} (HTTP {r.get('code', '?')})\n")
            f.write(f"    Title: {r.get('title', 'N/A')}\n")
            if r.get('type') == 'SECRET':
                f.write(f"    Secret: {r.get('secret_type', '?')} = {r.get('value', '?')}\n")
                if r.get('context'):
                    f.write(f"    Context: {r['context']}\n")
            if r.get('score'):
                f.write(f"    Score: {r['score']} | Reasons: {', '.join(r.get('reasons', [])) or 'N/A'}\n")
            f.write("\n")

    return json_path, txt_path


def _esc(value):
    """Escape a value for safe HTML embedding."""
    return str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

TYPE_BADGE = {
    'ADMIN': ('#e74c3c', 'Admin Panel'),
    'SENSITIVE': ('#e67e22', 'Sensitive File'),
    'AUTH': ('#9b59b6', 'Auth Endpoint'),
    'SECRET': ('#e84393', 'Secret'),
}


def save_html_report(results, output_base, target='N/A', stats=None, version="5.0 Elite Pro"):
    """Save a self-contained HTML report. Returns the generated path."""
    if not output_base.endswith(('.json', '.txt')):
        output_base = output_base.rstrip('.') or 'scan'
    html_path = f"{output_base}.html"

    stats = stats or {}
    counts = {'ADMIN': 0, 'SENSITIVE': 0, 'AUTH': 0, 'SECRET': 0}
    for r in results:
        if r.get('type') in counts:
            counts[r['type']] += 1

    rows = []
    for r in results:
        color, label = TYPE_BADGE.get(r.get('type'), ('#95a5a6', r.get('type', '?')))
        if r.get('type') == 'SECRET':
            reasons = f"{_esc(r.get('secret_type'))} = <b>{_esc(r.get('value'))}</b>"
        else:
            reasons = ' &middot; '.join(_esc(x) for x in r.get('reasons', [])) or '—'
        auth = f"<span class='auth'>{_esc(r.get('auth'))}</span>" if r.get('auth') else '—'
        rows.append(
            f"<tr><td><span class='badge' style='background:{color}'>{label}</span></td>"
            f"<td class='url'>{_esc(r.get('url'))}</td>"
            f"<td>{r.get('code', '?')}</td>"
            f"<td>{_esc(r.get('title', 'N/A'))}</td>"
            f"<td>{auth}</td>"
            f"<td>{r.get('score', 0)}</td>"
            f"<td class='reasons'>{reasons}</td></tr>"
        )

    card = (
        lambda label, value, color: f"<div class='card'><span class='num' style='color:{color}'>{value}</span>"
        f"<span class='lbl'>{label}</span></div>"
    )
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AdminHunter Scan Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0d1117; color: #e6edf3; font-family: 'Segoe UI', system-ui, sans-serif; padding: 32px 16px; }}
  .wrap {{ max-width: 1100px; margin: 0 auto; }}
  h1 {{ font-size: 22px; letter-spacing: 1px; }}
  h1 span {{ color: #58a6ff; }}
  .meta {{ color: #8b949e; font-size: 13px; margin: 8px 0 24px; }}
  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 28px; }}
  .card {{ background: #161b22; border: 1px solid #21262d; border-radius: 10px; padding: 16px; text-align: center; }}
  .num {{ font-size: 30px; font-weight: 700; display: block; }}
  .lbl {{ font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #8b949e; }}
  table {{ width: 100%; border-collapse: collapse; background: #161b22; border-radius: 10px; overflow: hidden; }}
  th, td {{ padding: 10px 12px; text-align: left; font-size: 13px; border-bottom: 1px solid #21262d; }}
  th {{ background: #1c2128; color: #8b949e; text-transform: uppercase; font-size: 11px; letter-spacing: 1px; }}
  tr:last-child td {{ border-bottom: none; }}
  .badge {{ color: #fff; padding: 3px 10px; border-radius: 999px; font-size: 11px; font-weight: 600; white-space: nowrap; }}
  .url {{ font-family: Consolas, monospace; color: #79c0ff; word-break: break-all; }}
  .auth {{ font-family: Consolas, monospace; color: #d2a8ff; }}
  .reasons {{ color: #8b949e; font-size: 12px; }}
  .empty {{ color: #8b949e; text-align: center; padding: 40px; }}
  .foot {{ margin-top: 24px; color: #8b949e; font-size: 12px; text-align: center; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>AdminHunter <span>Elite Pro</span> — Scan Report</h1>
  <div class="meta">Target: <b>{_esc(target)}</b> &nbsp;|&nbsp; Generated: {_timestamp()} &nbsp;|&nbsp; Version: {version}</div>
  <div class="cards">
    {card('Admin Panels', counts['ADMIN'], '#e74c3c')}
    {card('Sensitive Files', counts['SENSITIVE'], '#e67e22')}
    {card('Auth Endpoints', counts['AUTH'], '#9b59b6')}
    {card('Secrets', counts['SECRET'], '#e84393')}
    {card('Total Requests', stats.get('total_requests', 0), '#58a6ff')}
    {card('Retries', stats.get('retries', 0), '#58a6ff')}
    {card('Failed', stats.get('failed', 0), '#e74c3c')}
  </div>
  <table>
    <thead><tr><th>Type</th><th>URL</th><th>HTTP</th><th>Title</th><th>Auth</th><th>Score</th><th>Reasons</th></tr></thead>
    <tbody>{''.join(rows) if rows else f"<tr><td colspan='7' class='empty'>No findings detected</td></tr>"}</tbody>
  </table>
  <div class="foot">Generated by AdminHunter Elite Pro — {_esc(version)}</div>
</div>
</body>
</html>"""
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return html_path
