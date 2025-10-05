"""Tool for resolving scverse package names and listing installed packages."""

from contextsc.core import format_package_list, get_installed_scverse_packages
from contextsc.mcp import mcp


@mcp.tool
def resolve_scverse_package(package_name: str | None = None) -> str:
    """Resolve scverse package names to IDs and list installed packages.

    This tool helps identify which scverse packages are available in the current
    environment. If a package_name is provided, it returns information about that
    specific package. Otherwise, it lists all core scverse packages and their
    installation status.

    Parameters
    ----------
    package_name : str | None, default: None
        Optional package name to look up. If None, lists all packages.

    Returns
    -------
    str
        Formatted information about installed scverse packages.

    Examples
    --------
    >>> resolve_scverse_package()  # List all packages
    >>> resolve_scverse_package("scanpy")  # Info about scanpy
    """
    installed_packages = get_installed_scverse_packages()

    if package_name:
        # Find specific package
        package_name_lower = package_name.lower()
        for pkg in installed_packages:
            if pkg.metadata.name.lower() == package_name_lower:
                if pkg.is_available:
                    return (
                        f"# {pkg.metadata.display_name}\n\n"
                        f"**Package:** `{pkg.metadata.name}`\n"
                        f"**Version:** {pkg.version}\n"
                        f"**Status:** ✅ Installed\n\n"
                        f"**Description:** {pkg.metadata.description}\n\n"
                        f"**Documentation:** {pkg.metadata.docs_url}\n"
                        f"**GitHub:** {pkg.metadata.github_url}\n\n"
                        f"Use `get-scverse-docs` to fetch documentation for specific functions."
                    )
                else:
                    return (
                        f"# {pkg.metadata.display_name}\n\n"
                        f"**Package:** `{pkg.metadata.name}`\n"
                        f"**Status:** ❌ Not Installed\n\n"
                        f"**Description:** {pkg.metadata.description}\n\n"
                        f"Install with: `pip install {pkg.metadata.name}`\n\n"
                        f"**Documentation:** {pkg.metadata.docs_url}\n"
                        f"**GitHub:** {pkg.metadata.github_url}"
                    )

        return f"Package '{package_name}' is not a core scverse package."

    # List all packages
    package_tuples = [(pkg.metadata.name, pkg.version, pkg.is_available) for pkg in installed_packages]

    return format_package_list(package_tuples)
