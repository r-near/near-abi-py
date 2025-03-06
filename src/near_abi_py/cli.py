#!/usr/bin/env python3
"""
Command-line interface for the NEAR Python ABI Builder.

This module provides a CLI using Click and Rich with support for
multi-file project directories.
"""

import json
import sys
import os

import click
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from .generator import generate_abi_from_files, generate_abi
from .schema import validate_abi
from .scanner import find_python_files


# Create Rich console
console = Console()


@click.group(help="NEAR Python ABI Builder")
@click.version_option(package_name="near-abi-py")
def cli():
    """Main CLI entry point."""
    pass


@cli.command(help="Generate ABI from a contract file or directory")
@click.argument("source_path", type=click.Path(exists=True))
@click.option(
    "--output", "-o", type=click.Path(), help="Output file path (default: stdout)"
)
@click.option("--validate", "-v", is_flag=True, help="Validate the generated ABI")
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Scan subdirectories recursively (only for directory input)",
)
@click.option(
    "--respect-gitignore/--ignore-gitignore",
    default=True,
    help="Respect .gitignore patterns (only for directory input)",
)
def generate(source_path, output, validate, recursive, respect_gitignore):
    """Generate ABI from a Python contract file or directory."""
    try:
        # Check if source is a file or directory
        is_directory = os.path.isdir(source_path)

        if is_directory:
            console.print(f"[bold blue]Scanning directory:[/] {source_path}")

            # Find Python files in directory
            python_files = find_python_files(
                source_path, recursive=recursive, respect_gitignore=respect_gitignore
            )

            if not python_files:
                console.print("[bold red]Error:[/] No Python files found in directory")
                return 1

            # Display found files
            file_tree = Tree(f"[bold]Found {len(python_files)} Python files:[/]")
            for file in python_files:
                rel_path = os.path.relpath(file, source_path)
                file_tree.add(f"[blue]{rel_path}[/]")
            console.print(file_tree)

            # Generate ABI from all files
            console.print("[bold blue]Analyzing contract files...[/]")
            abi = generate_abi_from_files(python_files, source_path)

        else:
            # Single file mode
            console.print(f"[bold blue]Analyzing contract:[/] {source_path}")
            abi = generate_abi(source_path)

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

        # Display functions summary
        functions = abi["body"]["functions"]
        if functions:
            table = Table(title="Contract Functions")
            table.add_column("Function", style="cyan")
            table.add_column("Kind", style="green")
            table.add_column("Parameters", style="yellow")

            for func in functions:
                name = func["name"]
                kind = func["kind"]
                params = func.get("params", {}).get("args", [])
                param_str = ", ".join(p["name"] for p in params) if params else "-"
                table.add_row(name, kind, param_str)

            console.print(table)

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


@cli.command(help="List Python files in a directory that would be scanned")
@click.argument(
    "directory", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--recursive/--no-recursive", default=True, help="Scan subdirectories recursively"
)
@click.option(
    "--respect-gitignore/--ignore-gitignore",
    default=True,
    help="Respect .gitignore patterns",
)
def scan(directory, recursive, respect_gitignore):
    """Scan and list Python files in a directory."""
    try:
        console.print(f"[bold blue]Scanning directory:[/] {directory}")

        python_files = find_python_files(
            directory, recursive=recursive, respect_gitignore=respect_gitignore
        )

        if not python_files:
            console.print("[bold yellow]No Python files found in directory[/]")
            return 0

        # Display found files
        console.print(f"[bold green]Found {len(python_files)} Python files:[/]")

        file_tree = Tree(f"[bold]{directory}[/]")

        # Sort files for better tree structure
        python_files.sort()

        for file in python_files:
            rel_path = os.path.relpath(file, directory)
            parts = rel_path.split(os.path.sep)

            # Create tree structure
            current = file_tree
            for i, part in enumerate(parts[:-1]):
                # Find or create node
                found = False
                for child in current.children:
                    if child.label == f"[bold blue]{part}/[/]":
                        current = child
                        found = True
                        break

                if not found:
                    current = current.add(f"[bold blue]{part}/[/]")

            # Add file leaf
            current.add(f"[green]{parts[-1]}[/]")

        console.print(file_tree)

        return 0
    except Exception as e:
        console.print(f"[bold red]Error scanning directory:[/] {str(e)}")
        return 1


def main():
    """Entry point for the command-line interface."""
    return cli()


if __name__ == "__main__":
    sys.exit(main())
