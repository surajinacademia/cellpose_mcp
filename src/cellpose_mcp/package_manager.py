"""Package management tools for dynamic installation of image processing packages."""

import os
import subprocess
import sys
from typing import Any

# Fix OpenMP threading conflicts
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")


class PackageManager:
    """Manages dynamic installation of Python packages for image processing."""

    # Whitelist of safe packages for image processing
    ALLOWED_PACKAGES = {
        "scikit-image",
        "opencv-python",
        "opencv-contrib-python",
        "pillow",
        "scipy",
        "pandas",
        "matplotlib",
        "seaborn",
        "plotly",
        "imageio",
        "tifffile",
        "napari",
        "cellprofiler",
        "scikit-learn",
        "pytest",
        "jupyter",
        "ipython",
        "notebook",
    }

    @staticmethod
    def is_package_allowed(package_name: str) -> bool:
        """Check if a package is in the allowed list.

        Args:
            package_name: Name of the package to check

        Returns:
            True if package is allowed, False otherwise
        """
        # Extract base package name (remove version specifiers)
        base_name = package_name.split("==")[0].split(">=")[0].split("<=")[0].strip()
        return base_name.lower() in PackageManager.ALLOWED_PACKAGES

    @staticmethod
    def install_package(
        package_name: str,
        version: str | None = None,
        force: bool = False,
    ) -> dict[str, Any]:
        """Install a Python package using pip.

        Args:
            package_name: Name of the package to install
            version: Optional specific version to install
            force: Whether to force reinstall if already installed

        Returns:
            Dictionary with installation results
        """
        # Security check
        if not PackageManager.is_package_allowed(package_name):
            return {
                "success": False,
                "error": f"Package '{package_name}' is not in the allowed list for security reasons",
                "allowed_packages": list(PackageManager.ALLOWED_PACKAGES),
            }

        try:
            # Construct package specifier
            if version:
                package_spec = f"{package_name}=={version}"
            else:
                package_spec = package_name

            # Construct pip command
            cmd = [sys.executable, "-m", "pip", "install"]

            if force:
                cmd.append("--force-reinstall")

            cmd.append(package_spec)

            # Run pip install
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            return {
                "success": result.returncode == 0,
                "package": package_spec,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Installation timed out (exceeded 5 minutes)",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def list_installed_packages() -> dict[str, Any]:
        """List all installed Python packages.

        Returns:
            Dictionary with list of installed packages
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                import json

                packages = json.loads(result.stdout)
                return {
                    "success": True,
                    "packages": packages,
                    "count": len(packages),
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def check_package_installed(package_name: str) -> dict[str, Any]:
        """Check if a package is installed and get its version.

        Args:
            package_name: Name of the package to check

        Returns:
            Dictionary with installation status and version
        """
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package_name],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Parse output
                info = {}
                for line in result.stdout.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        info[key.strip().lower()] = value.strip()

                return {
                    "installed": True,
                    "package": package_name,
                    "version": info.get("version", "unknown"),
                    "location": info.get("location", "unknown"),
                }
            else:
                return {
                    "installed": False,
                    "package": package_name,
                }

        except Exception as e:
            return {"installed": False, "package": package_name, "error": str(e)}

    @staticmethod
    def get_allowed_packages() -> list[str]:
        """Get the list of packages allowed for installation.

        Returns:
            List of allowed package names
        """
        return sorted(list(PackageManager.ALLOWED_PACKAGES))
