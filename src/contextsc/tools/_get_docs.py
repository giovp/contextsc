"""Tool for fetching documentation from scverse packages."""

from contextsc.core import (
    IntrospectionError,
    extract_function_info,
    format_function_docs,
    format_function_list,
    get_installed_package_names,
    list_module_functions,
)
from contextsc.mcp import mcp


@mcp.tool
def get_scverse_docs(function_path: str, max_tokens: int = 10000) -> str:
    """Fetch documentation for a specific scverse function or list functions in a module.

    This tool retrieves up-to-date API documentation directly from installed
    scverse packages using Python introspection. It extracts docstrings,
    function signatures, and parameter information.

    Parameters
    ----------
    function_path : str
        Full dotted path to a function or module.
        Examples:
        - 'scanpy.pp.normalize_total' - Get docs for specific function
        - 'scanpy.pp' - List all functions in the module
        - 'anndata.AnnData' - Get docs for a class
    max_tokens : int, default: 10000
        Maximum tokens to return in the response. Documentation will be
        truncated if it exceeds this limit.

    Returns
    -------
    str
        Formatted documentation with signature, parameters, and docstring.
        Or a list of functions if a module path is provided.

    Examples
    --------
    >>> get_scverse_docs("scanpy.pp.normalize_total")
    >>> get_scverse_docs("scanpy.pp")  # List all preprocessing functions
    >>> get_scverse_docs("anndata.AnnData.obs_names")
    """
    # Check if any scverse packages are installed
    installed = get_installed_package_names()
    if not installed:
        return (
            "❌ No scverse packages are currently installed.\n\n"
            "Please install at least one scverse package:\n"
            "- `pip install scanpy` for single-cell analysis\n"
            "- `pip install anndata` for data structures\n"
            "- `pip install mudata` for multimodal data\n\n"
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
        return format_function_docs(func_info, max_tokens=max_tokens)
    except IntrospectionError:
        # Maybe it's a module - try listing functions
        try:
            functions = list_module_functions(function_path)
            if functions:
                result = format_function_list(function_path, functions)
                # Add helpful message
                result += (
                    f"\n\nTo get documentation for a specific function, use:\n"
                    f"`get-scverse-docs('{function_path}.<function_name>')`"
                )
                return result
            else:
                return (
                    f"❌ No public functions found in module '{function_path}'.\n\n"
                    f"Try using `resolve-scverse-package` to explore available packages."
                )
        except IntrospectionError as e:
            return (
                f"❌ Could not find '{function_path}'.\n\n"
                f"Error: {str(e)}\n\n"
                f"Make sure the path is correct. Examples:\n"
                f"- 'scanpy.pp.normalize_total'\n"
                f"- 'anndata.AnnData'\n"
                f"- 'mudata.MuData'\n\n"
                f"Use `resolve-scverse-package` to see installed packages."
            )
