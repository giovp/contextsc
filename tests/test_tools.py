"""Tests for MCP tools."""

import pytest
from fastmcp import Client

import contextsc


@pytest.mark.asyncio
async def test_resolve_scverse_package_list_all():
    """Test listing all scverse packages."""
    async with Client(contextsc.mcp) as client:
        result = await client.call_tool("resolve_scverse_package", {})
        assert result.data is not None
        assert "Installed Scverse Packages" in result.data
        # Should list all 6 packages
        assert "anndata" in result.data or "scanpy" in result.data or "mudata" in result.data


@pytest.mark.asyncio
async def test_resolve_scverse_package_specific():
    """Test resolving a specific package."""
    async with Client(contextsc.mcp) as client:
        result = await client.call_tool("resolve_scverse_package", {"package_name": "scanpy"})
        assert result.data is not None
        assert "scanpy" in result.data.lower()
        # Should show either installed or not installed status
        assert "Installed" in result.data or "Not Installed" in result.data


@pytest.mark.asyncio
async def test_resolve_scverse_package_invalid():
    """Test resolving an invalid package."""
    async with Client(contextsc.mcp) as client:
        result = await client.call_tool("resolve_scverse_package", {"package_name": "invalid_package"})
        assert result.data is not None
        assert "not a core scverse package" in result.data


@pytest.mark.asyncio
async def test_get_scverse_docs_builtin():
    """Test getting documentation for a built-in function."""
    async with Client(contextsc.mcp) as client:
        # Use os.path.join as a test since it's always available
        result = await client.call_tool("get_scverse_docs", {"function_path": "os.path.join"})
        assert result.data is not None
        # Could be docs or error about package not being scverse
        assert "os" in result.data


@pytest.mark.asyncio
async def test_get_scverse_docs_invalid():
    """Test getting docs for invalid path."""
    async with Client(contextsc.mcp) as client:
        result = await client.call_tool("get_scverse_docs", {"function_path": "nonexistent.function"})
        assert result.data is not None
        assert "Could not find" in result.data or "not installed" in result.data


@pytest.mark.asyncio
async def test_get_scverse_docs_with_token_limit():
    """Test getting docs with token limit."""
    async with Client(contextsc.mcp) as client:
        result = await client.call_tool("get_scverse_docs", {"function_path": "os.path.join", "max_tokens": 100})
        assert result.data is not None
        # Should either be truncated or within limit
        assert len(result.data) < 10000
