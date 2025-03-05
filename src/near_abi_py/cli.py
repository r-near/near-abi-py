#!/usr/bin/env python3
"""
Simplified command-line interface for the NEAR Python ABI Builder.

This module provides a streamlined CLI using Click and Rich.
"""

import json
import sys

import click
from rich.console import Console
from rich.syntax import Syntax

from .generator import generate_abi
from .schema import validate_abi


# Create Rich console
console = Console()


@click.group(help="NEAR Python ABI Builder")
@click.version_option(package_name="near-abi-py")
def cli():
    """Main CLI entry point."""
    pass


@cli.command(help="Generate ABI from a contract file")
@click.argument(
    "contract_file", type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output file path (default: stdout)"
)
@click.option("--validate", "-v", is_flag=True, help="Validate the generated ABI")
def generate(contract_file, output, validate):
    """Generate ABI from a Python contract file."""
    try:
        console.print(f"[bold blue]Analyzing contract:[/] {contract_file}")
        abi = generate_abi(contract_file)

        # Validate if requested
        if validate:
            console.print("[bold blue]Validating ABI...[/]")
            messages = validate_abi(abi)
            if messages:
                console.print("[bold yellow]Validation results:[/]")
                for msg in messages:
                    console.print(f"  [bold yellow]![/] {msg}")
                console.print()
            else:
                console.print("[bold green]✓ ABI is valid[/]\n")

        # Output the ABI
        json_output = json.dumps(abi, indent=2)
        if output:
            with open(output, "w") as f:
                f.write(json_output)
            console.print(f"[bold green]✓ ABI written to:[/] {output}")
        else:
            # Pretty print JSON to console
            console.print("[bold blue]Generated ABI:[/]")
            syntax = Syntax(json_output, "json", theme="monokai", line_numbers=True)
            console.print(syntax)

        return 0
    except Exception as e:
        console.print(f"[bold red]Error generating ABI:[/] {str(e)}")
        return 1


@cli.command(help="Validate an ABI file")
@click.argument(
    "abi_file", type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
def validate(abi_file):
    """Validate an existing ABI file."""
    try:
        with open(abi_file, "r") as f:
            abi = json.load(f)

        console.print(f"[bold blue]Validating ABI file:[/] {abi_file}")
        messages = validate_abi(abi)

        if messages:
            console.print("[bold yellow]Validation results:[/]")
            for msg in messages:
                if msg.startswith("Error"):
                    console.print(f"  [bold red]×[/] {msg}")
                else:
                    console.print(f"  [bold yellow]![/] {msg}")
            return 1 if any(msg.startswith("Error") for msg in messages) else 0
        else:
            console.print("[bold green]✓ ABI is valid[/]")
            return 0
    except json.JSONDecodeError:
        console.print("[bold red]Error:[/] The file is not valid JSON")
        return 1
    except Exception as e:
        console.print(f"[bold red]Error validating ABI file:[/] {str(e)}")
        return 1


def main():
    """Entry point for the command-line interface."""
    return cli()


if __name__ == "__main__":
    sys.exit(main())
