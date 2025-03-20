# NEAR ABI Python

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An ultra-minimalist tool for generating Application Binary Interface (ABI) definitions for NEAR smart contracts written in Python.

## 🔑 Key Features

- ✨ **Simple**: Ultra-minimalist design, easy to use and understand
- 🔍 **Auto-detection**: Automatically detects NEAR contract functions and their types
- 📊 **Beautiful CLI**: Rich text interface with color-coded output and tables
- 📄 **Validation**: Built-in ABI validation against the official schema
- 📂 **Multi-file support**: Analyze entire directories of Python contract files
- 🧩 **Metadata extraction**: Automatically extracts project metadata from config files

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
from near_abi_py.analyzer.loader import ModuleLoader
loader = ModuleLoader()
python_files = loader.find_python_files("path/to/project_dir")
abi = generate_abi_from_files(python_files, "path/to/project_dir")

# Validate the generated ABI
from near_abi_py.core.schema import SchemaManager
schema_manager = SchemaManager()
is_valid, messages = schema_manager.validate_abi(abi)

if is_valid:
    print("ABI is valid!")
else:
    print("ABI has issues:", messages)
```

## 📘 How It Works

NEAR ABI Python analyzes Python smart contract files by:

1. Identifying functions marked with NEAR decorators (`@view`, `@call`, `@init`, etc.)
2. Extracting parameter types and return types using Pydantic type adapters
3. Generating JSON Schema representations of each parameter and return type
4. Creating a standardized ABI schema following NEAR's specifications
5. Validating the schema against the official metaschema

For multi-file projects:

1. The tool scans the entire directory for Python files
2. It analyzes each file for contract functions
3. Functions from all files are combined into a single comprehensive ABI
4. Project metadata is extracted from configuration files like pyproject.toml

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
  --recursive / --no-recursive   Scan subdirectories recursively (only for
                                directory input)
  --validate / --no-validate     Validate the generated ABI against the schema
  --no-color                     Disable colored output
  --help                         Show this message and exit.
```

### Validate Command

```
Usage: near-abi-py validate [OPTIONS] ABI_FILE

  Validate an existing ABI file against the schema.

Options:
  --no-color  Disable colored output
  --help      Show this message and exit.
```

## 📚 Library API

### Core Functions

```python
generate_abi(contract_file: str) -> Dict[str, Any]
```
Analyzes a single Python contract file and generates the corresponding ABI.

```python
generate_abi_from_files(file_paths: List[str], project_dir: str) -> Dict[str, Any]
```
Generates an ABI from multiple Python files in a project directory.

### Helper Classes

```python
ModuleLoader()
```
Provides utilities for loading Python modules and finding Python files.

```python
SchemaManager()
```
Handles JSON Schema creation and validation for NEAR ABI.

```python
FunctionAnalyzer()
```
Analyzes and extracts ABI information from Python functions.

```python
MetadataExtractor()
```
Extracts metadata from project files like pyproject.toml.

## 🧠 Understanding NEAR ABI Format

The generated ABI follows [NEAR's ABI specification](https://github.com/near/NEPs/pull/451) and includes:

- Contract metadata (name, version, authors)
- Function definitions (name, parameters, return types)
- Function modifiers (view, call, init, etc.)
- Type information in JSON Schema format

Example of a generated ABI:

```json
{
  "schema_version": "0.4.0",
  "metadata": {
    "name": "greeting",
    "version": "0.1.0",
    "authors": ["Example Author"],
    "build": {
      "compiler": "python 3.11.5",
      "builder": "near-abi-py"
    }
  },
  "body": {
    "functions": [
      {
        "name": "get_greeting",
        "kind": "view",
        "params": {
          "serialization_type": "json",
          "args": []
        },
        "result": {
          "serialization_type": "json",
          "type_schema": {
            "type": "string"
          }
        }
      },
      {
        "name": "set_greeting",
        "kind": "call",
        "params": {
          "serialization_type": "json",
          "args": [
            {
              "name": "message",
              "type_schema": {
                "type": "string"
              }
            }
          ]
        }
      }
    ],
    "root_schema": {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "title": "NEAR Contract Schema",
      "definitions": {
        "AccountId": {
          "type": "string",
          "description": "NEAR account identifier"
        }
        // Additional NEAR types...
      }
    }
  }
}
```

## 🧠 Working with Multi-file Projects

NEAR ABI Python supports analyzing multi-file NEAR contract projects. When a directory is provided instead of a single file, the tool:

1. Scans for all Python files in the directory (recursively by default)
2. Analyzes each file for NEAR contract functions
3. Combines all discovered functions into a single comprehensive ABI
4. Automatically detects project metadata from pyproject.toml or similar files

This is especially useful for larger contracts split across multiple files or when your contract depends on local modules.

## 🔄 Integration with NEAR Tools

NEAR ABI Python complements the following tools in the NEAR Python ecosystem:

- **near-sdk-py**: The Python SDK for writing NEAR smart contracts
- **nearc**: The Python-to-WebAssembly compiler for NEAR smart contracts

While the SDK provides the framework for writing contracts and the compiler turns them into WebAssembly, NEAR ABI Python creates the interface definitions needed for external tools to interact with your contract.

## 💼 Use Cases

- Generate and share contract interfaces with frontend developers
- Enable IDE autocompletion and type checking for contract interactions
- Document your contract API in a standard format
- Validate contract implementations against interface specifications
- Support cross-language contract development and interaction
- Analyze complex, multi-file NEAR contract projects

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

# These exports make functions available to the NEAR runtime
new = contract.new
set_greeting = contract.set_greeting
get_greeting = contract.get_greeting
```

## 🧩 Project Structure

The codebase is organized into logical modules:

```
near_abi_py/
├── __init__.py               # Package exports and version
├── abi_schema.json           # JSON Schema for ABI validation
├── cli/
│   ├── __init__.py           # CLI entry points
│   └── commands.py           # Click command implementations
├── core/
│   ├── __init__.py           # Core module exports
│   ├── constants.py          # Schema versions and constants
│   ├── metadata.py           # Project metadata extraction
│   ├── schema.py             # JSON Schema generation utilities
│   ├── types.py              # Type definitions for ABI
│   └── utils.py              # Shared utilities and console
├── analyzer/
│   ├── __init__.py           # Function extraction exports
│   ├── function.py           # Function processing
│   ├── inspector.py          # Function inspection and decorator detection
│   └── loader.py             # Module loading utilities
└── generator/
    ├── __init__.py           # Generator exports
    └── builder.py            # Main ABI builder logic
```

## 📝 Contributing

Contributions are welcome! Feel free to submit a Pull Request with bug fixes, improvements, or new features.

## 📦 Dependencies

- Python 3.8+
- pydantic >= 2.0.0
- click >= 8.0.0
- jsonschema >= 4.0.0 
- rich >= 10.0.0

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.