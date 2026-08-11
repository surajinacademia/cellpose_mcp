"""Auto-installer for cellpose-mcp in various AI applications."""

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any


def _resolve_executable(candidate: str | Path) -> str | None:
    """Return a canonical executable path without persisting a PATH lookup."""
    value = str(candidate)
    selected = value if os.path.isfile(value) else shutil.which(value)
    if selected is None:
        return None
    try:
        resolved = Path(selected).expanduser().resolve(strict=True)
    except OSError:
        return None
    if not resolved.is_file() or not os.access(resolved, os.X_OK):
        return None
    return str(resolved)


def find_conda_env(env_name: str = "Cellpose_mcp") -> str | None:
    """Find the path to a conda environment.

    Args:
        env_name: Name of the conda environment (default: Cellpose_mcp)

    Returns
    -------
        Path to the environment's Python executable, or None if not found
    """
    # Prefer the active environment's fixed prefix over a PATH lookup.
    if os.environ.get("CONDA_DEFAULT_ENV") == env_name:
        conda_prefix = os.environ.get("CONDA_PREFIX")
        if conda_prefix:
            active_python = Path(conda_prefix) / "bin" / "python"
            resolved = _resolve_executable(active_python)
            if resolved:
                return resolved

    # Try common conda locations
    home = Path.home()
    conda_paths = [
        home / "anaconda3" / "envs" / env_name / "bin" / "python",
        home / "miniconda3" / "envs" / env_name / "bin" / "python",
        home / "opt" / "anaconda3" / "envs" / env_name / "bin" / "python",
        home / ".conda" / "envs" / env_name / "bin" / "python",
    ]

    for conda_python_path in conda_paths:
        resolved = _resolve_executable(conda_python_path)
        if resolved:
            return resolved

    return None


def resolve_python_path(
    python_path: str | None = None,
    env_name: str = "Cellpose_mcp",
) -> str | None:
    """Resolve the Python executable to use for running cellpose_mcp.

    Precedence: explicit python_path > conda env named env_name > current interpreter.

    Args:
        python_path: Explicit path or executable name to resolve.
        env_name: Conda environment name to try when python_path is None.

    Returns
    -------
        Path to Python executable, or None only if explicit python_path was invalid.
    """
    if python_path is not None:
        return _resolve_executable(python_path)
    conda_python = find_conda_env(env_name)
    if conda_python is not None:
        return conda_python
    return _resolve_executable(sys.executable)


