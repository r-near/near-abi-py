# NEAR ABI Python

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

ABI Builder for NEAR Python Smart Contracts - generate standardized interface definitions from your Python smart contracts.

## 🔑 Key Features

- Generate ABI schemas from Python NEAR smart contracts
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
# Generate ABI from a contract file
near-abi-py generate example.py

# Generate and save to a specific output file
near-abi-py generate example.py -o example.abi.json

# Validate an existing ABI file
near-abi-py validate contract.abi.json
```

### Library Usage

```python
from near_abi_py import generate_abi, validate_abi

# Generate ABI from a contract file
abi = generate_abi("path/to/contract.py")

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

The resulting ABI can be used by developer tools, IDEs, and frontends to:

- Understand contract interfaces
- Generate client-side bindings
- Type-check interactions with the contract
- Document the contract's capabilities

## 🔧 CLI Reference

```
near-abi-py [COMMAND] [OPTIONS]

Commands:
  generate    Generate ABI from a contract file
  validate    Validate an existing ABI file

Options for 'generate':
  --output, -o    Output file path (default: stdout)
  --validate, -v  Validate the generated ABI before output

Options for 'validate':
  (no additional options)

General options:
  --help          Show this help message
  --version       Show version information
```

## 📚 Library API

### `generate_abi(contract_file: str, package_path: Optional[str] = None) -> Dict[str, Any]`

Analyzes a Python contract file and generates the corresponding ABI.

**Parameters:**

- `contract_file`: Path to the Python contract file
- `package_path`: Optional path to the package information file (e.g., pyproject.toml)

**Returns:**

- ABI definition as a dictionary

### `validate_abi(abi: Dict[str, Any]) -> List[str]`

Validates an ABI against the official schema.

**Parameters:**

- `abi`: The ABI to validate (dictionary)

**Returns:**

- List of validation error messages (empty if valid)

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
      "builder": "near-sdk-py 0.3.0"
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

# Generate the ABI
near-abi-py generate contract.py -o contract.abi.json

# Deploy the contract (example)
near deploy myaccount.testnet contract.wasm
```

## 📝 Contributing

Contributions are welcome! Feel free to submit a Pull Request with bug fixes, improvements, or new features.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
