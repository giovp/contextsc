"""Formatting utilities for presenting documentation to LLMs."""

from .introspector import FunctionInfo


def estimate_token_count(text: str) -> int:
    """Estimate token count for text.

    Uses a simple heuristic: ~4 characters per token.

    Parameters
    ----------
    text : str
        Text to estimate tokens for.

    Returns
    -------
    int
        Estimated token count.
    """
    return len(text) // 4


def format_function_docs(func_info: FunctionInfo, max_tokens: int | None = None) -> str:
    """Format function information for LLM consumption.

    Parameters
    ----------
    func_info : FunctionInfo
        Function information to format.
    max_tokens : int | None, default: None
        Maximum tokens to return. If None, no limit.

    Returns
    -------
    str
        Formatted documentation string.
    """
    # Build the output
    lines = [
        f"# {func_info.name}",
        "",
        f"**Module:** `{func_info.module}`",
        "",
        "## Signature",
        "",
        "```python",
        f"{func_info.name}{func_info.signature}",
        "```",
        "",
    ]

    # Add parameters if available
    if func_info.parameters:
        lines.append("## Parameters")
        lines.append("")
        for param_name, param_type in func_info.parameters.items():
            lines.append(f"- **{param_name}**: `{param_type}`")
        lines.append("")

    # Add return type
    if func_info.return_annotation != "Any":
        lines.append("## Returns")
        lines.append("")
        lines.append(f"`{func_info.return_annotation}`")
        lines.append("")

    # Add docstring
    lines.append("## Documentation")
    lines.append("")
    lines.append(func_info.docstring)

    result = "\n".join(lines)

    # Truncate if needed
    if max_tokens:
        estimated_tokens = estimate_token_count(result)
        if estimated_tokens > max_tokens:
            # Truncate to approximate character count
            char_limit = max_tokens * 4
            result = result[:char_limit] + "\n\n[... truncated due to token limit ...]"

    return result


def format_package_list(packages: list[tuple[str, str, bool]]) -> str:
    """Format list of packages for LLM consumption.

    Parameters
    ----------
    packages : list[tuple[str, str, bool]]
        List of (package_name, version, is_installed) tuples.

    Returns
    -------
    str
        Formatted package list.
    """
    lines = ["# Installed Scverse Packages", ""]

    installed = [p for p in packages if p[2]]
    not_installed = [p for p in packages if not p[2]]

    if installed:
        lines.append("## Available Packages")
        lines.append("")
        for name, version, _ in installed:
            lines.append(f"- **{name}** (v{version})")
        lines.append("")

    if not_installed:
        lines.append("## Not Installed")
        lines.append("")
        for name, _, _ in not_installed:
            lines.append(f"- {name}")
        lines.append("")

    if not installed:
        lines.append("⚠️ No scverse packages are currently installed in this environment.")
        lines.append("")
        lines.append("Install packages with: `pip install <package-name>`")

    return "\n".join(lines)


def format_function_list(module_path: str, functions: list[str]) -> str:
    """Format list of functions in a module.

    Parameters
    ----------
    module_path : str
        Module path.
    functions : list[str]
        List of function names.

    Returns
    -------
    str
        Formatted function list.
    """
    lines = [
        f"# Functions in {module_path}",
        "",
        f"Found {len(functions)} public functions:",
        "",
    ]

    for func in functions:
        lines.append(f"- `{module_path}.{func}`")

    return "\n".join(lines)
