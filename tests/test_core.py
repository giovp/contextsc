"""Tests for core introspection functionality."""

import pytest

from contextsc.core import (
    ANALYSIS_PACKAGES,
    CORE_SCVERSE_PACKAGES,
    DATA_FORMAT_PACKAGES,
    IntrospectionError,
    PackageCategory,
    ScverseAnalysisPackage,
    ScverseDataFormatPackage,
    extract_function_info,
    format_function_docs,
    format_package_list,
    get_installed_package_names,
    get_installed_scverse_packages,
    get_package_by_name,
    is_package_installed,
    list_module_functions,
)


def test_package_registry():
    """Test package registry has expected packages."""
    assert len(CORE_SCVERSE_PACKAGES) == 12
    assert len(DATA_FORMAT_PACKAGES) == 3
    assert len(ANALYSIS_PACKAGES) == 9

    package_names = [pkg.name for pkg in CORE_SCVERSE_PACKAGES]
    assert "anndata" in package_names
    assert "scanpy" in package_names
    assert "mudata" in package_names
    assert "scvi-tools" in package_names
    assert "scirpy" in package_names
    assert "snapatac2" in package_names
    assert "rapids_singlecell" in package_names
    assert "pertpy" in package_names
    assert "decoupler" in package_names


def test_package_categories():
    """Test package categories are correctly assigned."""
    # Test data format packages
    for pkg in DATA_FORMAT_PACKAGES:
        assert isinstance(pkg, ScverseDataFormatPackage)
        assert pkg.category == PackageCategory.DATA_FORMAT

    # Test analysis packages
    for pkg in ANALYSIS_PACKAGES:
        assert isinstance(pkg, ScverseAnalysisPackage)
        assert pkg.category == PackageCategory.ANALYSIS

    # Check specific packages
    anndata = get_package_by_name("anndata")
    assert anndata.category == PackageCategory.DATA_FORMAT

    scanpy = get_package_by_name("scanpy")
    assert scanpy.category == PackageCategory.ANALYSIS


def test_get_package_by_name():
    """Test looking up package by name."""
    scanpy = get_package_by_name("scanpy")
    assert scanpy is not None
    assert scanpy.name == "scanpy"
    assert scanpy.display_name == "Scanpy"

    # Case insensitive
    anndata = get_package_by_name("AnnData")
    assert anndata is not None
    assert anndata.name == "anndata"

    # Non-existent package
    result = get_package_by_name("nonexistent")
    assert result is None


def test_is_package_installed():
    """Test checking if packages are installed."""
    # Standard library should be installed
    assert is_package_installed("sys")
    assert is_package_installed("os")

    # Non-existent package
    assert not is_package_installed("this_package_does_not_exist_12345")


def test_get_installed_scverse_packages():
    """Test getting list of installed scverse packages."""
    packages = get_installed_scverse_packages()
    assert len(packages) == 12
    assert all(hasattr(pkg, "metadata") for pkg in packages)
    assert all(hasattr(pkg, "version") for pkg in packages)
    assert all(hasattr(pkg, "is_available") for pkg in packages)


def test_get_installed_package_names():
    """Test getting only names of installed packages."""
    names = get_installed_package_names()
    assert isinstance(names, list)
    # Could be empty if no scverse packages installed
    assert all(isinstance(name, str) for name in names)


def test_extract_function_info_builtin():
    """Test extracting info from a built-in function."""
    # Use a simple built-in
    func_info = extract_function_info("os.path.join")
    assert func_info.name == "os.path.join"
    assert func_info.docstring != "No documentation available."
    assert func_info.module == "posixpath" or func_info.module == "ntpath"


def test_extract_function_info_invalid():
    """Test extracting info from invalid path."""
    with pytest.raises(IntrospectionError):
        extract_function_info("nonexistent.module.function")


def test_list_module_functions():
    """Test listing functions in a module."""
    # Use os.path as a test module
    functions = list_module_functions("os.path")
    assert isinstance(functions, list)
    assert len(functions) > 0
    assert "join" in functions
    assert "exists" in functions
    # Should not include private functions
    assert not any(f.startswith("_") for f in functions)


def test_list_module_functions_invalid():
    """Test listing functions from invalid module."""
    with pytest.raises(IntrospectionError):
        list_module_functions("nonexistent.module")


def test_format_function_docs():
    """Test formatting function documentation."""
    func_info = extract_function_info("os.path.join")
    formatted = format_function_docs(func_info)

    assert "# os.path.join" in formatted
    assert "## Signature" in formatted
    assert "## Documentation" in formatted
    assert func_info.docstring in formatted


def test_format_function_docs_with_token_limit():
    """Test formatting with token limit."""
    func_info = extract_function_info("os.path.join")
    formatted = format_function_docs(func_info, max_tokens=100)

    # Should be truncated
    assert "[... truncated due to token limit ...]" in formatted or len(formatted) < 1000


def test_format_package_list():
    """Test formatting package list."""
    packages = [
        ("scanpy", "1.9.0", True),
        ("anndata", "0.8.0", True),
        ("mudata", "0.1.0", False),
    ]

    formatted = format_package_list(packages)
    assert "# Installed Scverse Packages" in formatted
    assert "scanpy" in formatted
    assert "anndata" in formatted
    assert "Available Packages" in formatted
    assert "Not Installed" in formatted


def test_format_package_list_none_installed():
    """Test formatting when no packages are installed."""
    packages = [
        ("scanpy", "not installed", False),
        ("anndata", "not installed", False),
    ]

    formatted = format_package_list(packages)
    assert "No scverse packages are currently installed" in formatted
