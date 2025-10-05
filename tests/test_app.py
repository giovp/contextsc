import pytest
from fastmcp import Client

import contextsc


def test_package_has_version():
    """Testing package version exist."""
    assert contextsc.__version__ is not None


@pytest.mark.asyncio
async def test_mcp_server():
    """Testing MCP server."""
    async with Client(contextsc.mcp) as client:
        result = await client.call_tool("greet", {"name": "test"})
        assert result.data == "Hello, test!"
