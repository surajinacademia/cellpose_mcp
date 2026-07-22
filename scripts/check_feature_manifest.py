#!/usr/bin/env python3
"""Validate bootstrap structure or report deterministic release blockers."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

FEATURE_MANIFEST_MODULE_NAME = "cellpose_mcp.release.feature_manifest"


def load_feature_manifest_module() -> ModuleType:
    """Load the real release contract without running the legacy package."""
    loaded = sys.modules.get(FEATURE_MANIFEST_MODULE_NAME)
    if loaded is not None:
        return loaded

    root = Path(__file__).resolve().parents[1]
    package_dir = root / "src/cellpose_mcp"
    package_spec = importlib.util.spec_from_file_location(
        "cellpose_mcp",
        package_dir / "__init__.py",
        submodule_search_locations=[str(package_dir)],
    )
    if package_spec is None or package_spec.loader is None:
        raise RuntimeError("cannot create the cellpose_mcp package spec")
    package = importlib.util.module_from_spec(package_spec)
    sys.modules[package_spec.name] = package

    module_path = package_dir / "release/feature_manifest.py"
    module_spec = importlib.util.spec_from_file_location(
        FEATURE_MANIFEST_MODULE_NAME,
        module_path,
    )
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("cannot create the feature manifest module spec")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


FEATURE_MANIFEST = load_feature_manifest_module()
load_feature_manifest = FEATURE_MANIFEST.load_feature_manifest
release_gate_failures = FEATURE_MANIFEST.release_gate_failures


def main() -> int:
    """Run development validation or intentionally blocked release mode."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", action="store_true")
    args = parser.parse_args()
    manifest = load_feature_manifest()
    failures = release_gate_failures(manifest)
    if args.release:
        for failure in failures:
            print(f"{failure.code}: {failure.subject}: {failure.message}")
        return 1
    print(f"bootstrap manifest valid; release blockers: {len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
