"""Environment detection for installed scverse packages."""

import importlib.metadata
import importlib.util
from dataclasses import dataclass
from functools import lru_cache

from .package_registry import CORE_SCVERSE_PACKAGES, ScversePackage


@dataclass(frozen=True)
class InstalledPackage:
    """Information about an installed scverse package.

    Attributes
    ----------
    metadata : ScversePackage
        Package metadata from registry.
    version : str
        Installed version.
    is_available : bool
        Whether the package can be imported.
    """

    metadata: ScversePackage
    version: str
    is_available: bool


@lru_cache(maxsize=128)
def is_package_installed(package_name: str) -> bool:
    """Check if a package is installed and importable.

    Parameters
    ----------
    package_name : str
        Name of the package to check.

    Returns
    -------
    bool
        True if package is installed and importable.
    """
    return importlib.util.find_spec(package_name) is not None


@lru_cache(maxsize=128)
def get_package_version(package_name: str) -> str | None:
    """Get the version of an installed package.

    Parameters
    ----------
    package_name : str
        Name of the package.

    Returns
    -------
    str | None
        Version string if package is installed, None otherwise.
    """
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None


def get_installed_scverse_packages() -> list[InstalledPackage]:
    """Get list of installed core scverse packages.

    Returns
    -------
    list[InstalledPackage]
        List of installed packages with their metadata and versions.
    """
    installed = []

    for package in CORE_SCVERSE_PACKAGES:
        is_available = is_package_installed(package.name)
        version = get_package_version(package.name) if is_available else "not installed"

        installed.append(
            InstalledPackage(
                metadata=package,
                version=version,
                is_available=is_available,
            )
        )

    return installed


def get_installed_package_names() -> list[str]:
    """Get list of installed scverse package names.

    Returns
    -------
    list[str]
        Names of installed scverse packages.
    """
    return [pkg.metadata.name for pkg in get_installed_scverse_packages() if pkg.is_available]
