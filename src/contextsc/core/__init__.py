"""Core utilities for scverse documentation introspection."""

from .environment import (
    InstalledPackage,
    get_installed_package_names,
    get_installed_scverse_packages,
    get_package_version,
    is_package_installed,
)
from .formatter import (
    format_function_docs,
    format_function_list,
    format_package_list,
)
from .introspector import (
    FunctionInfo,
    IntrospectionError,
    extract_function_info,
    get_object_by_path,
    list_module_functions,
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
    "format_function_docs",
    "format_function_list",
    "format_package_list",
    # introspector
    "FunctionInfo",
    "IntrospectionError",
    "extract_function_info",
    "get_object_by_path",
    "list_module_functions",
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
