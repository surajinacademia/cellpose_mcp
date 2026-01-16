"""Auto-installer for cellpose-mcp in various AI applications."""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_conda_env(env_name: str = "image_analysis") -> str | None:
    """Find the path to a conda environment.

    Args:
        env_name: Name of the conda environment

    Returns:
        Path to the environment's Python executable, or None if not found
    """
    # Check if we're already in the environment
    if os.environ.get("CONDA_DEFAULT_ENV") == env_name:
        python_path = shutil.which("python")
        if python_path:
            return python_path

    # Try common conda locations
    home = Path.home()
    conda_paths = [
        home / "anaconda3" / "envs" / env_name / "bin" / "python",
        home / "miniconda3" / "envs" / env_name / "bin" / "python",
        home / "opt" / "anaconda3" / "envs" / env_name / "bin" / "python",
        home / ".conda" / "envs" / env_name / "bin" / "python",
    ]

    for python_path in conda_paths:
        if python_path.exists():
            return str(python_path)

    # Try using conda command
    try:
        result = subprocess.run(
            ["conda", "env", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            envs_data = json.loads(result.stdout)
            envs = envs_data.get("envs", [])
            for env_path in envs:
                if Path(env_path).name == env_name or env_name in env_path:
                    python_path = Path(env_path) / "bin" / "python"
                    if python_path.exists():
                        return str(python_path)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass

    return None


def get_cursor_config_path() -> Path | None:
    """Get the path to Cursor MCP configuration file.

    Returns:
        Path to config file, or None if not found
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        config_paths = [
            Path.home()
            / "Library"
            / "Application Support"
            / "Cursor"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "cline_mcp_settings.json",
            Path.home() / ".cursor" / "mcp_settings.json",
        ]
    elif system == "Linux":
        config_paths = [
            Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "cline_mcp_settings.json",
            Path.home() / ".cursor" / "mcp_settings.json",
        ]
    elif system == "Windows":
        config_paths = [
            Path.home()
            / "AppData"
            / "Roaming"
            / "Cursor"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "cline_mcp_settings.json",
            Path.home() / ".cursor" / "mcp_settings.json",
        ]
    else:
        config_paths = [Path.home() / ".cursor" / "mcp_settings.json"]

    for config_path in config_paths:
        if config_path.exists() or config_path.parent.exists():
            return config_path

    # Return the first path as default (will create if needed)
    return config_paths[0]


def install_for_cursor(python_path: str | None = None, env_name: str = "image_analysis") -> bool:
    """Install cellpose-mcp configuration for Cursor.

    Args:
        python_path: Path to Python executable (auto-detected if None)
        env_name: Name of conda environment to use

    Returns:
        True if installation succeeded, False otherwise
    """
    # Find Python path
    if python_path is None:
        python_path = find_conda_env(env_name)
        if python_path is None:
            print(f"❌ Could not find '{env_name}' conda environment.")
            print(f"   Please activate it or provide the Python path manually.")
            return False

    # Verify Python can import cellpose_mcp
    try:
        result = subprocess.run(
            [python_path, "-m", "cellpose_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # Even if it fails, we'll still add it (might work after restart)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"⚠️  Warning: Could not verify cellpose_mcp installation in {python_path}")
        print(f"   Make sure cellpose-mcp is installed: pip install -e .")

    # Get config path
    config_path = get_cursor_config_path()
    if config_path is None:
        print("❌ Could not determine Cursor config file location.")
        return False

    # Create directory if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing config or create new
    config: dict[str, Any] = {}
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"⚠️  Warning: Could not read existing config, creating new one.")

    # Ensure mcpServers exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}

    # Add or update cellpose server config
    config["mcpServers"]["cellpose"] = {
        "command": python_path,
        "args": ["-m", "cellpose_mcp"],
        "env": {},
    }

    # Write config
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Successfully configured cellpose-mcp for Cursor!")
        print(f"   Config file: {config_path}")
        print(f"   Python: {python_path}")
        print(f"\n📝 Next steps:")
        print(f"   1. Restart Cursor IDE")
        print(f"   2. Ask your AI assistant: 'List available Cellpose models'")
        print(f"   3. Start segmenting cells!")
        return True
    except IOError as e:
        print(f"❌ Error writing config file: {e}")
        return False


def main() -> None:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Install cellpose-mcp for AI applications")
    parser.add_argument(
        "app",
        choices=["cursor", "claude-desktop", "claude-code", "cline-vscode", "cline-cursor"],
        help="AI application to configure",
    )
    parser.add_argument(
        "--python-path",
        type=str,
        help="Path to Python executable (auto-detected if not provided)",
    )
    parser.add_argument(
        "--env-name",
        type=str,
        default="image_analysis",
        help="Name of conda environment (default: image_analysis)",
    )

    args = parser.parse_args()

    if args.app == "cursor":
        success = install_for_cursor(args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Support for '{args.app}' is coming soon!")
        print(f"   For now, please configure manually in your application's MCP settings.")
        sys.exit(1)


if __name__ == "__main__":
    main()
