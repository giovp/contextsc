"""Introspection utilities for extracting documentation from scverse packages."""

import importlib
import inspect
from dataclasses import dataclass
from typing import Any


@dataclass
class FunctionInfo:
    """Information extracted from a function or method.

    Attributes
    ----------
    name : str
        Full qualified name (e.g., 'scanpy.pp.normalize_total').
    docstring : str
        Function docstring.
    signature : str
        Function signature as string.
    module : str
        Module where the function is defined.
    parameters : dict[str, str]
        Parameter names and their annotations as strings.
    return_annotation : str
        Return type annotation as string.
    """

    name: str
    docstring: str
    signature: str
    module: str
    parameters: dict[str, str]
    return_annotation: str


class IntrospectionError(Exception):
    """Raised when introspection fails."""

    pass


def get_object_by_path(module_path: str) -> Any:
    """Get a Python object by its full dotted path.

    Parameters
    ----------
    module_path : str
        Full dotted path (e.g., 'scanpy.pp.normalize_total').

    Returns
    -------
    Any
        The object at that path.

    Raises
    ------
    IntrospectionError
        If the object cannot be found or imported.
    """
    parts = module_path.split(".")

    # Try different split points to find the module
    for i in range(len(parts), 0, -1):
        module_name = ".".join(parts[:i])
        attr_path = parts[i:]

        try:
            module = importlib.import_module(module_name)

            # Navigate to the final object
            obj = module
            for attr in attr_path:
                obj = getattr(obj, attr)

            return obj
        except (ImportError, AttributeError):
            continue

    raise IntrospectionError(f"Could not find object at path: {module_path}")


def extract_function_info(module_path: str) -> FunctionInfo:
    """Extract detailed information about a function or method.

    Parameters
    ----------
    module_path : str
        Full dotted path to the function (e.g., 'scanpy.pp.normalize_total').

    Returns
    -------
    FunctionInfo
        Extracted function information.

    Raises
    ------
    IntrospectionError
        If the function cannot be introspected.
    """
    try:
        obj = get_object_by_path(module_path)
    except IntrospectionError as e:
        raise IntrospectionError(f"Failed to import {module_path}: {e}") from e

    # Verify it's callable
    if not callable(obj):
        raise IntrospectionError(f"{module_path} is not a callable object")

    # Extract docstring
    docstring = inspect.getdoc(obj) or "No documentation available."

    # Extract signature
    try:
        sig = inspect.signature(obj)
        signature_str = str(sig)
    except (ValueError, TypeError):
        signature_str = "Signature not available"
        sig = None

    # Extract module
    try:
        module_name = obj.__module__
    except AttributeError:
        module_name = "unknown"

    # Extract parameters
    parameters = {}
    if sig:
        for param_name, param in sig.parameters.items():
            annotation = param.annotation
            if annotation != inspect.Parameter.empty:
                parameters[param_name] = str(annotation)
            else:
                parameters[param_name] = "Any"

    # Extract return annotation
    return_annotation = "Any"
    if sig and sig.return_annotation != inspect.Signature.empty:
        return_annotation = str(sig.return_annotation)

    return FunctionInfo(
        name=module_path,
        docstring=docstring,
        signature=signature_str,
        module=module_name,
        parameters=parameters,
        return_annotation=return_annotation,
    )


def list_module_functions(module_path: str) -> list[str]:
    """List all public functions in a module.

    Parameters
    ----------
    module_path : str
        Module path (e.g., 'scanpy.pp').

    Returns
    -------
    list[str]
        List of function names in the module.

    Raises
    ------
    IntrospectionError
        If the module cannot be imported.
    """
    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        raise IntrospectionError(f"Failed to import module {module_path}: {e}") from e

    functions = []
    for name in dir(module):
        # Skip private members
        if name.startswith("_"):
            continue

        try:
            obj = getattr(module, name)
            if callable(obj):
                functions.append(name)
        except (AttributeError, ImportError):
            continue

    return sorted(functions)
