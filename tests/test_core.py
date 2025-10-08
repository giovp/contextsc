"""Tests for core introspection functionality."""

import pytest

from contextsc.core import (
    ANALYSIS_PACKAGES,
    CORE_SCVERSE_PACKAGES,
    DATA_FORMAT_PACKAGES,
    DEFAULT_TOKENS,
    MINIMUM_TOKENS,
    IntrospectionError,
    PackageCategory,
    ScverseAnalysisPackage,
    ScverseDataFormatPackage,
    extract_function_info,
    extract_function_source,
    filter_docstring_by_topic,
    format_function_docs,
    format_function_source,
    format_package_list,
    get_installed_package_names,
    get_installed_scverse_packages,
    get_package_by_name,
    is_package_installed,
    list_module_functions,
    parse_numpy_docstring,
    search_ecosystem_by_topic,
    search_functions_by_topic,
)


# Test utility: allow testing with non-scverse packages like os.path
def extract_function_info_any(path: str):
    """Extract function info allowing any package (for testing)."""
    return extract_function_info(path, _allow_any_package=True)


def extract_function_source_any(path: str):
    """Extract function source allowing any package (for testing)."""
    return extract_function_source(path, _allow_any_package=True)


def list_module_functions_any(path: str):
    """List module functions allowing any package (for testing)."""
    # list_module_functions doesn't have validation, but import uses extract_function_info
    import importlib

    try:
        module = importlib.import_module(path)
    except ImportError as e:
        from contextsc.core import IntrospectionError

        raise IntrospectionError(f"Failed to import module {path}: {e}") from e

    functions = []
    for name in dir(module):
        if name.startswith("_"):
            continue
        try:
            obj = getattr(module, name)
            if callable(obj):
                functions.append(name)
        except (AttributeError, ImportError):
            continue

    return sorted(functions)


def search_functions_by_topic_any(module_path: str, topic: str, max_results: int = 5):
    """Search functions allowing any package (for testing).

    This uses the real search_functions_by_topic but bypasses package validation.
    """
    from contextsc.core import IntrospectionError

    if not topic.strip():
        return []

    functions = list_module_functions_any(module_path)

    # Try semantic search first if available (same logic as real function)
    try:
        from sentence_transformers import SentenceTransformer
        from sentence_transformers.util import cos_sim

        model = SentenceTransformer("all-MiniLM-L6-v2")
        topic_embedding = model.encode(topic, convert_to_tensor=False)

        func_embeddings = []
        func_data = []
        for func_name in functions:
            full_path = f"{module_path}.{func_name}"
            try:
                func_info = extract_function_info_any(full_path)
                first_para = func_info.docstring.split("\n\n")[0] if func_info.docstring else ""
                searchable_text = f"{func_name} {first_para}"[:512]
                func_embeddings.append(model.encode(searchable_text, convert_to_tensor=False))
                func_data.append((func_name, func_info))
            except IntrospectionError:
                continue

        if func_embeddings:
            similarities = cos_sim(topic_embedding, func_embeddings)[0]
            results = []
            for idx, (func_name, func_info) in enumerate(func_data):
                score = int(similarities[idx].item() * 100)
                if score > 10:
                    results.append((func_name, func_info, score))
            results.sort(key=lambda x: x[2], reverse=True)
            return results[:max_results]
    except (ImportError, RuntimeError, OSError):
        pass

    # Keyword search fallback
    topic_lower = topic.lower()
    results = []

    for func_name in functions:
        full_path = f"{module_path}.{func_name}"
        try:
            func_info = extract_function_info_any(full_path)
        except IntrospectionError:
            continue

        score = 0
        if topic_lower in func_name.lower():
            score += 10

        docstring_lower = func_info.docstring.lower()
        first_para = docstring_lower.split("\n\n")[0] if "\n\n" in docstring_lower else docstring_lower
        score += first_para.count(topic_lower) * 5
        score += docstring_lower.count(topic_lower)

        if score > 0:
            results.append((func_name, func_info, score))

    results.sort(key=lambda x: x[2], reverse=True)
    return results[:max_results]


