# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**contextsc** is a BioContextAI MCP (Model Context Protocol) server inspired by Context7, designed specifically for the scverse ecosystem. It is part of the [BioContextAI Registry](https://biocontext.ai/registry), a community-driven catalog of biomedical MCP servers that bridge the gap between LLMs and specialized biomedical knowledge.

This server provides up-to-date, version-specific documentation and code examples for scverse packages (scanpy, anndata, mudata, squidpy, scvi-tools, etc.) directly into LLM prompts.

### Purpose

Solves the problem of LLMs generating outdated or hallucinated code for scverse packages by:
- **Environment-aware introspection**: Only provides documentation for packages installed in the user's environment
- **Python introspection**: Uses `inspect` and `importlib` to extract docstrings directly from installed packages (no web scraping)
- **Version-specific**: Reports actual installed versions using `importlib.metadata`
- **Real API references**: Extracts signatures, parameters, and return types directly from source
- Contributing to the broader BioContextAI ecosystem of composable, interoperable biomedical AI tools

### Scverse Ecosystem

The scverse project is a computational ecosystem for single-cell omics data analysis, including:
- **Core data structures**: anndata, mudata, spatialdata
- **Analysis frameworks**: scanpy, muon, squidpy, scvi-tools, scirpy, pertpy
- **Specialized tools**: rapids-singlecell (GPU-accelerated), SnapATAC2 (ATAC-seq), decoupler (scoring framework)

This MCP server is built with FastMCP and exposes tools that MCP clients can call to retrieve documentation and examples.

## Architecture

### Core Components

- **`src/contextsc/mcp.py`**: Defines the FastMCP instance (`mcp`) that serves as the core server object
- **`src/contextsc/main.py`**: Entry point with Click CLI for running the server with different transports (stdio/http) and environments (development/production)
- **`src/contextsc/tools/`**: MCP tool implementations
  - `_resolve_package.py`: Lists installed scverse packages and their versions
  - `_get_docs.py`: Fetches documentation for specific functions/classes
  - Tools are registered by decorating functions with `@mcp.tool`
- **`src/contextsc/core/`**: Core introspection functionality
  - `package_registry.py`: Registry of 12 core scverse packages (3 data formats, 9 analysis tools)
  - `environment.py`: Detects which packages are installed using `importlib.util.find_spec()`
  - `introspector.py`: Extracts docstrings, signatures, parameters using `inspect` module; includes topic-based search
  - `formatter.py`: Formats documentation with intelligent section-based truncation and topic filtering

### MCP Tools

**`resolve-scverse-package`**: Resolves package names and lists installed packages
- Parameters: `package_name` (optional) - specific package to look up
- Returns: List of all packages with installation status, or details for a specific package

**`get-scverse-docs`**: Fetches documentation from installed packages
- Parameters:
  - `function_path` - dotted path (e.g., `scanpy.pp.normalize_total`, `anndata.AnnData`)
  - `topic` (optional) - keyword for filtering documentation (e.g., 'normalize', 'clustering')
  - `max_tokens` (default: 10000, minimum: 1000) - token limit for response
- Returns: Formatted documentation with signature, parameters, docstring
- Also supports listing functions in a module (e.g., `scanpy.pp` lists all preprocessing functions)
- **Topic filtering modes**:
  - With module path: Searches for functions matching the topic (e.g., `get-scverse-docs("scanpy.pp", topic="normalize")`)
  - With function path: Filters docstring sections by topic (e.g., `get-scverse-docs("scanpy.pp.neighbors", topic="connectivity")`)
- **Intelligent truncation**: Preserves critical sections (signature, parameters) even with low token limits

### How It Works

1. **Package Detection**: On startup or when called, checks which core scverse packages are installed
2. **Dynamic Import**: Only imports packages that are actually available in the environment
3. **Introspection**: Uses `inspect.getdoc()` and `inspect.signature()` to extract documentation
4. **Formatting**: Presents information in markdown format optimized for LLM consumption
5. **Token Management**: Intelligent section-based truncation with priority levels
   - **CRITICAL sections** (always included): Function header, signature, parameters
   - **HIGH priority**: Return type, topic-filtered docstring
   - **MEDIUM priority**: Full docstring, additional sections
   - Enforces minimum 1000 tokens, default 10000 tokens
6. **Topic Filtering**:
   - **Automatic semantic search**: If `contextsc[semsearch]` is installed, automatically uses sentence transformers for intelligent matching
   - **Keyword search fallback**: Falls back to keyword matching if semantic search unavailable
   - **Section-level**: Parses numpy-style docstrings and filters sections by keyword relevance

Example usage flows:
```python
# Basic usage: Get full documentation
# Tool call: get_scverse_docs("scanpy.pp.normalize_total")
# Returns: Full docstring with signature and parameters

# Topic search: Find relevant functions in a module
# Tool call: get_scverse_docs("scanpy.pp", topic="normalize")
# Returns: Top 5 functions matching "normalize" with their documentation
# Note: Uses semantic search automatically if contextsc[semsearch] is installed

# Filtered documentation: Focus on specific aspects
# Tool call: get_scverse_docs("scanpy.pp.neighbors", topic="connectivity")
# Returns: Function docs with only sections mentioning "connectivity"

# Token-limited: Ensure response fits context
# Tool call: get_scverse_docs("scanpy.pp.normalize_total", max_tokens=2000)
# Returns: Intelligently truncated docs preserving critical info
```

