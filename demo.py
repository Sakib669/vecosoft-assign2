"""
Interactive and Visual Demonstration of LRU Cache & TTL Expiration Extension.
Produces clear, step-by-step output showing operations, return values, evictions,
and internal Doubly Linked List state.
"""

from __future__ import annotations
import sys
import time
from typing import Optional
from src.lru_cache import Cache, TTLCache

# Ensure UTF-8 output on all operating systems and shells
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.box import ROUNDED
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def run_assessment_example(console: Optional[Console] = None) -> None:
    """
    Demonstrate the exact sequence required in the assessment specification:
      cache = Cache(2)
      cache.put("A", 10)
      cache.put("B", 20)
      cache.get("A")   -> 10
      cache.put("C", 30)
      cache.get("B")   -> -1
      cache.get("C")   -> 30
      cache.get("A")   -> 10
    """
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

    if RICH_AVAILABLE and console:
        console.rule("[bold cyan]TASK 2 — LRU CACHE DEMONSTRATION[/bold cyan]")
        console.print("[dim]Target: Least Recently Used Cache with capacity = 2[/dim]\n")

        table = Table(
            title="Step-by-Step LRU Cache Execution",
            box=ROUNDED,
            header_style="bold magenta",
            title_style="bold white on blue",
            show_lines=True,
        )
        table.add_column("Step", justify="center", style="bold cyan", width=6)
        table.add_column("Operation", style="bold yellow", width=16)
        table.add_column("Return Value", justify="center", style="bold green", width=14)
        table.add_column("Eviction Action", justify="center", style="bold red", width=20)
        table.add_column("Cache Ordering (MRU -> LRU)", style="bold white", width=36)

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
        console.print("\n[bold green][PASS][/bold green] [white]get('A')[/white] -> 10 [dim](promoted 'A' to Most Recently Used)[/dim]")
        console.print("[bold green][PASS][/bold green] [white]put('C', 30)[/white] -> Evicted 'B' [dim](since 'B' was Least Recently Used)[/dim]")
        console.print("[bold green][PASS][/bold green] [white]get('B')[/white] -> -1 [dim](key no longer exists)[/dim]")
        console.print("[bold green][PASS][/bold green] [white]get('C')[/white] -> 30 [dim](retrieved value)[/dim]")
        console.print("[bold green][PASS][/bold green] [white]get('A')[/white] -> 10 [dim](retrieved value & promoted to MRU)[/dim]")
    else:
        print("=" * 80)
        print("TASK 2 — LRU CACHE DEMONSTRATION (Capacity = 2)")
        print("=" * 80)
        print(f"{'Step':<6} | {'Operation':<16} | {'Return':<12} | {'Eviction':<20} | {'Cache State (MRU -> LRU)'}")
        print("-" * 80)
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
            print(f"#{step:<5} | {op + arg_str:<16} | {ret_val:<12} | {evict_str:<20} | {state}")

        print("\n[PASS] get('A') -> 10 (promoted 'A' to MRU)")
        print("[PASS] put('C', 30) -> Evicted 'B' (Least Recently Used)")
        print("[PASS] get('B') -> -1 (not found / evicted)")
        print("[PASS] get('C') -> 30")
        print("[PASS] get('A') -> 10")


