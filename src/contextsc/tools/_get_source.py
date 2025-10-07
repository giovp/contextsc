"""Tool for fetching source code from scverse packages."""

from contextsc.core import (
    DEFAULT_TOKENS,
    MINIMUM_TOKENS,
    IntrospectionError,
    extract_function_info,
    extract_function_source,
    format_function_source,
    get_installed_package_names,
)
from contextsc.mcp import mcp


@mcp.tool
def get_scverse_source(function_path: str, include_docs: bool = False, max_tokens: int = DEFAULT_TOKENS) -> str:
    """Fetch source code for a specific scverse function.

    This tool retrieves the actual Python implementation code directly from
    installed scverse packages using Python introspection. This is useful when
    docstrings don't fully capture the behavior or you need to understand the
    implementation details.

    Parameters
    ----------
    function_path : str
        Full dotted path to a function or method.

    Examples
    --------
        - 'scanpy.pp.normalize_total' - Get source for specific function
        - 'anndata.AnnData.obs_names' - Get source for a property/method
    include_docs : bool, default: False
        If True, include brief documentation alongside the source code.
    max_tokens : int, default: 10000
        Maximum tokens to return in the response. Source code will be
        intelligently truncated if it exceeds this limit.
        Minimum 1000 tokens enforced.

    Returns
    -------
    str
        Formatted source code with file path and line numbers.
        Optionally includes brief documentation.

    Examples
    --------
    >>> get_scverse_source("scanpy.pp.normalize_total")
    >>> get_scverse_source("scanpy.pp.normalize_total", include_docs=True)
    >>> get_scverse_source("anndata.AnnData.__init__", max_tokens=5000)
    """
    # Enforce minimum token limit
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

    # Try to extract source code
    try:
        source_info = extract_function_source(function_path)
    except IntrospectionError as e:
        error_msg = str(e)
        if "C extension" in error_msg or "built-in" in error_msg:
            return (
                f"❌ Cannot retrieve source code for '{function_path}'.\n\n"
                f"This appears to be a built-in function, C extension, or dynamically generated code. "
                f"Source code is not available for inspection.\n\n"
                f"Error: {error_msg}\n\n"
                f"Try using `get-scverse-docs('{function_path}')` to see the documentation instead."
            )
        else:
            return (
                f"❌ Could not find '{function_path}'.\n\n"
                f"Error: {error_msg}\n\n"
                f"Make sure the path is correct. Examples:\n"
                f"- 'scanpy.pp.normalize_total'\n"
                f"- 'anndata.AnnData'\n"
                f"- 'scanpy.tl.rank_genes_groups'\n\n"
                f"Use `get-scverse-docs('<package>.pp')` or `get-scverse-docs('<package>.tl')` "
                f"to list available functions."
            )

    # Get documentation if requested
    func_info = None
    if include_docs:
        try:
            func_info = extract_function_info(function_path)
        except IntrospectionError:
            # If we can't get docs, that's okay - just show source
            pass

    # Format and return
    return format_function_source(source_info, func_info=func_info, max_tokens=max_tokens)