def verify_python_can_import(python_path: str) -> bool:
    """Return True if package metadata exists in an isolated interpreter."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)
    try:
        result = subprocess.run(
            [
                python_path,
                "-I",
                "-c",
                (
                    "import importlib.metadata; "
                    "importlib.metadata.distribution('cellpose-mcp')"
                ),
            ],
            capture_output=True,
            text=True,
            timeout=10,
            env=env,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def warn_if_python_unverified(python_path: str) -> None:
    """Print a user-facing warning when the selected Python cannot import package."""
    if verify_python_can_import(python_path):
        return
    print("⚠️  Warning: Could not verify cellpose_mcp in this Python.")
    print("   Ensure cellpose-mcp is installed: pip install cellpose-mcp")


def _prepare_config_path(config_path: Path, trusted_root: Path) -> Path | None:
    """Create safe parent directories and reject symlink traversal."""
    path = Path(os.path.abspath(config_path.expanduser()))
    root = Path(os.path.abspath(trusted_root.expanduser()))
    try:
        relative = path.relative_to(root)
    except ValueError:
        print(f"❌ Refusing to write config outside trusted root: {root}")
        return None

    if not root.is_dir() or root.is_symlink() or not relative.parts:
        print(f"❌ Invalid trusted config root: {root}")
        return None

    current = root
    try:
        for part in relative.parts[:-1]:
            current /= part
            if current.is_symlink():
                print(f"❌ Refusing to follow config symlink: {current}")
                return None
            if current.exists():
                if not current.is_dir():
                    print(f"❌ Config parent is not a directory: {current}")
                    return None
            else:
                current.mkdir(mode=0o700)

        if path.is_symlink():
            print(f"❌ Refusing to replace config symlink: {path}")
            return None
        if path.exists() and not path.is_file():
            print(f"❌ Config path is not a regular file: {path}")
            return None
    except OSError as exc:
        print(f"❌ Could not prepare config path: {exc}")
        return None
    return path


def _atomic_write_private(path: Path, text: str) -> bool:
    """Publish a complete mode-0600 config with atomic replacement."""
    temp_fd = -1
    temp_name = ""
    try:
        temp_fd, temp_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        os.fchmod(temp_fd, 0o600)
        with os.fdopen(temp_fd, "w", encoding="utf-8") as config_file:
            temp_fd = -1
            config_file.write(text)
            config_file.flush()
            os.fsync(config_file.fileno())
        if path.is_symlink():
            raise OSError(f"config path became a symlink: {path}")
        os.replace(temp_name, path)
        temp_name = ""
        return True
    except OSError as exc:
        print(f"❌ Error writing config file: {exc}")
        return False
    finally:
        if temp_fd >= 0:
            os.close(temp_fd)
        if temp_name:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass


def write_mcp_config(
    config_path: Path,
    python_path: str,
    *,
    trusted_root: Path,
) -> bool:
    """Safely write or update a standard MCP JSON config file."""
    safe_path = _prepare_config_path(config_path, trusted_root)
    if safe_path is None:
        return False

    config: dict[str, Any] = {}
    if safe_path.exists():
        try:
            parsed = json.loads(safe_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"❌ Existing config is unreadable; leaving it unchanged: {exc}")
            return False
        if not isinstance(parsed, dict):
            print("❌ Existing MCP config must be a JSON object.")
            return False
        config = parsed

    servers = config.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        print("❌ Existing mcpServers value must be a JSON object.")
        return False
    servers["cellpose"] = {
        "command": python_path,
        "args": ["-m", "cellpose_mcp"],
        "env": {
            "KMP_DUPLICATE_LIB_OK": "TRUE",
            "OMP_NUM_THREADS": "1",
        },
    }
    return _atomic_write_private(safe_path, json.dumps(config, indent=2) + "\n")


_TOML_MARKER = "__cellpose_mcp_table_marker__"


def _find_toml_marker(value: Any, path: tuple[str, ...] = ()) -> tuple[str, ...] | None:
    """Find the table path containing the synthetic TOML marker."""
    if isinstance(value, dict):
        if value.get(_TOML_MARKER) is True:
            return path
        for key, child in value.items():
            found = _find_toml_marker(child, (*path, str(key)))
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _find_toml_marker(child, path)
            if found is not None:
                return found
    return None


def _toml_table_path(line: str) -> tuple[str, ...] | None:
    """Parse one TOML table header, including quoted keys and comments."""
    if not line.lstrip().startswith("["):
        return None
    try:
        parsed = tomllib.loads(f"{line}\n{_TOML_MARKER} = true\n")
    except tomllib.TOMLDecodeError:
        return None
    return _find_toml_marker(parsed)


def _remove_toml_tables(
    text: str,
    table_names: set[tuple[str, ...]],
) -> str:
    """Remove full TOML table blocks by structurally parsed table path."""
    kept_lines: list[str] = []
    skip = False

    for line in text.splitlines():
        table_path = _toml_table_path(line)
        if table_path is not None:
            skip = table_path in table_names
            if skip:
                continue
        if not skip:
            kept_lines.append(line)

    return "\n".join(kept_lines).rstrip()


def _toml_string(value: str) -> str:
    """Format a Python string as a TOML basic string."""
    return json.dumps(value)


def _codex_mcp_block(python_path: str) -> str:
    """Return the Codex TOML block for this MCP server."""
    return "\n".join(
        [
            "[mcp_servers.cellpose]",
            f"command = {_toml_string(python_path)}",
            'args = ["-m", "cellpose_mcp"]',
            "",
            "[mcp_servers.cellpose.env]",
            'KMP_DUPLICATE_LIB_OK = "TRUE"',
            'OMP_NUM_THREADS = "1"',
        ]
    )


def write_codex_config(
    config_path: Path,
    python_path: str,
    *,
    trusted_root: Path,
) -> bool:
    """Safely write or update Codex CLI/App TOML MCP configuration."""
    safe_path = _prepare_config_path(config_path, trusted_root)
    if safe_path is None:
        return False
    existing = ""
    if safe_path.exists():
        try:
            existing = safe_path.read_text(encoding="utf-8")
            tomllib.loads(existing)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            print(f"❌ Existing Codex config is invalid; leaving it unchanged: {exc}")
            return False

    base = _remove_toml_tables(
        existing,
        {
            ("mcp_servers", "cellpose"),
            ("mcp_servers", "cellpose", "env"),
        },
    )
    block = _codex_mcp_block(python_path)
    config_text = f"{base}\n\n{block}\n" if base else f"{block}\n"
    try:
        tomllib.loads(config_text)
    except tomllib.TOMLDecodeError as exc:
        print(f"❌ Refusing to write invalid Codex config: {exc}")
        return False
    return _atomic_write_private(safe_path, config_text)


def get_cursor_config_path() -> Path | None:
    """Get the path to Cursor MCP configuration file.

    Returns
    -------
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
            Path.home()
            / ".config"
            / "Cursor"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "cline_mcp_settings.json",
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

    Returns
    -------
        Path to config file, or None if not found
    """
    system = platform.system()

    if system == "Darwin":  # macOS
        config_paths = [
            Path.home()
            / "Library"
            / "Application Support"
            / "Claude"
            / "claude_desktop_config.json",
        ]
    elif system == "Linux":
        config_paths = [
            Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
        ]
    elif system == "Windows":
        config_paths = [
            Path(os.environ.get("APPDATA", ""))
            / "Claude"
            / "claude_desktop_config.json",
        ]
    else:
        config_paths = [
            Path.home() / ".config" / "Claude" / "claude_desktop_config.json"
        ]

    for config_path in config_paths:
        if config_path.exists() or config_path.parent.exists():
            return config_path

    # Return the first path as default (will create if needed)
    return config_paths[0] if config_paths else None


def get_codex_config_path() -> Path:
    """Get the global Codex config file path."""
    return Path.home() / ".codex" / "config.toml"


def get_codex_project_config_path() -> Path:
    """Get the project-local Codex config file path."""
    return Path.cwd() / ".codex" / "config.toml"


def get_antigravity_config_path() -> Path | None:
    """Get the path to Antigravity (Google Gemini) MCP configuration file.

    Returns
    -------
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

    Returns
    -------
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


