from fastmcp import FastMCP

mcp: FastMCP = FastMCP(
    name="contextsc",
    instructions="BioContextAI MCP server for scverse ecosystem documentation. Provides version-specific documentation and code examples for scanpy, anndata, mudata, squidpy, and other scverse packages.",
    on_duplicate_tools="error",
)