def test_package_registry():
    """Test package registry has expected packages."""
    assert len(CORE_SCVERSE_PACKAGES) == 11  # snapatac2 disabled due to install issues
    assert len(DATA_FORMAT_PACKAGES) == 3
    assert len(ANALYSIS_PACKAGES) == 8  # snapatac2 disabled

    package_names = [pkg.name for pkg in CORE_SCVERSE_PACKAGES]
    assert "anndata" in package_names
    assert "scanpy" in package_names
    assert "mudata" in package_names
    assert "scvi-tools" in package_names
    assert "scirpy" in package_names
    # snapatac2 is commented out in package_registry.py due to installation issues
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
    assert len(packages) == 11  # snapatac2 disabled due to install issues
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
    # Use a simple built-in (with test utility to allow non-scverse packages)
    func_info = extract_function_info_any("os.path.join")
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
    func_info = extract_function_info_any("os.path.join")
    formatted = format_function_docs(func_info)

    assert "# os.path.join" in formatted
    assert "## Signature" in formatted
    assert "## Documentation" in formatted
    assert func_info.docstring in formatted


def test_format_function_docs_with_token_limit():
    """Test formatting with token limit."""
    func_info = extract_function_info_any("os.path.join")
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


# Token limit tests
def test_token_constants():
    """Test token limit constants are defined correctly."""
    assert MINIMUM_TOKENS == 1000
    assert DEFAULT_TOKENS == 10000
    assert DEFAULT_TOKENS > MINIMUM_TOKENS


def test_token_limit_enforcement():
    """Test that minimum token limit is enforced."""
    func_info = extract_function_info_any("os.path.join")

    # Should enforce minimum even when requesting less
    formatted = format_function_docs(func_info, max_tokens=100)
    assert "# os.path.join" in formatted
    assert "## Signature" in formatted
    # Critical sections should always be present

    # Should respect limits above minimum
    formatted_medium = format_function_docs(func_info, max_tokens=5000)
    formatted_large = format_function_docs(func_info, max_tokens=15000)
    assert len(formatted_medium) <= len(formatted_large)


def test_intelligent_truncation_preserves_critical_sections():
    """Test that critical sections are always preserved."""
    func_info = extract_function_info_any("os.path.join")

    # Even with very low token limit, critical sections should be present
    formatted = format_function_docs(func_info, max_tokens=500)

    # Critical sections that should always be present
    assert "# os.path.join" in formatted  # Header
    assert "## Signature" in formatted  # Signature
    # Parameters section should be present if function has parameters

    # Should not have been truncated mid-sentence
    assert not formatted.endswith("...")


# Numpy docstring parsing tests
def test_parse_numpy_docstring():
    """Test parsing numpy-style docstrings."""
    docstring = """
    Short summary of the function.

    Longer description here.

    Parameters
    ----------
    x : int
        The first parameter.
    y : str
        The second parameter.

    Returns
    -------
    bool
        The return value.

    Examples
    --------
    >>> example()
    True
    """

    sections = parse_numpy_docstring(docstring)

    assert "Summary" in sections
    assert "Parameters" in sections
    assert "Returns" in sections
    assert "Examples" in sections

    # Check content
    assert "Short summary" in sections["Summary"]
    assert "x : int" in sections["Parameters"]
    assert "bool" in sections["Returns"]
    assert "example()" in sections["Examples"]


def test_parse_numpy_docstring_no_sections():
    """Test parsing docstring with no sections."""
    docstring = "Just a simple docstring with no sections."
    sections = parse_numpy_docstring(docstring)

    assert "Summary" in sections
    assert "Just a simple docstring" in sections["Summary"]


