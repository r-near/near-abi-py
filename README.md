# NEAR ABI Python

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight tool for generating Application Binary Interface (ABI) definitions for NEAR smart contracts written in Python.

## 🔑 Key Features

- ✨ **Simple**: Minimalist design with a focus on usability
- 🔍 **Auto-detection**: Automatically detects NEAR contract functions and their types
- 📊 **Beautiful CLI**: Rich text interface with color-coded output
- 📄 **Validation**: Built-in ABI validation against the official schema
- 📂 **Multi-file support**: Analyze entire directories of Python contract files

## 📦 Installation

```bash
# Install with pip
pip install near-abi-py

# Install with uv
uv pip install near-abi-py

# Or use directly without installing
python -m near_abi_py generate example.py
```

## 🚀 Quick Start

### CLI Usage

```bash
# Generate ABI from a single contract file
near-abi-py generate example.py

# Generate ABI from a project directory
near-abi-py generate ./my_contract_project/

# Generate and save to a specific output file
near-abi-py generate example.py -o example.abi.json

# Validate an existing ABI file
near-abi-py validate contract.abi.json
```

### Library Usage

```python
from near_abi_py import generate_abi, generate_abi_from_files

# Generate ABI from a single contract file
abi = generate_abi("path/to/contract.py")

# Or generate ABI from multiple files
python_files = ["path/to/file1.py", "path/to/file2.py"]
abi = generate_abi_from_files(python_files, "path/to/project_dir")

# Validate the generated ABI
from near_abi_py.utils import validate_abi
is_valid, messages = validate_abi(abi)

if is_valid:
    print("ABI is valid!")
else:
    print("ABI has issues:", messages)
```

## 📘 How It Works

NEAR ABI Python analyzes Python smart contract files by:

1. Identifying functions marked with NEAR decorators (`@view`, `@call`, `@init`, etc.)
2. Extracting parameter types and return types using Python type hints
3. Generating JSON Schema representations of each parameter and return type
4. Creating a standardized ABI schema following NEAR's specifications
5. Validating the output against the official ABI schema

## 🔧 CLI Reference

```
Usage: near-abi-py [OPTIONS] COMMAND [ARGS]...

  NEAR Python ABI Builder

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  generate  Generate ABI from a contract file or directory
  validate  Validate an existing ABI file against the schema
```

### Generate Command

```
Usage: near-abi-py generate [OPTIONS] SOURCE_PATH

  Generate ABI from a Python contract file or directory.

Options:
  -o, --output FILE              Output file path (default: stdout)
  --recursive / --no-recursive   Scan subdirectories recursively (default: True)
  --validate / --no-validate     Validate the generated ABI (default: True)
  --help                         Show this message and exit.
```

### Validate Command

```
Usage: near-abi-py validate [OPTIONS] ABI_FILE

  Validate an existing ABI file against the schema.

Options:
  --help      Show this message and exit.
```

## 🧩 Example Contract

```python
from near_sdk_py import view, call, init, Context, Storage, Log

class GreetingContract:
    @init
    def new(self, owner_id=None):
        """Initialize the contract with optional owner"""
        owner = owner_id or Context.predecessor_account_id()
        Storage.set("owner", owner)
        Log.info(f"Contract initialized by {owner}")
        return True

    @call
    def set_greeting(self, message):
        """Store a greeting message (requires gas)"""
        Storage.set("greeting", message)
        return f"Greeting updated to: {message}"

    @view
    def get_greeting(self):
        """Retrieve the greeting message (free, no gas needed)"""
        return Storage.get_string("greeting") or "Hello, NEAR world!"

# Export the contract methods
contract = GreetingContract()
new = contract.new
set_greeting = contract.set_greeting
get_greeting = contract.get_greeting
```

## 🧠 Understanding NEAR ABI Format

The generated ABI follows [NEAR's ABI specification](https://github.com/near/NEPs/pull/451) and includes:

- Contract metadata (name, version, authors)
- Function definitions (name, parameters, return types)
- Function modifiers (view, call, init, etc.)
- Type information in JSON Schema format

## 📦 Dependencies

- Python 3.12+
- pydantic >= 2.10.6
- click >= 8.1.8
- jsonschema >= 4.23.0 
- rich >= 13.9.4

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.