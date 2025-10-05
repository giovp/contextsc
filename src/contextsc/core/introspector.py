"""Introspection utilities for extracting documentation from scverse packages."""

import importlib
import inspect
from dataclasses import dataclass
from typing import Any

from .package_registry import CORE_SCVERSE_PACKAGES

# Allowed package names for introspection (scverse analysis + data format packages)
ALLOWED_PACKAGES = frozenset(pkg.name for pkg in CORE_SCVERSE_PACKAGES)


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


def get_object_by_path(module_path: str, _allow_any_package: bool = False) -> Any:
    """Get a Python object by its full dotted path.

    Only allows introspection of core scverse packages by default.

    Parameters
    ----------
    module_path : str
        Full dotted path (e.g., 'scanpy.pp.normalize_total').
    _allow_any_package : bool, default: False
        Internal parameter for testing. Allows introspection of non-scverse packages.

    Returns
    -------
    Any
        The object at that path.

    Raises
    ------
    IntrospectionError
        If the object cannot be found or imported, or if the package is not a scverse package.
    """
    parts = module_path.split(".")

    # Validate that the root package is a scverse package (unless testing)
    if not _allow_any_package and (not parts or parts[0] not in ALLOWED_PACKAGES):
        allowed_list = ", ".join(sorted(ALLOWED_PACKAGES))
        raise IntrospectionError(
            f"Package '{parts[0] if parts else module_path}' is not an allowed scverse package. "
            f"Allowed packages: {allowed_list}"
        )

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


def extract_function_info(module_path: str, _allow_any_package: bool = False) -> FunctionInfo:
    """Extract detailed information about a function or method.

    Parameters
    ----------
    module_path : str
        Full dotted path to the function (e.g., 'scanpy.pp.normalize_total').
    _allow_any_package : bool, default: False
        Internal parameter for testing. Allows introspection of non-scverse packages.

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
        obj = get_object_by_path(module_path, _allow_any_package=_allow_any_package)
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


def search_functions_by_topic(
    module_path: str, topic: str, max_results: int = 5
) -> list[tuple[str, FunctionInfo, int]]:
    """Search for functions in a module matching a topic.

    Automatically uses semantic search if sentence-transformers is installed,
    otherwise falls back to keyword search.

    Parameters
    ----------
    module_path : str
        Module path to search in (e.g., 'scanpy.pp').
    topic : str
        Topic keyword to search for.
    max_results : int, default: 5
        Maximum number of results to return.

    Returns
    -------
    list[tuple[str, FunctionInfo, int]]
        List of (function_name, function_info, score) tuples sorted by relevance.
        Scores are integers in 0-100 range.

    Raises
    ------
    IntrospectionError
        If the module cannot be imported or introspected.

    Notes
    -----
    If contextsc[semsearch] is installed, this function will use semantic similarity
    for more intelligent matching. Otherwise, it falls back to keyword-based search.
    """
    # Handle empty topic edge case
    if not topic.strip():
        return []

    functions = list_module_functions(module_path)

    # Try semantic search first if available
    try:
        from sentence_transformers import SentenceTransformer
        from sentence_transformers.util import cos_sim

        # Load model (cached by sentence-transformers library)
        model = SentenceTransformer("all-MiniLM-L6-v2")

        # Encode topic query
        topic_embedding = model.encode(topic, convert_to_tensor=False)

        # Collect and encode function descriptions
        func_embeddings = []
        func_data = []
        for func_name in functions:
            full_path = f"{module_path}.{func_name}"
            try:
                func_info = extract_function_info(full_path)
                # Use function name + first paragraph of docstring for embedding
                first_para = func_info.docstring.split("\n\n")[0] if func_info.docstring else ""
                searchable_text = f"{func_name} {first_para}"[:512]  # Truncate to model limit
                func_embeddings.append(model.encode(searchable_text, convert_to_tensor=False))
                func_data.append((func_name, func_info))
            except IntrospectionError:
                continue

        if not func_embeddings:
            return []

        # Compute cosine similarities
        similarities = cos_sim(topic_embedding, func_embeddings)[0]

        # Create results with normalized scores (0-100 range)
        results = []
        for idx, (func_name, func_info) in enumerate(func_data):
            score = int(similarities[idx].item() * 100)  # Normalize to match keyword scores
            if score > 10:  # Filter low-relevance results
                results.append((func_name, func_info, score))

        results.sort(key=lambda x: x[2], reverse=True)
        return results[:max_results]

    except ImportError:
        # sentence-transformers not installed, fall back to keyword search silently
        pass
    except (RuntimeError, OSError):
        # Model loading failed (network, disk space, etc.), fall back silently
        pass

    # Keyword search logic (fallback or default)
    topic_lower = topic.lower()
    results = []

    for func_name in functions:
        full_path = f"{module_path}.{func_name}"
        try:
            func_info = extract_function_info(full_path)
        except IntrospectionError:
            continue  # Skip functions we can't introspect

        # Calculate relevance score
        score = 0

        # High weight for name matches
        if topic_lower in func_name.lower():
            score += 10

        # Medium weight for docstring first paragraph
        docstring_lower = func_info.docstring.lower()
        first_para = docstring_lower.split("\n\n")[0] if "\n\n" in docstring_lower else docstring_lower
        score += first_para.count(topic_lower) * 5

        # Low weight for full docstring
        score += docstring_lower.count(topic_lower)

        if score > 0:
            results.append((func_name, func_info, score))

    # Sort by score (descending) and return top results
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:max_results]
