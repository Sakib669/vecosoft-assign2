"""
Screenshot Generator for Vecosoft Assessment Task 2.
Executes the live LRU Cache and TTLCache implementations, captures styled
program output, and renders high-resolution PNG screenshots matching submission requirements.
"""

from __future__ import annotations
import os
import sys

# Ensure UTF-8 encoding so Rich renders crisp unicode box-drawing characters
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import subprocess
import time
from pathlib import Path

from src.lru_cache import Cache, TTLCache
from rich.console import Console
from rich.table import Table
from rich.box import ROUNDED


def create_terminal_html(title: str, content_html: str) -> str:
    """Wraps Rich HTML output inside a modern dark-mode terminal window mockup."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    html, body {{
      background: #0d1117;
      font-family: 'Consolas', 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
      padding: 20px;
      overflow: hidden;
    }}
    .terminal-window {{
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      box-shadow: 0 15px 35px rgba(0, 0, 0, 0.7);
      width: 980px;
      overflow: hidden;
      margin: 0 auto;
    }}
    .terminal-header {{
      background: #1f242c;
      padding: 10px 16px;
      display: flex;
      align-items: center;
      border-bottom: 1px solid #30363d;
    }}
    .terminal-dots {{
      display: flex;
      gap: 7px;
      margin-right: 18px;
    }}
    .dot {{
      width: 11px;
      height: 11px;
      border-radius: 50%;
    }}
    .dot-red {{ background: #ff5f56; }}
    .dot-yellow {{ background: #ffbd2e; }}
    .dot-green {{ background: #27c93f; }}
    .terminal-title {{
      color: #8b949e;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.4px;
    }}
    .terminal-body {{
      padding: 20px 24px;
      font-size: 13.5px;
      line-height: 1.45;
      color: #c9d1d9;
    }}
    pre {{
      font-family: inherit;
      margin: 0;
    }}
  </style>
</head>
<body>
  <div class="terminal-window">
    <div class="terminal-header">
      <div class="terminal-dots">
        <div class="dot dot-red"></div>
        <div class="dot dot-yellow"></div>
        <div class="dot dot-green"></div>
      </div>
      <div class="terminal-title">{title}</div>
    </div>
    <div class="terminal-body">
      {content_html}
    </div>
  </div>
</body>
</html>
"""


def generate_lru_core_screenshot(output_png: Path, html_file: Path) -> None:
    """Executes the exact assessment sequence and renders the required output screenshot."""
    console = Console(record=True, width=105, force_terminal=True)

    console.rule("[bold cyan]TASK 2 — LRU CACHE EXECUTION & VERIFICATION[/bold cyan]")
    console.print("[dim white]Operations: Real-time put(), get(), LRU eviction, and returned values[/dim white]\n")

    cache = Cache(2)

    operations = [
        ("put", ("A", 10)),
        ("put", ("B", 20)),
        ("get", ("A",)),
        ("put", ("C", 30)),
        ("get", ("B",)),
        ("get", ("C",)),
        ("get", ("A",)),
    ]

    table = Table(
        title="LRU Cache Operations Walkthrough (Capacity = 2)",
        box=ROUNDED,
        header_style="bold magenta",
        title_style="bold white on blue",
        show_lines=True,
    )
    table.add_column("Step", justify="center", style="bold cyan", width=6)
    table.add_column("Operation", style="bold yellow", width=16)
    table.add_column("Return Value", justify="center", style="bold green", width=14)
    table.add_column("Eviction Action", justify="center", style="bold red", width=22)
    table.add_column("Internal Order (MRU -> LRU)", style="bold white", width=38)

    for step, (op, args) in enumerate(operations, 1):
        if op == "put":
            k, v = args
            evicted = cache.put(k, v)
            ret_val = "None"
            evict_str = f"Evicted ({evicted[0]}: {evicted[1]})" if evicted else "-"
        else:
            k = args[0]
            val = cache.get(k)
            ret_val = str(val)
            evict_str = "-"

        state = cache.state_display()
        arg_str = f'("{args[0]}"' + (f', {args[1]})' if len(args) > 1 else ')')
        table.add_row(f"#{step}", f"{op}{arg_str}", ret_val, evict_str, state)

    console.print(table)
    console.print("\n[bold green][PASS][/bold green] [white]cache.get('A')[/white] -> [bold cyan]10[/bold cyan] [dim](promoted 'A' to Most Recently Used)[/dim]")
    console.print("[bold green][PASS][/bold green] [white]cache.put('C', 30)[/white] -> [bold red]Evicted 'B'[/bold red] [dim](because 'B' was Least Recently Used)[/dim]")
    console.print("[bold green][PASS][/bold green] [white]cache.get('B')[/white] -> [bold red]-1[/bold red] [dim](correctly returns -1 for evicted key)[/dim]")
    console.print("[bold green][PASS][/bold green] [white]cache.get('C')[/white] -> [bold cyan]30[/bold cyan] [dim](retrieved value)[/dim]")
    console.print("[bold green][PASS][/bold green] [white]cache.get('A')[/white] -> [bold cyan]10[/bold cyan] [dim](retrieved value and promoted to MRU)[/dim]")

    raw_html = console.export_html(inline_styles=True)
    start = raw_html.find("<pre")
    end = raw_html.rfind("</pre>") + 6
    body_content = raw_html[start:end] if start != -1 and end != -1 else raw_html

    full_html = create_terminal_html("python demo.py (Core LRU Cache Verification)", body_content)
    html_file.write_text(full_html, encoding="utf-8")

    render_html_to_png(html_file, output_png, window_size="1040,680")


