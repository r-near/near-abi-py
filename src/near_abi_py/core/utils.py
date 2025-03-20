"""
Shared utilities for NEAR ABI generation.
"""

from rich.console import Console

# Create a shared console instance
console = Console()

# Flag to control whether we use color output
use_color = True


def configure_console(color_enabled=True):
    """Configure console settings globally"""
    global use_color
    use_color = color_enabled
    console.highlight = color_enabled


def log_success(message):
    """Log a success message"""
    if use_color:
        console.print(f"[bold green]✓[/] {message}")
    else:
        console.print(f"✓ {message}")


def log_error(message):
    """Log an error message"""
    if use_color:
        console.print(f"[bold red]×[/] {message}")
    else:
        console.print(f"× {message}")


def log_info(message):
    """Log an info message"""
    if use_color:
        console.print(f"[bold blue]-[/] {message}")
    else:
        console.print(f"- {message}")


def log_warning(message):
    """Log a warning message"""
    if use_color:
        console.print(f"[bold yellow]![/] {message}")
    else:
        console.print(f"! {message}")