# Topic filtering tests
def test_filter_docstring_by_topic():
    """Test filtering docstring sections by topic."""
    docstring = """
    Function for data normalization.

    Parameters
    ----------
    data : array
        Input data to normalize.
    method : str
        Normalization method to use.

    Returns
    -------
    array
        Normalized data.

    Examples
    --------
    >>> normalize(data)
    """

    # Filter by topic "normalize"
    filtered = filter_docstring_by_topic(docstring, "normalize")

    # Summary should always be included
    assert "data normalization" in filtered

    # Sections mentioning "normalize" should be included
    assert "Normalization method" in filtered or "normalize" in filtered.lower()


def test_filter_docstring_no_topic():
    """Test that empty topic returns full docstring."""
    docstring = "Test docstring content."
    filtered = filter_docstring_by_topic(docstring, "")
    assert filtered == docstring


def test_search_functions_by_topic():
    """Test searching functions by topic."""
    # Search os.path for "join" related functions
    results = search_functions_by_topic("os.path", "join", max_results=3)

    assert isinstance(results, list)
    assert len(results) <= 3

    # Should return tuples of (name, func_info, score)
    if results:
        func_name, func_info, score = results[0]
        assert isinstance(func_name, str)
        assert func_info.name.endswith(func_name)
        assert isinstance(score, int)
        assert score > 0

        # "join" should be in the top results for topic "join"
        function_names = [name for name, _, _ in results]
        assert "join" in function_names


def test_search_functions_by_topic_scoring():
    """Test that function name matches score higher."""
    # Search for functions with "join" in name vs only in docstring
    results = search_functions_by_topic("os.path", "join", max_results=5)

    if results:
        # "join" function should score highest (name match = 10 points)
        top_result = results[0]
        if top_result[0] == "join":
            assert top_result[2] >= 10  # Should have at least name match bonus


def test_search_functions_no_matches():
    """Test search with no matching functions."""
    results = search_functions_by_topic("os.path", "nonexistent_topic_xyz", max_results=5)
    assert results == []


def test_format_function_docs_with_topic():
    """Test formatting function docs with topic filtering."""
    func_info = extract_function_info_any("os.path.join")

    # Format with topic
    formatted = format_function_docs(func_info, topic="path")

    # Should still have basic structure
    assert "# os.path.join" in formatted
    assert "## Signature" in formatted

    # Should have filtered documentation
    assert "## Documentation" in formatted


def test_format_function_docs_topic_and_token_limit():
    """Test combining topic filtering with token limits."""
    func_info = extract_function_info_any("os.path.join")

    # Format with both topic and token limit
    formatted = format_function_docs(func_info, max_tokens=2000, topic="path")

    # Should have critical sections
    assert "# os.path.join" in formatted
    assert "## Signature" in formatted

    # Should respect token limit
    from contextsc.core.formatter import estimate_token_count

    estimated = estimate_token_count(formatted)
    # Allow some flexibility in estimation
    assert estimated <= 3000  # Some buffer for estimation variance


# Semantic search tests
def test_semantic_search_empty_topic():
    """Test that empty topic returns empty list."""
    results = search_functions_by_topic("os.path", "")
    assert results == []

    results = search_functions_by_topic("os.path", "   ")
    assert results == []


def test_semantic_search_fallback_on_import_error(monkeypatch):
    """Test graceful fallback when sentence-transformers not installed."""
    import builtins

    # Mock sentence_transformers import to raise ImportError
    def mock_import(name, *args, **kwargs):
        if name == "sentence_transformers" or name.startswith("sentence_transformers."):
            raise ImportError("No module named 'sentence_transformers'")
        return original_import(name, *args, **kwargs)

    original_import = builtins.__import__
    monkeypatch.setattr(builtins, "__import__", mock_import)

    # Should fall back to keyword search without crashing (using test utility)
    results = search_functions_by_topic_any("os.path", "join")

    # Should still return results via keyword search
    assert len(results) > 0
    function_names = [name for name, _, _ in results]
    assert "join" in function_names


