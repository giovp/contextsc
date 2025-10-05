from importlib.metadata import version

from contextsc.main import run_app
from contextsc.mcp import mcp

__version__ = version("contextsc")

__all__ = ["mcp", "run_app", "__version__"]


if __name__ == "__main__":
    run_app()