def install_for_claude_desktop(
    python_path: str | None = None, env_name: str = "Cellpose_mcp"
) -> bool:
    """Install cellpose-mcp configuration for Claude Desktop.

    Args:
        python_path: Path to Python executable (auto-detected if None)
        env_name: Name of conda environment to use (default: Cellpose_mcp)

    Returns
    -------
        True if installation succeeded, False otherwise
    """
    # Resolve Python path (conda env, or current interpreter)
    resolved = resolve_python_path(python_path, env_name)
    if resolved is None:
        print(f"❌ Invalid Python path: {python_path}")
        return False
    python_path = resolved

    warn_if_python_unverified(python_path)

    # Get config path
    config_path = get_claude_desktop_config_path()
    if config_path is None:
        print("❌ Could not determine Claude Desktop config file location.")
        return False

    if write_mcp_config(config_path, python_path, trusted_root=Path.home()):
        print("✅ Successfully configured cellpose-mcp for Claude Desktop!")
        print(f"   Config file: {config_path}")
        print(f"   Python: {python_path}")
        print("\n📝 Next steps:")
        print("   1. Restart Claude Desktop completely (close all windows)")
        print("   2. Ask Claude: 'List available Cellpose models'")
        print("   3. Start segmenting cells!")
        return True
    return False


def install_for_cursor(
    python_path: str | None = None, env_name: str = "Cellpose_mcp"
) -> bool:
    """Install cellpose-mcp configuration for Cursor.

    Args:
        python_path: Path to Python executable (auto-detected if None)
        env_name: Name of conda environment to use (default: Cellpose_mcp)

    Returns
    -------
        True if installation succeeded, False otherwise
    """
    # Resolve Python path (conda env, or current interpreter)
    resolved = resolve_python_path(python_path, env_name)
    if resolved is None:
        print(f"❌ Invalid Python path: {python_path}")
        return False
    python_path = resolved

    warn_if_python_unverified(python_path)

    # Get config path
    config_path = get_cursor_config_path()
    if config_path is None:
        print("❌ Could not determine Cursor config file location.")
        return False

    if write_mcp_config(config_path, python_path, trusted_root=Path.home()):
        print("✅ Successfully configured cellpose-mcp for Cursor!")
        print(f"   Config file: {config_path}")
        print(f"   Python: {python_path}")
        print("\n📝 Next steps:")
        print("   1. Restart Cursor IDE")
        print("   2. Ask your AI assistant: 'List available Cellpose models'")
        print("   3. Start segmenting cells!")
        return True
    return False


def install_for_antigravity(
    python_path: str | None = None, env_name: str = "Cellpose_mcp"
) -> bool:
    """Install cellpose-mcp configuration for Antigravity (Google Gemini).

    Args:
        python_path: Path to Python executable (auto-detected if None)
        env_name: Name of conda environment to use (default: Cellpose_mcp)

    Returns
    -------
        True if installation succeeded, False otherwise
    """
    # Resolve Python path (conda env, or current interpreter)
    resolved = resolve_python_path(python_path, env_name)
    if resolved is None:
        print(f"❌ Invalid Python path: {python_path}")
        return False
    python_path = resolved

    warn_if_python_unverified(python_path)

    # Get config path
    config_path = get_antigravity_config_path()
    if config_path is None:
        print("❌ Could not determine Antigravity config file location.")
        return False

    if write_mcp_config(config_path, python_path, trusted_root=Path.home()):
        print("✅ Successfully configured cellpose-mcp for Antigravity!")
        print(f"   Config file: {config_path}")
        print(f"   Python: {python_path}")
        print("\n📝 Next steps:")
        print("   1. Restart Antigravity (close and reopen the application)")
        print("   2. Ask: 'List available Cellpose models'")
        print("   3. Start segmenting cells!")
        return True
    return False


