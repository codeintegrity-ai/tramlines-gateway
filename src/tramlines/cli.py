"""
Tramlines CLI Entrypoint.

This module contains the command-line interface for running the Tramlines proxy.
It handles argument parsing, configuration loading, and server initialization.
"""

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from tramlines.guardrail.dsl.evaluator import load_policy_from_file
from tramlines.guardrail.dsl.types import Policy
from tramlines.logger import logger
from tramlines.proxy import create_guarded_proxy

POLICY_DIR = Path(__file__).parent / "guardrail" / "policies"


def _discover_policies() -> dict[str, Policy]:
    """Dynamically discover and load all available guardrail policies."""
    discovered: dict[str, Policy] = {}
    if not POLICY_DIR.is_dir():
        return discovered

    for f in POLICY_DIR.glob("*.py"):
        if f.name.startswith("_"):
            continue

        module_name = f.stem
        try:
            module = importlib.import_module(
                f"tramlines.guardrail.policies.{module_name}"
            )
            if hasattr(module, "policy") and isinstance(module.policy, Policy):
                discovered[module_name] = module.policy
        except ImportError as e:
            logger.warning(
                f"POLICY_DISCOVERY_FAIL | Could not import policy '{module_name}': {e}"
            )
    return discovered


def _load_mcp_config(config_path: str | None) -> dict[str, Any]:
    """Load MCP configuration from file path or environment variable."""
    mcp_config: dict[str, Any] = {}

    # Try config file first if provided
    if config_path:
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                print(f"❌ Config file not found: {config_path}", file=sys.stderr)
                sys.exit(1)

            with config_file.open() as f:
                mcp_config = json.load(f)
            logger.info(f"CONFIG_LOAD | Loaded MCP config from file: {config_path}")
        except json.JSONDecodeError as exc:
            print(
                f"❌ Invalid JSON in config file {config_path}: {exc}", file=sys.stderr
            )
            sys.exit(1)
        except Exception as exc:
            print(
                f"❌ Failed to read config file {config_path}: {exc}", file=sys.stderr
            )
            sys.exit(1)

    # Fall back to environment variable if no config file
    elif os.environ.get("MCP_CONFIG"):
        try:
            mcp_config = json.loads(os.environ["MCP_CONFIG"])
            logger.info(
                "CONFIG_LOAD | Loaded MCP config from MCP_CONFIG environment variable"
            )
        except json.JSONDecodeError as exc:
            print(f"❌ Invalid MCP_CONFIG JSON: {exc}", file=sys.stderr)
            sys.exit(1)

    # Exit if no configuration found
    else:
        print(
            "❌ No MCP configuration found. Provide either:\n"
            "   - --config-path pointing to a JSON file, or\n"
            "   - MCP_CONFIG environment variable with JSON configuration",
            file=sys.stderr,
        )
        sys.exit(1)

    if not mcp_config:
        print("❌ Empty MCP configuration provided.", file=sys.stderr)
        sys.exit(1)

    for name, cfg in mcp_config.items():
        _handle_docker_env_vars(name, cfg)

    return mcp_config


def _handle_docker_env_vars(name: str, cfg: dict[str, Any]) -> None:
    """Handle Docker environment variable conversion."""
    if cfg.get("command") != "docker" or not isinstance(cfg.get("env"), dict):
        return

    env_pairs = [flag for k, v in cfg["env"].items() for flag in ("-e", f"{k}={v}")]
    args = list(cfg.get("args", []))
    insert_at = (args.index("run") + 1) if "run" in args else 0
    cfg["args"] = args[:insert_at] + env_pairs + args[insert_at:]

    logger.debug(
        f"MCP_CONFIG_SANITIZE | {name} | injected {len(env_pairs) // 2} docker env vars into args"
    )


