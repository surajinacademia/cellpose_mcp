#!/usr/bin/env python3
"""Validate bootstrap structure or report deterministic release blockers."""

from __future__ import annotations

import argparse

from cellpose_mcp.release.feature_manifest import (
    load_feature_manifest,
    release_gate_failures,
)


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
