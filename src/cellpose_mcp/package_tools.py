"""MCP tools for dynamic package installation and management."""

import os

# Fix OpenMP threading conflicts
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from typing import Any

from cellpose_mcp.mcp_instance import mcp
from cellpose_mcp.package_manager import PackageManager


@mcp.tool()
def install_package(
    package_name: str,
    version: str | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Install a Python package for image processing.

    This tool allows dynamic installation of approved image processing packages.
    Only packages from a whitelist can be installed for security.

    Args:
        package_name: Name of the package to install (e.g., 'scikit-image')
        version: Optional specific version to install (e.g., '0.20.0')
        force: Whether to force reinstall if already installed

    Returns:
        Dictionary with installation results including success status and output
    """
    try:
        result = PackageManager.install_package(package_name, version, force)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_installed_packages() -> dict[str, Any]:
    """List all installed Python packages in the environment.

    Returns:
        Dictionary with list of installed packages and their versions
    """
    try:
        result = PackageManager.list_installed_packages()
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def check_package_installed(package_name: str) -> dict[str, Any]:
    """Check if a specific package is installed and get its version.

    Args:
        package_name: Name of the package to check

    Returns:
        Dictionary with installation status, version, and location
    """
    try:
        result = PackageManager.check_package_installed(package_name)
        return result
    except Exception as e:
        return {"installed": False, "package": package_name, "error": str(e)}


@mcp.tool()
def list_allowed_packages() -> dict[str, Any]:
    """List all packages allowed for installation.

    This tool shows the whitelist of packages that can be safely installed
    for image processing tasks.

    Returns:
        Dictionary with list of allowed packages
    """
    try:
        allowed = PackageManager.get_allowed_packages()
        return {
            "success": True,
            "allowed_packages": allowed,
            "count": len(allowed),
            "note": "Only these packages can be installed for security reasons",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