def _combine_policies(
    custom_policy_path: str,
    use_policies: list[str],
    available_policies: dict[str, Policy],
) -> Policy | None:
    """Load policies from path and names, then combine them into a single policy."""
    all_rules = []
    loaded_policy_names = []

    # 1. Load from --policy-path
    if custom_policy_path:
        try:
            custom_policy = load_policy_from_file(custom_policy_path)
            all_rules.extend(custom_policy.rules)
            loaded_policy_names.append(f"Custom ({custom_policy.name})")
        except Exception as e:
            logger.error(
                f"POLICY_LOAD_FAIL | Failed to load custom policy from {custom_policy_path}: {e}"
            )
            raise

    # 2. Load from --use-policy
    for name in use_policies:
        if name in available_policies:
            policy = available_policies[name]
            all_rules.extend(policy.rules)
            loaded_policy_names.append(policy.name)
        else:
            logger.warning(
                f"POLICY_NOT_FOUND | Built-in policy '{name}' not found. Skipping."
            )

    if not all_rules:
        logger.info("POLICY_LOAD | No policies specified or loaded. Tracking only.")
        return None

    # 3. Combine into a single policy
    final_policy = Policy(
        name="Combined Guardrail Policy",
        description="A combination of all enabled guardrail policies.",
        rules=all_rules,
    )

    logger.info(
        f"POLICY_LOAD | Successfully loaded and combined {len(loaded_policy_names)} policies:"
    )
    for name in loaded_policy_names:
        logger.info(f"  - {name}")

    return final_policy


def _list_policies(available_policies: dict[str, Policy]) -> None:
    """Prints a formatted list of available policies and exits."""
    print("\nAvailable Guardrail Policies:")
    print("----------------------------------------------------------------------")
    if not available_policies:
        print("  No built-in policies found.")
    else:
        for module_name, p in sorted(available_policies.items()):
            print(f"\n  Module:      {module_name}")
            print(f"  Name:        {p.name}")
            print(f"  Description: {p.description}")
    print("\n----------------------------------------------------------------------")
    print("Use the 'Module' name with the --use-policy flag to enable a policy.")
    sys.exit(0)


def app() -> None:  # pragma: no cover
    """CLI entrypoint for running the Tramlines proxy server."""

    available_policies = _discover_policies()

    parser = argparse.ArgumentParser(
        description="Tramlines MCP Proxy (GuardedFastMCPProxy)"
    )
    parser.add_argument(
        "--config-path",
        type=str,
        help="Path to JSON configuration file (alternative to MCP_CONFIG env var)",
    )
    parser.add_argument(
        "--policy-path",
        type=str,
        default="",
        help="Path to a custom Python policy file (*.py)",
    )
    parser.add_argument(
        "--use-policy",
        nargs="*",
        default=[],
        help=f"Names of built-in policies to use (e.g., {' '.join(available_policies.keys())})",
    )
    parser.add_argument(
        "--list-policies",
        action="store_true",
        help="List all available built-in policies and exit",
    )
    parser.add_argument(
        "--disable-tools",
        nargs="*",
        default=[],
        help="List of tool names to disable at discovery",
    )
    args = parser.parse_args()

    if args.list_policies:
        _list_policies(available_policies)

    # Load MCP configuration from file or environment
    mcp_config = _load_mcp_config(args.config_path)
    logger.info(f"CONFIG_LOADED | MCP Config: {mcp_config}")

    # Show disabled tools info
    if args.disable_tools:
        print(
            f"🚫 Disabling {len(args.disable_tools)} tools: {args.disable_tools}",
            file=sys.stderr,
        )

    # Load and combine selected policies
    policy = _combine_policies(
        custom_policy_path=args.policy_path,
        use_policies=args.use_policy,
        available_policies=available_policies,
    )

    # Create the guarded proxy directly
    proxy = create_guarded_proxy(
        mcp_config=mcp_config, policy=policy, disabled_tools=args.disable_tools
    )

    print("🚀 Tramlines Proxy Ready", file=sys.stderr)
    print("   Transport: stdio", file=sys.stderr)
    proxy.run(transport="stdio")