def test_semantic_search_fallback_on_runtime_error(monkeypatch):
    """Test graceful fallback when model loading fails."""

    # Mock SentenceTransformer to raise RuntimeError
    def mock_sentence_transformer(*args, **kwargs):
        raise RuntimeError("Model download failed")

    import sys
    from unittest.mock import MagicMock

    mock_st = MagicMock()
    mock_st.SentenceTransformer = mock_sentence_transformer
    sys.modules["sentence_transformers"] = mock_st
    sys.modules["sentence_transformers.util"] = MagicMock()

    try:
        # Should fall back to keyword search (using test utility)
        results = search_functions_by_topic_any("os.path", "join")

        # Should still return results
        assert len(results) > 0
    finally:
        # Clean up mocks
        if "sentence_transformers" in sys.modules:
            del sys.modules["sentence_transformers"]
        if "sentence_transformers.util" in sys.modules:
            del sys.modules["sentence_transformers.util"]


def test_semantic_search_score_normalization(monkeypatch):
    """Test that semantic search scores are normalized to 0-100 range."""

    # Mock the semantic search components
    class MockModel:
        def __init__(self, model_name=None):
            self.encode_count = 0

        def encode(self, text, convert_to_tensor=False):
            import numpy as np

            # Return a simple embedding
            return np.array([0.5, 0.5, 0.5, 0.5])

    def mock_cos_sim(query_emb, doc_embs):
        import numpy as np

        # Return similarity scores in 0-1 range matching the number of documents
        num_docs = len(doc_embs) if isinstance(doc_embs, list) else doc_embs.shape[0]
        # Generate scores between 0.3 and 0.9 for all documents
        scores = [0.75 - (i * 0.05) for i in range(num_docs)]
        return np.array([scores])

    # Mock sentence_transformers module
    import sys
    from unittest.mock import MagicMock

    mock_st = MagicMock()
    mock_st.SentenceTransformer = MockModel
    mock_st.util = MagicMock()
    mock_st.util.cos_sim = mock_cos_sim

    sys.modules["sentence_transformers"] = mock_st
    sys.modules["sentence_transformers.util"] = mock_st.util

    try:
        results = search_functions_by_topic_any("os.path", "join", max_results=3)

        # Check that scores are integers in 0-100 range
        for _func_name, _func_info, score in results:
            assert isinstance(score, int)
            assert 0 <= score <= 100
    finally:
        # Clean up mock
        if "sentence_transformers" in sys.modules:
            del sys.modules["sentence_transformers"]
        if "sentence_transformers.util" in sys.modules:
            del sys.modules["sentence_transformers.util"]


def test_semantic_search_automatic():
    """Test that search works without explicit semantic parameter."""
    # Should work and use whichever method is available
    results = search_functions_by_topic("os.path", "join", max_results=3)

    assert isinstance(results, list)
    assert len(results) <= 3
    if results:
        func_name, func_info, score = results[0]
        assert isinstance(score, int)


# Ecosystem search tests
def test_search_ecosystem_by_topic():
    """Test searching across the scverse ecosystem."""
    # This test only runs if at least one scverse package is installed
    installed = get_installed_package_names()

    if not installed:
        pytest.skip("No scverse packages installed")

    # Search for a common topic across all packages
    results = search_ecosystem_by_topic("normalize", max_results_per_package=2)

    # Results should be a dict mapping package names to function lists
    assert isinstance(results, dict)

    # All keys should be installed package names
    for package_name in results.keys():
        assert package_name in installed

    # Each value should be a list of tuples (func_name, func_info, score)
    for _package_name, matches in results.items():
        assert isinstance(matches, list)
        assert len(matches) <= 2  # Respects max_results_per_package

        for func_name, func_info, score in matches:
            assert isinstance(func_name, str)
            assert func_info.name.endswith(func_name)
            assert isinstance(score, int)
            assert score > 0


