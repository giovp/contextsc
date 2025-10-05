# contextsc

[![BioContextAI - Registry](https://img.shields.io/badge/Registry-package?style=flat&label=BioContextAI&labelColor=%23fff&color=%233555a1&link=https%3A%2F%2Fbiocontext.ai%2Fregistry)](https://biocontext.ai/registry)
[![Tests][badge-tests]][tests]
[![Documentation][badge-docs]][documentation]

[badge-tests]: https://img.shields.io/github/actions/workflow/status/giovp/contextsc/test.yaml?branch=main
[badge-docs]: https://img.shields.io/readthedocs/contextsc

BioContextAI MCP server for scverse ecosystem documentation. Provides version-specific documentation and code examples for scanpy, anndata, mudata, squidpy, and other scverse packages.

## Getting started

Please refer to the [documentation][],
in particular, the [API documentation][].

You can also find the project on [BioContextAI](https://biocontext.ai), the community-hub for biomedical MCP servers: [contextsc on BioContextAI](https://biocontext.ai/registry/giovp/contextsc).

## Installation

You need to have Python 3.11 or newer installed on your system.
If you don't have Python installed, we recommend installing [uv][].

There are several alternative options to install contextsc:

1. Use `uvx` to run it immediately:

```bash
uvx contextsc
```

2. Include it in one of various clients that supports the `mcp.json` standard, please use:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "uvx",
      "args": ["contextsc"],
      "env": {
        "UV_PYTHON": "3.12" // or required version
      }
    }
  }
}
```

3. Install it with `uv`:

```bash
uv pip install contextsc
```

4. Install it through `pip`:

```bash
pip install contextsc
```

5. Install the latest development version:

```bash
uv pip install git+https://github.com/giovp/contextsc.git@main
```

## Contact

If you found a bug, please use the [issue tracker][].

## Citation

> t.b.a

[uv]: https://github.com/astral-sh/uv
[issue tracker]: https://github.com/giovp/contextsc/issues
[tests]: https://github.com/giovp/contextsc/actions/workflows/test.yaml
[documentation]: https://contextsc.readthedocs.io
[changelog]: https://contextsc.readthedocs.io/en/latest/changelog.html
[api documentation]: https://contextsc.readthedocs.io/en/latest/api.html
[pypi]: https://pypi.org/project/contextsc
