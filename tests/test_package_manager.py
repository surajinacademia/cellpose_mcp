"""Unit tests for package_manager module."""

import os

import pytest

# Set OpenMP env vars before imports
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from cellpose_mcp.package_manager import PackageManager


class TestPackageManager:
    """Tests for PackageManager class."""

    def test_is_package_allowed(self):
        """Test checking if package is allowed."""
        assert PackageManager.is_package_allowed("scikit-image")
        assert PackageManager.is_package_allowed("opencv-python")
        assert PackageManager.is_package_allowed("pillow")
        assert not PackageManager.is_package_allowed("malicious-package")
        assert not PackageManager.is_package_allowed("unknown-lib")

    def test_is_package_allowed_with_version(self):
        """Test checking allowed packages with version specifiers."""
        assert PackageManager.is_package_allowed("scikit-image==0.20.0")
        assert PackageManager.is_package_allowed("pillow>=9.0.0")
        assert PackageManager.is_package_allowed("scipy<=1.10.0")

    def test_get_allowed_packages(self):
        """Test getting list of allowed packages."""
        allowed = PackageManager.get_allowed_packages()
        assert isinstance(allowed, list)
        assert len(allowed) > 0
        assert "scikit-image" in allowed
        assert "opencv-python" in allowed
        assert "cellprofiler" in allowed

    def test_install_disallowed_package(self):
        """Test that disallowed packages cannot be installed."""
        result = PackageManager.install_package("malicious-package")
        assert result["success"] is False
        assert "not in the allowed list" in result["error"]

    def test_check_package_installed_pytest(self):
        """Test checking if pytest is installed (should be in test env)."""
        result = PackageManager.check_package_installed("pytest")
        assert result["installed"] is True
        assert "version" in result

    def test_check_package_installed_nonexistent(self):
        """Test checking non-existent package."""
        result = PackageManager.check_package_installed("nonexistent-package-xyz")
        assert result["installed"] is False

    def test_list_installed_packages(self):
        """Test listing installed packages."""
        result = PackageManager.list_installed_packages()
        assert result["success"] is True
        assert "packages" in result
        assert isinstance(result["packages"], list)
        assert result["count"] > 0


@pytest.mark.unit
class TestPackageManagerUnit:
    """Unit tests that don't require network or installation."""

    def test_allowed_packages_is_set(self):
        """Test that ALLOWED_PACKAGES is properly defined."""
        assert isinstance(PackageManager.ALLOWED_PACKAGES, set)
        assert len(PackageManager.ALLOWED_PACKAGES) > 10

    def test_allowed_packages_contains_image_libs(self):
        """Test that common image processing libraries are allowed."""
        required_libs = {
            "scikit-image",
            "opencv-python",
            "pillow",
            "imageio",
            "scipy",
            "matplotlib",
        }
        assert required_libs.issubset(PackageManager.ALLOWED_PACKAGES)
