"""
Command-line interface for NEAR Python ABI Builder.
"""

import json
import os

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from near_abi_py.generator import generate_abi, generate_abi_from_files
from near_abi_py.utils import find_python_files, validate_abi

# Console for rich output
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
@click.option(
    "--recursive/--no-recursive",
    default=True,
    help="Scan subdirectories recursively (only for directory input)",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Validate the generated ABI against the schema",
)
def generate(source_path, output, recursive, validate):
    """Generate ABI from a Python contract file or directory."""

    try:
        # Check if source is a file or directory
        is_directory = os.path.isdir(source_path)

        if is_directory:
            console.print(f"[bold blue]Scanning directory:[/] {source_path}")

            # Find Python files in directory
            python_files = find_python_files(source_path, recursive=recursive)

            if not python_files:
                console.print("[bold red]Error:[/] No Python files found in directory")
                return 1

            # Display found files
            file_table = Table(title=f"Found {len(python_files)} Python Files")
            file_table.add_column("File", style="cyan")

            for file in python_files:
                rel_path = os.path.relpath(file, source_path)
                file_table.add_row(rel_path)

            console.print(file_table)

            # Generate ABI from all files
            with console.status("[bold green]Analyzing contract files...[/]"):
                abi = generate_abi_from_files(python_files, source_path)

        else:
            # Single file mode
            console.print(f"[bold blue]Analyzing contract:[/] {source_path}")
            with console.status("[bold green]Analyzing contract...[/]"):
                abi = generate_abi(source_path)

        # Display function summary
        display_functions_summary(abi)

        # Validate if requested
        if validate:
            with console.status("[bold green]Validating ABI...[/]"):
                is_valid, messages = validate_abi(abi)

            if not is_valid:
                console.print("[bold red]Validation failed:[/]")
                for msg in messages:
                    console.print(f"  [red]![/] {msg}")
            else:
                console.print("[bold green]✓[/] ABI is valid")

        # Output the ABI
        json_output = json.dumps(abi, indent=2)
        if output:
            with open(output, "w") as f:
                f.write(json_output)
            console.print(f"[bold green]✓[/] ABI written to: {output}")
        else:
            # Print JSON to console in a nicer format
            console.print("\n[bold]Generated ABI:[/]")
            syntax = Syntax(json_output, "json", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, expand=False))

        return 0
    except Exception as e:
        console.print(f"[bold red]Error generating ABI:[/] {str(e)}")
        return 1


@cli.command(help="Validate an existing ABI file against the schema")
@click.argument(
    "abi_file", type=click.Path(exists=True, file_okay=True, dir_okay=False)
)
def validate_command(abi_file):
    """Validate an existing ABI file against the schema."""

    try:
        # Load ABI from file
        console.print(f"[bold blue]Validating ABI file:[/] {abi_file}")
        with open(abi_file, "r") as f:
            abi = json.load(f)

        # Validate against schema
        with console.status("[bold green]Validating ABI...[/]"):
            is_valid, messages = validate_abi(abi)

        if not is_valid:
            console.print("[bold red]Validation failed:[/]")
            for msg in messages:
                console.print(f"  [red]![/] {msg}")
            return 1
        else:
            console.print("[bold green]✓ ABI is valid[/]")

            # Display a summary of the ABI
            metadata = abi.get("metadata", {})
            functions = abi.get("body", {}).get("functions", [])

            metadata_table = Table(title="ABI Metadata")
            metadata_table.add_column("Property", style="cyan")
            metadata_table.add_column("Value", style="green")

            for key, value in metadata.items():
                if key != "build" and key != "sources":
                    metadata_table.add_row(key, str(value))

            console.print(metadata_table)
            console.print(f"[bold]Found {len(functions)} contract functions[/]")

            return 0
    except json.JSONDecodeError:
        console.print("[bold red]Error:[/] The file is not valid JSON")
        return 1
    except Exception as e:
        console.print(f"[bold red]Error validating ABI file:[/] {str(e)}")
        return 1


def display_functions_summary(abi: dict) -> None:
    """
    Display a summary of the functions in the ABI.

    Args:
        abi: The ABI to display
    """
    functions = abi.get("body", {}).get("functions", [])
    if not functions:
        console.print("[yellow]No contract functions found in the source.[/]")
        return

    table = Table(title="Contract Functions")
    table.add_column("Function", style="cyan")
    table.add_column("Kind", style="green")
    table.add_column("Modifiers", style="magenta")
    table.add_column("Parameters", style="yellow")
    table.add_column("Return Type", style="blue")

    for func in functions:
        name = func["name"]
        kind = func["kind"]

        # Get modifiers
        modifiers = func.get("modifiers", [])
        mod_str = ", ".join(modifiers) if modifiers else "-"

        # Get parameters
        params = func.get("params", {}).get("args", [])
        param_str = ", ".join(p["name"] for p in params) if params else "-"

        # Get return type
        result = func.get("result")
        if result:
            schema = result.get("type_schema", {})
            if isinstance(schema, dict):
                result_type = schema.get("type", "?")
            else:
                result_type = str(schema)
        else:
            result_type = "-"

        table.add_row(name, kind, mod_str, param_str, result_type)

    console.print(table)


def main():
    """Entry point for the command-line interface."""
    return cli()
