"""Tool for searching functions across the scverse ecosystem."""

from contextsc.core import (
    get_installed_package_names,
    search_ecosystem_by_topic,
)
from contextsc.mcp import mcp


@mcp.tool
def search_scverse_ecosystem(topic: str, max_results_per_package: int = 3) -> str:
    """Search for functions across all installed scverse packages.

    This tool searches through all installed scverse packages to find functions
    matching your topic. It's useful for discovering which package has the
    functionality you need before diving into specific documentation.

    Parameters
    ----------
    topic : str
        Topic keyword to search for.

    Examples
    --------
        - 'differential' - Find differential expression analysis functions
        - 'clustering' - Find clustering methods across packages
        - 'normalize' - Find normalization functions
        - 'perturbation' - Find perturbation analysis tools
    max_results_per_package : int, default: 3
        Maximum number of results to show per package.

    Returns
    -------
    str
        Functions grouped by package with relevance scores and brief descriptions.

    Examples
    --------
    >>> search_scverse_ecosystem("differential")
    >>> search_scverse_ecosystem("clustering", max_results_per_package=5)
    """
    # Check if any scverse packages are installed
    installed = get_installed_package_names()
    if not installed:
        return (
            "❌ No scverse packages are currently installed.\n\n"
            "Please install at least one scverse package:\n"
            "- `pip install scanpy` for single-cell analysis\n"
            "- `pip install pertpy` for perturbation analysis\n"
            "- `pip install anndata` for data structures\n\n"
            "Use `resolve-scverse-package` to see all available packages."
        )

    # Validate topic
    if not topic.strip():
        return "❌ Please provide a search topic (e.g., 'differential', 'clustering', 'normalize')."

    # Search across ecosystem
    results = search_ecosystem_by_topic(topic, max_results_per_package)

    if not results:
        return (
            f"No functions found matching topic '{topic}' across installed packages.\n\n"
            f"Installed packages: {', '.join(installed)}\n\n"
            f"Tips:\n"
            f"- Try a different or more general topic\n"
            f"- Check if the relevant package is installed with `resolve-scverse-package`\n"
            f"- Use `get-scverse-docs('<package>.tl')` or `get-scverse-docs('<package>.pp')` "
            f"to list all functions in a package"
        )

    # Format output grouped by package
    output_lines = [
        f"# Functions matching '{topic}' across scverse ecosystem",
        "",
        f"Found matches in {len(results)} package(s):",
        "",
    ]

    for package_name in sorted(results.keys()):
        matches = results[package_name]
        output_lines.append(f"## {package_name}")
        output_lines.append("")

        for func_name, func_info, score in matches:
            # Extract first line of docstring as brief description
            first_line = func_info.docstring.split("\n")[0] if func_info.docstring else "No description"
            output_lines.append(f"- **{func_name}** (score: {score})")
            output_lines.append(f"  {first_line}")
            output_lines.append("")

        output_lines.append("")

    # Add helpful next steps
    output_lines.append("---")
    output_lines.append("")
    output_lines.append("To get detailed documentation for a specific function, use:")
    output_lines.append("`get-scverse-docs('<package>.<module>.<function_name>')`")
    output_lines.append("")
    output_lines.append("Example:")
    if results:
        # Show example with first result
        first_package = next(iter(results))
        first_func = results[first_package][0][0]
        output_lines.append(f"`get-scverse-docs('{first_package}.tl.{first_func}')`")

    return "\n".join(output_lines)
