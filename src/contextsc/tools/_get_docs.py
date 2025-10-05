"""Tool for fetching documentation from scverse packages."""

from contextsc.core import (
    DEFAULT_TOKENS,
    MINIMUM_TOKENS,
    IntrospectionError,
    extract_function_info,
    format_function_docs,
    format_function_list,
    get_installed_package_names,
    list_module_functions,
    search_functions_by_topic,
)
from contextsc.mcp import mcp


@mcp.tool
def get_scverse_docs(function_path: str, topic: str = "", max_tokens: int = DEFAULT_TOKENS) -> str:
    """Fetch documentation for a specific scverse function or search by topic.

    This tool retrieves up-to-date API documentation directly from installed
    scverse packages using Python introspection. It extracts docstrings,
    function signatures, and parameter information.

    Parameters
    ----------
    function_path : str
        Full dotted path to a function or module.

    Examples
    --------
        - 'scanpy.pp.normalize_total' - Get docs for specific function
        - 'scanpy.pp' - List or search functions in the module
        - 'anndata.AnnData' - Get docs for a class
    topic : str, default: ""
        Optional topic keyword to filter documentation (e.g., 'normalize', 'clustering').
        When specified with a module path, searches for relevant functions.
        When specified with a function path, filters docstring sections by topic.
    max_tokens : int, default: 10000
        Maximum tokens to return in the response. Documentation will be
        intelligently truncated if it exceeds this limit.
        Minimum 1000 tokens enforced.

    Returns
    -------
    str
        Formatted documentation with signature, parameters, and docstring.
        Or a list of functions if a module path is provided.
        Or topic-filtered results if topic is specified.

    Examples
    --------
    >>> get_scverse_docs("scanpy.pp.normalize_total")
    >>> get_scverse_docs("scanpy.pp", topic="normalize")  # Search for normalize functions
    >>> get_scverse_docs("scanpy.pp.neighbors", topic="connectivity")  # Filter by topic
    >>> get_scverse_docs("anndata.AnnData", max_tokens=5000)  # Limit output size
    """
    # Enforce minimum token limit (like Context7)
    max_tokens = max(max_tokens, MINIMUM_TOKENS)

    # Check if any scverse packages are installed
    installed = get_installed_package_names()
    if not installed:
        return (
            "❌ No scverse packages are currently installed.\n\n"
            "Please install at least one scverse package:\n"
            "- `pip install scanpy` for single-cell analysis\n"
            "- `pip install anndata` for data structures\n\n"
            "Use `resolve-scverse-package` to see all available packages."
        )

    # Check if the path starts with an installed package
    package_name = function_path.split(".")[0]
    if package_name not in installed:
        return (
            f"❌ Package '{package_name}' is not installed.\n\n"
            f"Installed packages: {', '.join(installed)}\n\n"
            f"Use `resolve-scverse-package` to see all available packages."
        )

    # Try to extract function info
    try:
        func_info = extract_function_info(function_path)
        # It's a function - format with topic filtering
        return format_function_docs(func_info, max_tokens=max_tokens, topic=topic)
    except IntrospectionError:
        # Maybe it's a module
        try:
            functions = list_module_functions(function_path)
            if not functions:
                return (
                    f"❌ No public functions found in module '{function_path}'.\n\n"
                    f"Try using `resolve-scverse-package` to explore available packages."
                )

            # If topic specified, search for relevant functions
            if topic:
                results = search_functions_by_topic(function_path, topic, max_results=5)
                if not results:
                    return (
                        f"No functions found in '{function_path}' matching topic '{topic}'.\n\n"
                        f"Try a different topic or use `get-scverse-docs('{function_path}')` "
                        f"to see all available functions."
                    )

                # Format results with documentation for each relevant function
                output_lines = [
                    f"# Functions in {function_path} matching topic: '{topic}'",
                    "",
                    f"Found {len(results)} relevant function(s):",
                    "",
                ]

                remaining_tokens = max_tokens
                for func_name, func_info, score in results:
                    # Reserve tokens for this function's documentation
                    func_output = format_function_docs(
                        func_info, max_tokens=remaining_tokens // len(results), topic=topic
                    )
                    output_lines.append(f"## {func_name} (relevance score: {score})")
                    output_lines.append("")
                    output_lines.append(func_output)
                    output_lines.append("\n" + "-" * 80 + "\n")

                    # Update remaining tokens
                    tokens_used = len("\n".join(output_lines)) // 4
                    remaining_tokens = max_tokens - tokens_used

                    if remaining_tokens < MINIMUM_TOKENS:
                        output_lines.append("\n[... additional results truncated due to token limit ...]\n")
                        break

                return "\n".join(output_lines)
            else:
                # No topic - just list functions
                result = format_function_list(function_path, functions)
                result += (
                    f"\n\nTo get documentation for a specific function, use:\n"
                    f"`get-scverse-docs('{function_path}.<function_name>')`\n\n"
                    f"Or search by topic:\n"
                    f"`get-scverse-docs('{function_path}', topic='your_topic')`"
                )
                return result

        except IntrospectionError as e:
            return (
                f"❌ Could not find '{function_path}'.\n\n"
                f"Error: {str(e)}\n\n"
                f"Make sure the path is correct. Examples:\n"
                f"- 'scanpy.pp.normalize_total'\n"
                f"- 'anndata.AnnData'\n"
                f"- 'scanpy.pp' (for module listing)\n\n"
                f"Use `resolve-scverse-package` to see installed packages."
            )
