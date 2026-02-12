"""Auto-installer for cellpose-mcp in various AI applications."""

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def find_conda_env(env_name: str = "Cellpose_mcp") -> str | None:
    """Find the path to a conda environment.

    Args:
        env_name: Name of the conda environment (default: Cellpose_mcp)

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


def resolve_python_path(
    python_path: str | None = None,
    env_name: str = "Cellpose_mcp",
) -> str | None:
    """Resolve the Python executable to use for running cellpose_mcp.

    Precedence: explicit python_path > conda env named env_name > current interpreter.

    Args:
        python_path: Explicit path to Python (if provided, used as-is).
        env_name: Conda environment name to try when python_path is None.

    Returns:
        Path to Python executable, or None only if explicit python_path was invalid.
    """
    if python_path is not None:
        if os.path.isfile(python_path) or shutil.which(python_path):
            return python_path
        return None
    conda_python = find_conda_env(env_name)
    if conda_python is not None:
        return conda_python
    return sys.executable


def get_cursor_config_path() -> Path | None:
    """Get the path to Cursor MCP configuration file.

    Returns:
        Path to config file, or None if not found
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        config_paths = [
            Path.home() / ".cursor" / "mcp.json",  # Primary location for Cursor
            Path.home()
            / "Library"
            / "Application Support"
            / "Cursor"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "cline_mcp_settings.json",
            Path.home() / ".cursor" / "mcp_settings.json",  # Fallback
        ]
    elif system == "Linux":
        config_paths = [
            Path.home() / ".cursor" / "mcp.json",  # Primary location for Cursor
            Path.home() / ".config" / "Cursor" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "cline_mcp_settings.json",
            Path.home() / ".cursor" / "mcp_settings.json",  # Fallback
        ]
    elif system == "Windows":
        config_paths = [
            Path.home() / ".cursor" / "mcp.json",  # Primary location for Cursor
            Path.home()
            / "AppData"
            / "Roaming"
            / "Cursor"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "cline_mcp_settings.json",
            Path.home() / ".cursor" / "mcp_settings.json",  # Fallback
        ]
    else:
        config_paths = [Path.home() / ".cursor" / "mcp.json"]

    for config_path in config_paths:
        if config_path.exists() or config_path.parent.exists():
            return config_path

    # Return the first path as default (will create if needed)
    return config_paths[0]


def get_claude_desktop_config_path() -> Path | None:
    """Get the path to Claude Desktop MCP configuration file.

    Returns:
        Path to config file, or None if not found
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        config_paths = [
            Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        ]
    elif system == "Linux":
        config_paths = [
            Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
        ]
    elif system == "Windows":
        config_paths = [
            Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
        ]
    else:
        config_paths = [Path.home() / ".config" / "Claude" / "claude_desktop_config.json"]

    for config_path in config_paths:
        if config_path.exists() or config_path.parent.exists():
            return config_path

    # Return the first path as default (will create if needed)
    return config_paths[0] if config_paths else None


def get_antigravity_config_path() -> Path | None:
    """Get the path to Antigravity (Google Gemini) MCP configuration file.

    Returns:
        Path to config file, or None if not found
    """
    # Antigravity uses the same config path on all platforms
    config_path = Path.home() / ".gemini" / "antigravity" / "mcp_config.json"

    if config_path.exists() or config_path.parent.exists():
        return config_path

    # Return the path as default (will create if needed)
    return config_path


def get_vscode_config_path() -> Path | None:
    """Get the path to VS Code MCP configuration file (for Cline/Roo Cline extension).

    Returns:
        Path to config file, or None if not found
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        config_paths = [
            Path.home()
            / "Library"
            / "Application Support"
            / "Code"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "cline_mcp_settings.json",
            Path.home()
            / "Library"
            / "Application Support"
            / "Code"
            / "User"
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",
        ]
    elif system == "Linux":
        config_paths = [
            Path.home()
            / ".config"
            / "Code"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "cline_mcp_settings.json",
            Path.home()
            / ".config"
            / "Code"
            / "User"
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",
        ]
    elif system == "Windows":
        config_paths = [
            Path.home()
            / "AppData"
            / "Roaming"
            / "Code"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "cline_mcp_settings.json",
            Path.home()
            / "AppData"
            / "Roaming"
            / "Code"
            / "User"
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",
        ]
    else:
        config_paths = [
            Path.home()
            / ".config"
            / "Code"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "cline_mcp_settings.json"
        ]

    for config_path in config_paths:
        if config_path.exists() or config_path.parent.exists():
            return config_path

    # Return the first path as default (will create if needed)
    return config_paths[0]