### Semantic Search (Optional Enhancement)

Semantic search is **automatically enabled** when installed, providing intelligent function matching:

**Installation**:
```bash
pip install contextsc[semsearch]
```

**What it provides**:
- **Automatic activation**: No configuration needed - just install and it works
- **Conceptual matching**: Finds functions by meaning (e.g., "standardize" matches "normalize", "scale")
- **Synonym awareness**: More flexible than keyword search for related concepts
- **Lightweight**: Uses sentence-transformers model (`all-MiniLM-L6-v2`, ~80MB)

**How it works**:
1. If `contextsc[semsearch]` is installed → automatically uses semantic search
2. If not installed → automatically uses keyword search
3. No user configuration or parameters needed - completely transparent

**When to install**:
- ✅ When searching with natural language queries
- ✅ When looking for functions you don't know the exact name of
- ✅ When exploring unfamiliar modules
- ❌ Skip if you only search by exact function names (keyword search is faster)

### Adding New Tools

To add a new tool:

1. Create a new file in `src/contextsc/tools/` (e.g., `_new_tool.py`)
2. Import `mcp` from `contextsc.mcp`
3. Use helper functions from `contextsc.core` for introspection
4. Decorate your function with `@mcp.tool`
5. Use numpy-style docstrings (required for tool documentation)
6. Export the function in `src/contextsc/tools/__init__.py`

Example:
```python
from contextsc.core import extract_function_info, format_function_docs
from contextsc.mcp import mcp

@mcp.tool
def search_scverse_functions(query: str) -> str:
    """Search for functions matching a query across all installed packages.

    Parameters
    ----------
    query : str
        Search term (e.g., 'normalize', 'cluster').

    Returns
    -------
    str
        List of matching functions with brief descriptions.
    """
    # Implementation using core utilities
    ...
```

## Development Commands

### Python Environment

This project uses a specific Python environment located at:
```
/Users/gpalla/Projects/venv/fastmcp/bin/python
```

Always use this Python interpreter for development tasks (stored in `.python-version`).

### Environment Setup
```bash
# Install with development dependencies
/Users/gpalla/Projects/venv/fastmcp/bin/python -m pip install -e ".[dev]"

# Install with all optional dependencies
/Users/gpalla/Projects/venv/fastmcp/bin/python -m pip install -e ".[dev,doc,test]"

# Install with semantic search support (optional)
/Users/gpalla/Projects/venv/fastmcp/bin/python -m pip install -e ".[semsearch]"

# Setup pre-commit hooks
/Users/gpalla/Projects/venv/fastmcp/bin/python -m pre_commit install
```

### Running the Server
```bash
# Run with stdio transport (default)
contextsc

# Run with HTTP transport on custom port
contextsc --transport http --port 8080 --host 0.0.0.0

# Using environment variables
MCP_TRANSPORT=http MCP_PORT=8080 contextsc
```

### Testing
```bash
# Run all tests
/Users/gpalla/Projects/venv/fastmcp/bin/python -m pytest

# Run with coverage
/Users/gpalla/Projects/venv/fastmcp/bin/python -m coverage run -m pytest
/Users/gpalla/Projects/venv/fastmcp/bin/python -m coverage report

# Run specific test file
/Users/gpalla/Projects/venv/fastmcp/bin/python -m pytest tests/test_core.py -v
/Users/gpalla/Projects/venv/fastmcp/bin/python -m pytest tests/test_tools.py -v

# Run specific test
/Users/gpalla/Projects/venv/fastmcp/bin/python -m pytest tests/test_app.py::test_mcp_server
```

Test organization:
- `tests/test_app.py` - Basic MCP server tests
- `tests/test_core.py` - Core introspection functionality tests (32 tests)
  - Package registry and environment detection
  - Function introspection and documentation extraction
  - Token limit enforcement and intelligent truncation
  - Topic filtering (keyword and semantic search)
  - Semantic search fallback and error handling
  - Numpy docstring parsing
- `tests/test_tools.py` - MCP tool integration tests (6 tests)

### Linting and Formatting
```bash
# Run pre-commit on all files
/Users/gpalla/Projects/venv/fastmcp/bin/python -m pre_commit run --all-files

# Format code with ruff
/Users/gpalla/Projects/venv/fastmcp/bin/python -m ruff format src tests

# Lint with ruff
/Users/gpalla/Projects/venv/fastmcp/bin/python -m ruff check src tests --fix
```

### Documentation
```bash
# Build documentation
hatch run docs:build

# Open documentation in browser
hatch run docs:open

# Clean documentation build
hatch run docs:clean
```

## Code Standards

- **Python version**: Requires Python 3.11+
- **Line length**: 120 characters
- **Docstring style**: NumPy convention (enforced by ruff)
- **Type hints**: Required for all function signatures
- **Import sorting**: Handled by ruff (isort)
- **Linting**: Ruff with extensive rule set (see pyproject.toml)
  - Test files exempt from docstring requirements
  - `__init__.py` files allow unused imports (F401)

## Project Configuration

- Built with **hatchling** as the build backend
- Uses **uv** as the installer (via hatch)
- Test matrix covers Python 3.11, 3.12, and 3.13
- Pre-commit hooks run on both pre-commit and pre-push stages
