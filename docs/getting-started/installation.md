# Installation

## Local Installation (using uv)

```bash
git clone https://github.com/codeintegrity-ai/tramlines-gateway.git
cd tramlines-gateway
uv sync
```

## Verify Installation

```bash
tl --list-policies
```

## Usage

Run with your existing MCP_CONFIG (same as used with Claude, Cursor, etc.):

```bash
export MCP_CONFIG='{"mcpServers":{"server1":{"command":"python","args":["server.py"]}}}'
tl --use-policy block_pii_in_tool_args
```

Or with Docker:

```bash
docker run -e MCP_CONFIG='{"mcpServers":{"server1":{"command":"python","args":["server.py"]}}}' \
  ghcr.io/codeintegrity-ai/tramlines-gateway:latest uv run tl --use-policy block_pii_in_tool_args
```

## Advanced Usage

For custom policies, use `--policy-path` to load your own policy file:

```bash
tl --policy-path /path/to/your/custom_policy.py
```

With Docker (mount your policy file):

```bash
docker run -v /path/to/your/policy.py:/app/policy.py \
  -e MCP_CONFIG='{"mcpServers":{"server1":{"command":"python","args":["server.py"]}}}' \
  ghcr.io/codeintegrity-ai/tramlines-gateway:latest uv run tl --policy-path /app/policy.py
```