def install_for_claude_desktop(python_path: str | None = None, env_name: str = "Cellpose_mcp") -> bool:
    """Install cellpose-mcp configuration for Claude Desktop.

    Args:
        python_path: Path to Python executable (auto-detected if None)
        env_name: Name of conda environment to use (default: Cellpose_mcp)

    Returns:
        True if installation succeeded, False otherwise
    """
    # Resolve Python path (conda env, or current interpreter)
    resolved = resolve_python_path(python_path, env_name)
    if resolved is None:
        print(f"❌ Invalid Python path: {python_path}")
        return False
    python_path = resolved

    # Verify Python can import cellpose_mcp
    try:
        subprocess.run(
            [python_path, "-m", "cellpose_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"⚠️  Warning: Could not verify cellpose_mcp in this Python.")
        print(f"   Ensure cellpose-mcp is installed: pip install cellpose-mcp")

    # Get config path
    config_path = get_claude_desktop_config_path()
    if config_path is None:
        print("❌ Could not determine Claude Desktop config file location.")
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
    # Include environment variables to fix OpenMP threading conflicts
    config["mcpServers"]["cellpose"] = {
        "command": python_path,
        "args": ["-m", "cellpose_mcp"],
        "env": {
            "KMP_DUPLICATE_LIB_OK": "TRUE",
            "OMP_NUM_THREADS": "1",
        },
    }

    # Write config
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Successfully configured cellpose-mcp for Claude Desktop!")
        print(f"   Config file: {config_path}")
        print(f"   Python: {python_path}")
        print(f"\n📝 Next steps:")
        print(f"   1. Restart Claude Desktop completely (close all windows)")
        print(f"   2. Ask Claude: 'List available Cellpose models'")
        print(f"   3. Start segmenting cells!")
        return True
    except IOError as e:
        print(f"❌ Error writing config file: {e}")
        return False


def install_for_cursor(python_path: str | None = None, env_name: str = "Cellpose_mcp") -> bool:
    """Install cellpose-mcp configuration for Cursor.

    Args:
        python_path: Path to Python executable (auto-detected if None)
        env_name: Name of conda environment to use (default: Cellpose_mcp)

    Returns:
        True if installation succeeded, False otherwise
    """
    # Resolve Python path (conda env, or current interpreter)
    resolved = resolve_python_path(python_path, env_name)
    if resolved is None:
        print(f"❌ Invalid Python path: {python_path}")
        return False
    python_path = resolved

    # Verify Python can import cellpose_mcp
    try:
        subprocess.run(
            [python_path, "-m", "cellpose_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"⚠️  Warning: Could not verify cellpose_mcp in this Python.")
        print(f"   Ensure cellpose-mcp is installed: pip install cellpose-mcp")

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
    # Include environment variables to fix OpenMP threading conflicts
    config["mcpServers"]["cellpose"] = {
        "command": python_path,
        "args": ["-m", "cellpose_mcp"],
        "env": {
            "KMP_DUPLICATE_LIB_OK": "TRUE",
            "OMP_NUM_THREADS": "1",
        },
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


def install_for_antigravity(python_path: str | None = None, env_name: str = "Cellpose_mcp") -> bool:
    """Install cellpose-mcp configuration for Antigravity (Google Gemini).

    Args:
        python_path: Path to Python executable (auto-detected if None)
        env_name: Name of conda environment to use (default: Cellpose_mcp)

    Returns:
        True if installation succeeded, False otherwise
    """
    # Resolve Python path (conda env, or current interpreter)
    resolved = resolve_python_path(python_path, env_name)
    if resolved is None:
        print(f"❌ Invalid Python path: {python_path}")
        return False
    python_path = resolved

    # Verify Python can import cellpose_mcp
    try:
        subprocess.run(
            [python_path, "-m", "cellpose_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"⚠️  Warning: Could not verify cellpose_mcp in this Python.")
        print(f"   Ensure cellpose-mcp is installed: pip install cellpose-mcp")

    # Get config path
    config_path = get_antigravity_config_path()
    if config_path is None:
        print("❌ Could not determine Antigravity config file location.")
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
    # Include environment variables to fix OpenMP threading conflicts
    config["mcpServers"]["cellpose"] = {
        "command": python_path,
        "args": ["-m", "cellpose_mcp"],
        "env": {
            "KMP_DUPLICATE_LIB_OK": "TRUE",
            "OMP_NUM_THREADS": "1",
        },
    }

    # Write config
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Successfully configured cellpose-mcp for Antigravity!")
        print(f"   Config file: {config_path}")
        print(f"   Python: {python_path}")
        print(f"\n📝 Next steps:")
        print(f"   1. Restart Antigravity (close and reopen the application)")
        print(f"   2. Ask: 'List available Cellpose models'")
        print(f"   3. Start segmenting cells!")
        return True
    except IOError as e:
        print(f"❌ Error writing config file: {e}")
        return False


def install_for_vscode(python_path: str | None = None, env_name: str = "Cellpose_mcp") -> bool:
    """Install cellpose-mcp configuration for VS Code (Cline/Roo Cline extension).

    Args:
        python_path: Path to Python executable (auto-detected if None)
        env_name: Name of conda environment to use (default: Cellpose_mcp)

    Returns:
        True if installation succeeded, False otherwise
    """
    # Resolve Python path (conda env, or current interpreter)
    resolved = resolve_python_path(python_path, env_name)
    if resolved is None:
        print(f"❌ Invalid Python path: {python_path}")
        return False
    python_path = resolved

    # Verify Python can import cellpose_mcp
    try:
        subprocess.run(
            [python_path, "-m", "cellpose_mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print(f"⚠️  Warning: Could not verify cellpose_mcp in this Python.")
        print(f"   Ensure cellpose-mcp is installed: pip install cellpose-mcp")

    # Get config path
    config_path = get_vscode_config_path()
    if config_path is None:
        print("❌ Could not determine VS Code config file location.")
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
    # Include environment variables to fix OpenMP threading conflicts
    config["mcpServers"]["cellpose"] = {
        "command": python_path,
        "args": ["-m", "cellpose_mcp"],
        "env": {
            "KMP_DUPLICATE_LIB_OK": "TRUE",
            "OMP_NUM_THREADS": "1",
        },
    }

    # Write config
    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Successfully configured cellpose-mcp for VS Code (Cline/Roo Cline)!")
        print(f"   Config file: {config_path}")
        print(f"   Python: {python_path}")
        print(f"\n📝 Next steps:")
        print(f"   1. Restart VS Code completely (close all windows)")
        print(f"   2. Open Cline/Roo Cline extension")
        print(f"   3. Ask: 'List available Cellpose models'")
        print(f"   4. Start segmenting cells!")
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
        choices=["cursor", "claude-desktop", "antigravity", "claude-code", "vscode", "cline", "roo-cline", "cline-vscode", "cline-cursor"],
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
        default="Cellpose_mcp",
        help="Name of conda environment (default: Cellpose_mcp)",
    )

    args = parser.parse_args()

    if args.app in ["cursor", "cline-cursor"]:
        success = install_for_cursor(args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    elif args.app == "claude-desktop":
        success = install_for_claude_desktop(args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    elif args.app == "antigravity":
        success = install_for_antigravity(args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    elif args.app in ["vscode", "cline", "roo-cline", "cline-vscode"]:
        success = install_for_vscode(args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Support for '{args.app}' is coming soon!")
        print(f"   For now, please configure manually in your application's MCP settings.")
        sys.exit(1)


if __name__ == "__main__":
    main()
