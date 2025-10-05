"""Formatting utilities for presenting documentation to LLMs."""

from dataclasses import dataclass
from enum import Enum

from .introspector import FunctionInfo


class SectionPriority(Enum):
    """Priority levels for documentation sections."""

    CRITICAL = 1  # Must always include
    HIGH = 2  # Include if possible
    MEDIUM = 3  # Include if space allows
    LOW = 4  # Include only if plenty of space


@dataclass
class DocumentSection:
    """A section of documentation with priority and content."""

    name: str
    content: str
    priority: SectionPriority
    tokens: int


# Minimum token limits (like Context7)
MINIMUM_TOKENS = 1000
DEFAULT_TOKENS = 10000


def estimate_token_count(text: str) -> int:
    """Estimate token count for text.

    Uses a simple heuristic: ~4 characters per token.

    Parameters
    ----------
    text : str
        Text to estimate tokens for.

    Returns
    -------
    int
        Estimated token count.
    """
    return len(text) // 4


def parse_numpy_docstring(docstring: str) -> dict[str, str]:
    """Parse numpy-style docstring into sections.

    Parameters
    ----------
    docstring : str
        The docstring to parse.

    Returns
    -------
    dict[str, str]
        Dictionary mapping section names to content.
    """
    sections = {}
    current_section = "Summary"
    current_content = []

    # Common numpy docstring section headers
    section_headers = {
        "Parameters",
        "Returns",
        "Yields",
        "Raises",
        "Warns",
        "Warnings",
        "See Also",
        "Notes",
        "References",
        "Examples",
        "Attributes",
        "Methods",
    }

    lines = docstring.split("\n")

    for line in lines:
        # Check if line is a section header (followed by dashes)
        stripped = line.strip()
        if stripped in section_headers:
            # Save previous section
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            # Start new section
            current_section = stripped
            current_content = []
        elif stripped.startswith("---") or stripped.startswith("==="):
            # Skip separator lines
            continue
        else:
            current_content.append(line)

    # Save final section
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def filter_docstring_by_topic(docstring: str, topic: str) -> str:
    """Filter docstring sections by topic relevance.

    Parameters
    ----------
    docstring : str
        The docstring to filter.
    topic : str
        Topic keyword to filter by.

    Returns
    -------
    str
        Filtered docstring with relevant sections.
    """
    if not topic:
        return docstring

    sections = parse_numpy_docstring(docstring)
    topic_lower = topic.lower()

    # Always include summary
    filtered = [sections.get("Summary", "")]

    # Add sections that mention the topic
    for section_name, section_content in sections.items():
        if section_name == "Summary":
            continue  # Already added

        # Check if topic appears in section
        if topic_lower in section_content.lower():
            filtered.append(f"\n## {section_name}\n{section_content}")

    result = "\n".join(filtered)
    return result if result.strip() else docstring  # Fallback to full docstring if nothing matched


def build_documentation_sections(func_info: FunctionInfo, topic: str = "") -> list[DocumentSection]:
    """Build prioritized documentation sections.

    Parameters
    ----------
    func_info : FunctionInfo
        Function information.
    topic : str, default: ""
        Optional topic for filtering.

    Returns
    -------
    list[DocumentSection]
        List of documentation sections with priorities.
    """
    sections = []

    # 1. Header (CRITICAL - always include)
    header = f"# {func_info.name}\n\n**Module:** `{func_info.module}`"
    sections.append(DocumentSection("Header", header, SectionPriority.CRITICAL, estimate_token_count(header)))

    # 2. Signature (CRITICAL - always include)
    signature = f"## Signature\n\n```python\n{func_info.name}{func_info.signature}\n```"
    sections.append(DocumentSection("Signature", signature, SectionPriority.CRITICAL, estimate_token_count(signature)))

    # 3. Parameters (CRITICAL - always include if present)
    if func_info.parameters:
        param_lines = ["## Parameters", ""]
        for param_name, param_type in func_info.parameters.items():
            param_lines.append(f"- **{param_name}**: `{param_type}`")
        params_text = "\n".join(param_lines)
        sections.append(
            DocumentSection("Parameters", params_text, SectionPriority.CRITICAL, estimate_token_count(params_text))
        )

    # 4. Returns (HIGH priority)
    if func_info.return_annotation != "Any":
        returns = f"## Returns\n\n`{func_info.return_annotation}`"
        sections.append(DocumentSection("Returns", returns, SectionPriority.HIGH, estimate_token_count(returns)))

    # 5. Docstring (MEDIUM to HIGH priority depending on topic filtering)
    docstring_content = func_info.docstring
    if topic:
        docstring_content = filter_docstring_by_topic(docstring_content, topic)
        priority = SectionPriority.HIGH  # Filtered docstring is high priority
    else:
        priority = SectionPriority.MEDIUM

    doc_text = f"## Documentation\n\n{docstring_content}"
    sections.append(DocumentSection("Documentation", doc_text, priority, estimate_token_count(doc_text)))

    return sections


