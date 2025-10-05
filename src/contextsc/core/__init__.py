"""Core utilities for scverse documentation introspection."""

from .environment import (
    InstalledPackage,
    get_installed_package_names,
    get_installed_scverse_packages,
    get_package_version,
    is_package_installed,
)
from .formatter import (
    DEFAULT_TOKENS,
    MINIMUM_TOKENS,
    filter_docstring_by_topic,
    format_function_docs,
    format_function_list,
    format_package_list,
    parse_numpy_docstring,
)
from .introspector import (
    FunctionInfo,
    IntrospectionError,
    extract_function_info,
    get_object_by_path,
    list_module_functions,
    search_functions_by_topic,
)
from .package_registry import (
    ANALYSIS_PACKAGES,
    CORE_SCVERSE_PACKAGES,
    DATA_FORMAT_PACKAGES,
    PackageCategory,
    ScverseAnalysisPackage,
    ScverseDataFormatPackage,
    ScversePackage,
    get_package_by_name,
)

__all__ = [
    # environment
    "InstalledPackage",
    "get_installed_package_names",
    "get_installed_scverse_packages",
    "get_package_version",
    "is_package_installed",
    # formatter
    "DEFAULT_TOKENS",
    "MINIMUM_TOKENS",
    "filter_docstring_by_topic",
    "format_function_docs",
    "format_function_list",
    "format_package_list",
    "parse_numpy_docstring",
    # introspector
    "FunctionInfo",
    "IntrospectionError",
    "extract_function_info",
    "get_object_by_path",
    "list_module_functions",
    "search_functions_by_topic",
    # package_registry
    "ANALYSIS_PACKAGES",
    "CORE_SCVERSE_PACKAGES",
    "DATA_FORMAT_PACKAGES",
    "PackageCategory",
    "ScverseAnalysisPackage",
    "ScverseDataFormatPackage",
    "ScversePackage",
    "get_package_by_name",
]