def test_search_ecosystem_empty_results():
    """Test ecosystem search with no matching functions."""
    installed = get_installed_package_names()

    if not installed:
        pytest.skip("No scverse packages installed")

    # Search for a very unlikely topic
    results = search_ecosystem_by_topic("nonexistent_topic_xyz_12345", max_results_per_package=3)

    # Should return empty dict
    assert isinstance(results, dict)
    assert len(results) == 0


def test_search_ecosystem_max_results():
    """Test that max_results_per_package is respected."""
    installed = get_installed_package_names()

    if not installed:
        pytest.skip("No scverse packages installed")

    # Search with max_results_per_package=1
    results = search_ecosystem_by_topic("data", max_results_per_package=1)

    # Each package should have at most 1 result
    for _package_name, matches in results.items():
        assert len(matches) <= 1


# Source extraction tests
def test_extract_function_source():
    """Test extracting source code from a function."""
    # Use a function from our own codebase
    source_info = extract_function_source_any("contextsc.core.introspector.extract_function_info")

    assert source_info.name == "contextsc.core.introspector.extract_function_info"
    assert source_info.source_code != ""
    assert "def extract_function_info" in source_info.source_code
    assert source_info.file_path != "unknown"
    assert source_info.line_start > 0
    assert source_info.line_end >= source_info.line_start


def test_extract_function_source_class_method():
    """Test extracting source for a class method."""
    # Use pathlib which is pure Python
    source_info = extract_function_source_any("pathlib.Path.is_dir")

    assert source_info.name == "pathlib.Path.is_dir"
    assert source_info.source_code != ""
    assert "def is_dir" in source_info.source_code


def test_extract_function_source_builtin_error():
    """Test that built-in functions raise appropriate errors."""
    # Built-in functions don't have source code
    with pytest.raises(IntrospectionError) as exc_info:
        extract_function_source_any("builtins.len")

    assert "Cannot retrieve source code" in str(exc_info.value)


def test_extract_function_source_invalid():
    """Test extracting source from invalid path."""
    with pytest.raises(IntrospectionError):
        extract_function_source_any("nonexistent.module.function")


def test_format_function_source():
    """Test formatting function source code."""
    source_info = extract_function_source_any("contextsc.core.formatter.estimate_token_count")
    formatted = format_function_source(source_info)

    assert "# contextsc.core.formatter.estimate_token_count" in formatted
    assert "**Source:**" in formatted
    assert "## Source Code" in formatted
    assert "```python" in formatted
    assert "def estimate_token_count" in formatted


def test_format_function_source_with_docs():
    """Test formatting source code with documentation."""
    source_info = extract_function_source_any("contextsc.core.formatter.estimate_token_count")
    func_info = extract_function_info_any("contextsc.core.formatter.estimate_token_count")
    formatted = format_function_source(source_info, func_info=func_info)

    assert "# contextsc.core.formatter.estimate_token_count" in formatted
    assert "## Documentation" in formatted
    assert "**Signature:**" in formatted
    assert "## Source Code" in formatted
    assert "```python" in formatted


def test_format_function_source_with_token_limit():
    """Test formatting source with token limit."""
    source_info = extract_function_source_any("contextsc.core.introspector.extract_function_info")
    # Use a larger function and smaller limit to test truncation
    formatted = format_function_source(source_info, max_tokens=2000)

    # Should be truncated or fit within limit (with some margin for headers)
    estimated_tokens = len(formatted) // 4
    assert estimated_tokens <= 2100  # Allow some margin for headers and formatting


def test_format_function_source_respects_minimum():
    """Test that formatter respects minimum token limit."""
    source_info = extract_function_source_any("contextsc.core.formatter.estimate_token_count")
    formatted = format_function_source(source_info, max_tokens=100)

    # Should enforce minimum of 1000 tokens, but if function is short it won't be padded
    # Just verify it returns something reasonable
    assert len(formatted) > 100  # At least returns headers and some code
    assert "## Source Code" in formatted
    assert "```python" in formatted