def format_function_docs(func_info: FunctionInfo, max_tokens: int = DEFAULT_TOKENS, topic: str = "") -> str:
    """Format function information for LLM consumption with intelligent truncation.

    Parameters
    ----------
    func_info : FunctionInfo
        Function information to format.
    max_tokens : int, default: 10000
        Maximum tokens to return. Minimum 1000 tokens enforced.
    topic : str, default: ""
        Optional topic to filter documentation by.

    Returns
    -------
    str
        Formatted documentation string.
    """
    # Enforce minimum token limit (like Context7)
    max_tokens = max(max_tokens, MINIMUM_TOKENS)

    # Build sections with priorities
    sections = build_documentation_sections(func_info, topic)

    # Include sections based on priority until token limit reached
    result_sections = []
    tokens_used = 0

    # First pass: include all CRITICAL sections
    for section in sections:
        if section.priority == SectionPriority.CRITICAL:
            result_sections.append(section.content)
            tokens_used += section.tokens

    # Check if we're already over limit with just critical sections
    if tokens_used >= max_tokens:
        result = "\n\n".join(result_sections)
        return result + "\n\n[... other sections truncated due to token limit ...]"

    # Second pass: include HIGH priority sections if they fit
    for section in sections:
        if section.priority == SectionPriority.HIGH:
            if tokens_used + section.tokens <= max_tokens:
                result_sections.append(section.content)
                tokens_used += section.tokens
            else:
                # Truncate this section to fit
                remaining_tokens = max_tokens - tokens_used
                if remaining_tokens > 100:  # Only include if meaningful amount left
                    char_limit = remaining_tokens * 4
                    truncated = section.content[:char_limit] + "\n\n[... truncated ...]"
                    result_sections.append(truncated)
                break

    # Third pass: include MEDIUM priority if space remains
    if tokens_used < max_tokens:
        for section in sections:
            if section.priority == SectionPriority.MEDIUM:
                if tokens_used + section.tokens <= max_tokens:
                    result_sections.append(section.content)
                    tokens_used += section.tokens
                else:
                    # Truncate to fit remaining space
                    remaining_tokens = max_tokens - tokens_used
                    if remaining_tokens > 100:
                        char_limit = remaining_tokens * 4
                        truncated = section.content[:char_limit] + "\n\n[... truncated ...]"
                        result_sections.append(truncated)
                    break

    return "\n\n".join(result_sections)


def format_package_list(packages: list[tuple[str, str, bool]]) -> str:
    """Format list of packages for LLM consumption.

    Parameters
    ----------
    packages : list[tuple[str, str, bool]]
        List of (package_name, version, is_installed) tuples.

    Returns
    -------
    str
        Formatted package list.
    """
    lines = ["# Installed Scverse Packages", ""]

    installed = [p for p in packages if p[2]]
    not_installed = [p for p in packages if not p[2]]

    if installed:
        lines.append("## Available Packages")
        lines.append("")
        for name, version, _ in installed:
            lines.append(f"- **{name}** (v{version})")
        lines.append("")

    if not_installed:
        lines.append("## Not Installed")
        lines.append("")
        for name, _, _ in not_installed:
            lines.append(f"- {name}")
        lines.append("")

    if not installed:
        lines.append("⚠️ No scverse packages are currently installed in this environment.")
        lines.append("")
        lines.append("Install packages with: `pip install <package-name>`")

    return "\n".join(lines)


def format_function_list(module_path: str, functions: list[str]) -> str:
    """Format list of functions in a module.

    Parameters
    ----------
    module_path : str
        Module path.
    functions : list[str]
        List of function names.

    Returns
    -------
    str
        Formatted function list.
    """
    lines = [
        f"# Functions in {module_path}",
        "",
        f"Found {len(functions)} public functions:",
        "",
    ]

    for func in functions:
        lines.append(f"- `{module_path}.{func}`")

    return "\n".join(lines)