def install_for_vscode(
    python_path: str | None = None, env_name: str = "Cellpose_mcp"
) -> bool:
    """Install cellpose-mcp configuration for VS Code (Cline/Roo Cline extension).

    Args:
        python_path: Path to Python executable (auto-detected if None)
        env_name: Name of conda environment to use (default: Cellpose_mcp)

    Returns
    -------
        True if installation succeeded, False otherwise
    """
    # Resolve Python path (conda env, or current interpreter)
    resolved = resolve_python_path(python_path, env_name)
    if resolved is None:
        print(f"❌ Invalid Python path: {python_path}")
        return False
    python_path = resolved

    warn_if_python_unverified(python_path)

    # Get config path
    config_path = get_vscode_config_path()
    if config_path is None:
        print("❌ Could not determine VS Code config file location.")
        return False

    if write_mcp_config(config_path, python_path, trusted_root=Path.home()):
        print("✅ Successfully configured cellpose-mcp for VS Code (Cline/Roo Cline)!")
        print(f"   Config file: {config_path}")
        print(f"   Python: {python_path}")
        print("\n📝 Next steps:")
        print("   1. Restart VS Code completely (close all windows)")
        print("   2. Open Cline/Roo Cline extension")
        print("   3. Ask: 'List available Cellpose models'")
        print("   4. Start segmenting cells!")
        return True
    return False


def install_for_project_mcp(
    app_name: str,
    python_path: str | None = None,
    env_name: str = "Cellpose_mcp",
) -> bool:
    """Install a project-local ``.mcp.json`` for Claude Code."""
    resolved = resolve_python_path(python_path, env_name)
    if resolved is None:
        print(f"❌ Invalid Python path: {python_path}")
        return False
    python_path = resolved

    warn_if_python_unverified(python_path)

    project_root = Path.cwd()
    config_path = project_root / ".mcp.json"
    if write_mcp_config(config_path, python_path, trusted_root=project_root):
        print(f"✅ Successfully configured cellpose-mcp for {app_name}!")
        print(f"   Config file: {config_path}")
        print(f"   Python: {python_path}")
        print("\n📝 Next steps:")
        print("   1. Restart or reload your AI coding app")
        print("   2. Ask: 'List available Cellpose models'")
        print("   3. Start segmenting cells!")
        return True
    return False


def install_for_codex(
    app_name: str,
    python_path: str | None = None,
    env_name: str = "Cellpose_mcp",
    *,
    project: bool = False,
) -> bool:
    """Install Codex CLI/App TOML MCP configuration."""
    resolved = resolve_python_path(python_path, env_name)
    if resolved is None:
        print(f"❌ Invalid Python path: {python_path}")
        return False
    python_path = resolved

    warn_if_python_unverified(python_path)

    config_path = (
        get_codex_project_config_path() if project else get_codex_config_path()
    )
    trusted_root = Path.cwd() if project else Path.home()
    if write_codex_config(config_path, python_path, trusted_root=trusted_root):
        print(f"✅ Successfully configured cellpose-mcp for {app_name}!")
        print(f"   Config file: {config_path}")
        print(f"   Python: {python_path}")
        print("\n📝 Next steps:")
        print("   1. Restart or reload Codex")
        print("   2. Run: codex mcp list")
        print("   3. Ask: 'List available Cellpose models'")
        return True
    return False


def main() -> None:
    """Main CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description=(
            "Install cellpose-mcp for AI applications. Supported apps: cursor, "
            "claude-desktop, antigravity, vscode, cline, roo-cline, "
            "cline-vscode, cline-cursor, claude-code, codex, codex-cli, "
            "codex-desktop, codex-project."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "app",
        help="AI application to configure, for example claude-desktop or cursor",
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

    app_name = args.app.lower()

    if app_name in ["cursor", "cline-cursor"]:
        success = install_for_cursor(args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    elif app_name == "claude-desktop":
        success = install_for_claude_desktop(args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    elif app_name == "antigravity":
        success = install_for_antigravity(args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    elif app_name in ["vscode", "cline", "roo-cline", "cline-vscode"]:
        success = install_for_vscode(args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    elif app_name == "claude-code":
        success = install_for_project_mcp(args.app, args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    elif app_name in ["codex", "codex-cli", "codex-desktop"]:
        success = install_for_codex(args.app, args.python_path, args.env_name)
        sys.exit(0 if success else 1)
    elif app_name == "codex-project":
        success = install_for_codex(
            args.app,
            args.python_path,
            args.env_name,
            project=True,
        )
        sys.exit(0 if success else 1)
    else:
        print(f"❌ Support for '{args.app}' is coming soon!")
        print(
            "   For now, please configure manually in your application's MCP settings."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