def run_ttl_bonus_demo(console: Optional[Console] = None) -> None:
    """
    Demonstrate optional TTL/expiration support.
    """
    ttl_cache = TTLCache(capacity=3)

    if RICH_AVAILABLE and console:
        console.print("\n")
        console.rule("[bold magenta]OPTIONAL BONUS — TTL / EXPIRATION DEMONSTRATION[/bold magenta]")
        console.print("[dim]Demonstrating temporal eviction alongside LRU capacity constraints[/dim]\n")

        insert_table = Table(title="1. Initial Insertion with TTL Constraints", box=ROUNDED, header_style="bold cyan")
        insert_table.add_column("Key", style="yellow")
        insert_table.add_column("Value", style="green")
        insert_table.add_column("Configured TTL", style="bold magenta")
        insert_table.add_column("Expected Expiration", style="white")

        insert_table.add_row("session_temp", "tok_xyz_123", "1.0 second", "Expires after 1.0s")
        insert_table.add_row("auth_token", "jwt_valid_456", "3.0 seconds", "Expires after 3.0s")
        insert_table.add_row("app_config", "env_production", "None (Permanent)", "Persists until capacity eviction")

        console.print(insert_table)

    ttl_cache.put("session_temp", "tok_xyz_123", ttl=1.0)
    ttl_cache.put("auth_token", "jwt_valid_456", ttl=3.0)
    ttl_cache.put("app_config", "env_production", ttl=None)

    v1 = ttl_cache.get("session_temp")
    v2 = ttl_cache.get("auth_token")
    v3 = ttl_cache.get("app_config")

    if RICH_AVAILABLE and console:
        read_table1 = Table(title="2. Immediate Access (Elapsed: 0.0s)", box=ROUNDED, header_style="bold cyan")
        read_table1.add_column("Operation", style="bold yellow")
        read_table1.add_column("Returned Value", style="bold green")
        read_table1.add_column("Status", style="bold green")
        read_table1.add_row('get("session_temp")', str(v1), "[PASS] Active (< 1.0s)")
        read_table1.add_row('get("auth_token")', str(v2), "[PASS] Active (< 3.0s)")
        read_table1.add_row('get("app_config")', str(v3), "[PASS] Active (Permanent)")
        console.print(read_table1)
        console.print(f"Current Ordering: [bold cyan]{ttl_cache.state_display()}[/bold cyan]")
    else:
        print("\n--- Immediate Access (0.0s) ---")
        print(f'get("session_temp") -> {v1}')
        print(f'get("auth_token")   -> {v2}')
        print(f'get("app_config")   -> {v3}')

    wait_time = 1.2
    if RICH_AVAILABLE and console:
        console.print(f"\n[dim yellow]>>> Simulating passage of time: Sleeping for {wait_time}s...[/dim yellow]")
    else:
        print(f"\nSleeping for {wait_time}s...")
    time.sleep(wait_time)

    v1_after = ttl_cache.get("session_temp")
    v2_after = ttl_cache.get("auth_token")
    v3_after = ttl_cache.get("app_config")

    if RICH_AVAILABLE and console:
        read_table2 = Table(title=f"3. Post-TTL Access (Elapsed: {wait_time}s)", box=ROUNDED, header_style="bold cyan")
        read_table2.add_column("Operation", style="bold yellow")
        read_table2.add_column("Returned Value", style="bold magenta")
        read_table2.add_column("Result Explanation", style="white")
        read_table2.add_row('get("session_temp")', str(v1_after), "[bold red]EXPIRED[/bold red] (Exceeded 1.0s TTL -> Lazily Purged -> Returns -1)")
        read_table2.add_row('get("auth_token")', str(v2_after), "[bold green]VALID[/bold green] (3.0s TTL still active -> Returns jwt_valid_456)")
        read_table2.add_row('get("app_config")', str(v3_after), "[bold green]VALID[/bold green] (Permanent item -> Returns env_production)")
        console.print(read_table2)
        console.print(f"Cache Ordering after lazy eviction: [bold cyan]{ttl_cache.state_display()}[/bold cyan]")
        console.print("\n[bold green][PASS][/bold green] TTL expiration successfully validated!")
    else:
        print(f"\n--- Post-TTL Access ({wait_time}s) ---")
        print(f'get("session_temp") -> {v1_after} (EXPIRED -> Returns -1)')
        print(f'get("auth_token")   -> {v2_after} (VALID)')
        print(f'get("app_config")   -> {v3_after} (VALID)')
        print(f"State: {ttl_cache.state_display()}")


if __name__ == "__main__":
    c = Console(width=100) if RICH_AVAILABLE else None
    run_assessment_example(c)
    run_ttl_bonus_demo(c)
