from fastmcp import FastMCP

mcp: FastMCP = FastMCP(
    name="contextsc",
    instructions="A very interesting piece of code",
    on_duplicate_tools="error",
)
