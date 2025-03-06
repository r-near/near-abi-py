# NEAR ABI Python

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ABI Builder for NEAR Python Smart Contracts - generate standardized interface definitions from your Python smart contracts.

## 🔑 Key Features

- Generate ABI schemas from Python NEAR smart contracts
- **Support for multi-file projects and directory scanning**
- Validate existing ABI definitions against the official schema
- Command-line interface for easy integration into build processes
- Usable as a library in your Python projects
- Support for NEP-compatible contract analysis
- Rich output formatting for better readability

## 📦 Installation

```bash
# Install with pip
pip install near-abi-py

# Install with uv
uv pip install near-abi-py

# Or use directly without installing (recommended)
uvx near-abi-py generate example.py
```

## 🚀 Quick Start

### CLI Usage

```bash
# Generate ABI from a single contract file
near-abi-py generate example.py

# Generate ABI from a project directory
near-abi-py generate ./my_contract_project/

# Scan and list Python files in a directory
near-abi-py scan ./my_contract_project/

# Generate and save to a specific output file
near-abi-py generate example.py -o example.abi.json

# Validate an existing ABI file
near-abi-py validate contract.abi.json
```

### Library Usage

```python
from near_abi_py import generate_abi, generate_abi_from_files, validate_abi, find_python_files

# Generate ABI from a single contract file
abi = generate_abi("path/to/contract.py")

# Or generate ABI from multiple files
python_files = find_python_files("path/to/project_dir")
abi = generate_abi_from_files(python_files, "path/to/project_dir")

# Validate the generated ABI
validation_messages = validate_abi(abi)
if not validation_messages:
    print("ABI is valid!")
else:
    print("ABI has issues:", validation_messages)
```

## 📘 How It Works

NEAR ABI Python analyzes Python smart contract files by:

1. Parsing the contract's AST (Abstract Syntax Tree)
2. Identifying functions marked with NEAR decorators (`@view`, `@call`, `@init`)
3. Extracting parameter types and return types
4. Generating a standardized ABI schema following NEAR's specifications
5. Validating the schema against the official metaschema

For multi-file projects:

1. The tool scans the entire directory for Python files
2. It analyzes each file for contract functions
3. Functions from all files are combined into a single comprehensive ABI
4. The tool automatically identifies likely main contract files

The resulting ABI can be used by developer tools, IDEs, and frontends to:

- Understand contract interfaces
- Generate client-side bindings
- Type-check interactions with the contract
- Document the contract's capabilities

## 🔧 CLI Reference

```
near-abi-py [COMMAND] [OPTIONS]

Commands:
  generate    Generate ABI from a contract file or directory
  validate    Validate an existing ABI file
  scan        List Python files in a directory that would be scanned

Options for 'generate':
  --output, -o               Output file path (default: stdout)
  --validate, -v             Validate the generated ABI before output
  --recursive/--no-recursive Scan subdirectories recursively (default: recursive)
  --respect-gitignore/--ignore-gitignore
                           Respect .gitignore patterns (default: respect)

Options for 'scan':
  --recursive/--no-recursive Scan subdirectories recursively (default: recursive)
  --respect-gitignore/--ignore-gitignore
                           Respect .gitignore patterns (default: respect)

General options:
  --help                    Show this help message
  --version                 Show version information
```

## 📚 Library API

### `generate_abi(contract_file: str, package_path: Optional[str] = None) -> Dict[str, Any]`

Analyzes a single Python contract file and generates the corresponding ABI.

**Parameters:**

- `contract_file`: Path to the Python contract file
- `package_path`: Optional path to the package information file (e.g., pyproject.toml)

**Returns:**

- ABI definition as a dictionary

### `generate_abi_from_files(file_paths: List[str], project_dir: str) -> Dict[str, Any]`

Generates an ABI from multiple Python files in a project directory.

**Parameters:**

- `file_paths`: List of Python file paths to analyze
- `project_dir`: Root directory of the project

**Returns:**

- ABI definition as a dictionary

### `find_python_files(directory: str, recursive: bool = True, respect_gitignore: bool = True) -> List[str]`

Finds all Python files in a directory, optionally respecting .gitignore patterns.

**Parameters:**

- `directory`: Path to the directory to scan
- `recursive`: Whether to scan subdirectories recursively
- `respect_gitignore`: Whether to respect .gitignore patterns

**Returns:**

- List of paths to Python files

### `scan_project(project_path: str, recursive: bool = True, respect_gitignore: bool = True) -> Dict[str, Any]`

Scans a project directory and analyzes its structure.

**Parameters:**

- `project_path`: Path to the project directory
- `recursive`: Whether to scan subdirectories recursively
- `respect_gitignore`: Whether to respect .gitignore patterns

**Returns:**

- Dictionary with project analysis results

### `validate_abi(abi: Dict[str, Any]) -> List[str]`

Validates an ABI against the official schema.

**Parameters:**

- `abi`: The ABI to validate (dictionary)

**Returns:**

- List of validation error messages (empty if valid)

## 🧠 Working with Multi-file Projects

NEAR ABI Python now supports analyzing multi-file NEAR contract projects. When a directory is provided instead of a single file, the tool:

1. Scans for all Python files in the directory (recursively by default)
2. Respects .gitignore patterns (if pathspec is installed)
3. Analyzes each file for NEAR contract functions
4. Combines all discovered functions into a single comprehensive ABI
5. Automatically detects project metadata from pyproject.toml if available

This is especially useful for larger contracts split across multiple files or when your contract depends on local modules.

### Example Multi-file Project Structure

```
my_near_contract/
  ├── pyproject.toml
  ├── contract.py           # Main contract entry points
  ├── models/
  │   ├── __init__.py
  │   ├── account.py        # Account-related functions
  │   └── token.py          # Token-related functions
  └── utils/
      ├── __init__.py
      └── helpers.py        # Helper functions
```

When running:

```bash
near-abi-py generate my_near_contract/
```

The tool will scan all Python files in the project and combine all NEAR-decorated functions (@view, @call, @init) into a single ABI.

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
- **Analyze complex, multi-file NEAR contract projects**

## 🧩 Examples

### Example Contract

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

### Generate ABI in a Build Process

```bash
#!/bin/bash
# build.sh

# Compile the contract
nearc contract.py

# Generate the ABI (works with directories too)
near-abi-py generate ./src/ -o contract.abi.json

# Deploy the contract (example)
near deploy myaccount.testnet contract.wasm
```

## 📝 Contributing

Contributions are welcome! Feel free to submit a Pull Request with bug fixes, improvements, or new features.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