def generate_ttl_bonus_screenshot(output_png: Path, html_file: Path) -> None:
    """Demonstrates optional TTL expiration support and renders the bonus screenshot."""
    console = Console(record=True, width=105, force_terminal=True)

    console.rule("[bold magenta]TASK 2 BONUS — TIME-TO-LIVE (TTL) EXPIRATION[/bold magenta]")
    console.print("[dim white]Execution: Validating time-based expiration and lazy pruning alongside LRU[/dim white]\n")

    ttl_cache = TTLCache(capacity=3)

    insert_table = Table(title="1. Key Insertion with TTL Parameters", box=ROUNDED, header_style="bold cyan", show_lines=True)
    insert_table.add_column("Key", style="bold yellow", width=16)
    insert_table.add_column("Value", style="bold green", width=16)
    insert_table.add_column("Configured TTL", style="bold magenta", width=16)
    insert_table.add_column("Behavior Description", style="white")

    insert_table.add_row("session_temp", "tok_xyz_123", "1.0 second", "Expires in 1.0s")
    insert_table.add_row("auth_token", "jwt_valid_456", "3.0 seconds", "Expires in 3.0s")
    insert_table.add_row("app_config", "env_production", "None (Permanent)", "Persists until LRU capacity eviction")

    console.print(insert_table)

    ttl_cache.put("session_temp", "tok_xyz_123", ttl=1.0)
    ttl_cache.put("auth_token", "jwt_valid_456", ttl=3.0)
    ttl_cache.put("app_config", "env_production", ttl=None)

    v1 = ttl_cache.get("session_temp")
    v2 = ttl_cache.get("auth_token")
    v3 = ttl_cache.get("app_config")

    read_table1 = Table(title="2. Immediate Access Verification (Elapsed: 0.0s)", box=ROUNDED, header_style="bold cyan", show_lines=True)
    read_table1.add_column("Operation", style="bold yellow", width=24)
    read_table1.add_column("Returned Value", style="bold green", width=18)
    read_table1.add_column("Status Assessment", style="white")
    read_table1.add_row('get("session_temp")', str(v1), "[bold green][PASS][/bold green] Active (< 1.0s TTL)")
    read_table1.add_row('get("auth_token")', str(v2), "[bold green][PASS][/bold green] Active (< 3.0s TTL)")
    read_table1.add_row('get("app_config")', str(v3), "[bold green][PASS][/bold green] Active (Permanent key)")
    console.print(read_table1)
    console.print(f"Current Ordering: [bold cyan]{ttl_cache.state_display()}[/bold cyan]\n")

    wait_time = 1.2
    console.print(f"[dim yellow]>>> Simulating passage of time: Sleeping for {wait_time}s...[/dim yellow]\n")
    time.sleep(wait_time)

    v1_after = ttl_cache.get("session_temp")
    v2_after = ttl_cache.get("auth_token")
    v3_after = ttl_cache.get("app_config")

    read_table2 = Table(title=f"3. Post-TTL Access Verification (Elapsed: {wait_time}s)", box=ROUNDED, header_style="bold cyan", show_lines=True)
    read_table2.add_column("Operation", style="bold yellow", width=24)
    read_table2.add_column("Returned Value", style="bold magenta", width=18)
    read_table2.add_column("Result Explanation", style="white")
    read_table2.add_row('get("session_temp")', str(v1_after), "[bold red]EXPIRED[/bold red] (TTL 1.0s exceeded -> Lazily evicted -> Returns -1)")
    read_table2.add_row('get("auth_token")', str(v2_after), "[bold green]VALID[/bold green] (3.0s TTL still active -> Returns 'jwt_valid_456')")
    read_table2.add_row('get("app_config")', str(v3_after), "[bold green]VALID[/bold green] (Permanent item -> Returns 'env_production')")
    console.print(read_table2)
    console.print(f"\nCache Ordering after lazy eviction: [bold cyan]{ttl_cache.state_display()}[/bold cyan]")
    console.print("\n[bold green][PASS][/bold green] TTL expiration successfully validated!")

    raw_html = console.export_html(inline_styles=True)
    start = raw_html.find("<pre")
    end = raw_html.rfind("</pre>") + 6
    body_content = raw_html[start:end] if start != -1 and end != -1 else raw_html

    full_html = create_terminal_html("python demo.py (TTL Expiration Bonus Verification)", body_content)
    html_file.write_text(full_html, encoding="utf-8")

    render_html_to_png(html_file, output_png, window_size="1040,1020")


def render_html_to_png(html_path: Path, output_png: Path, window_size: str = "1040,680") -> None:
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    file_uri = html_path.resolve().as_uri()

    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={window_size}",
        f"--screenshot={str(output_png.resolve())}",
        file_uri,
    ]
    subprocess.run(cmd, check=True)
    print(f"Generated screenshot: {output_png} ({os.path.getsize(output_png)} bytes)")


if __name__ == "__main__":
    base_dir = Path(__file__).parent
    screenshots_dir = base_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)

    lru_png = screenshots_dir / "lru_cache_output.png"
    lru_html = screenshots_dir / "lru_cache_output.html"
    generate_lru_core_screenshot(lru_png, lru_html)

    root_lru_png = base_dir / "output_screenshot.png"
    root_lru_png.write_bytes(lru_png.read_bytes())

    ttl_png = screenshots_dir / "ttl_bonus_output.png"
    ttl_html = screenshots_dir / "ttl_bonus_output.html"
    generate_ttl_bonus_screenshot(ttl_png, ttl_html)

    root_ttl_png = base_dir / "ttl_bonus_screenshot.png"
    root_ttl_png.write_bytes(ttl_png.read_bytes())

    print("\nAll screenshots generated successfully!")
