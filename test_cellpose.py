#!/usr/bin/env python3
"""Test script to verify Cellpose installation and MCP server setup."""

import sys
from pathlib import Path

def test_imports():
    """Test if required packages can be imported."""
    print("Testing imports...")
    try:
        import cellpose
        version = getattr(cellpose, '__version__', 'unknown')
        print(f"✅ cellpose imported (version: {version})")
    except ImportError as e:
        print(f"❌ cellpose not found: {e}")
        return False
    
    try:
        from cellpose import models, io
        print("✅ cellpose.models and cellpose.io imported successfully")
    except ImportError as e:
        print(f"❌ cellpose modules not found: {e}")
        return False
    
    try:
        from cellpose.denoise import DenoiseModel, CellposeDenoiseModel
        print("✅ cellpose.denoise imported successfully")
    except ImportError as e:
        print(f"⚠️  cellpose.denoise not available (may be older version): {e}")
    
    try:
        import fastmcp
        print(f"✅ fastmcp imported successfully")
    except ImportError as e:
        print(f"❌ fastmcp not found: {e}")
        print("   Install with: pip install fastmcp")
        return False
    
    try:
        import numpy
        print(f"✅ numpy version: {numpy.__version__}")
    except ImportError as e:
        print(f"❌ numpy not found: {e}")
        return False
    
    try:
        import imageio
        print(f"✅ imageio imported successfully")
    except ImportError as e:
        print(f"❌ imageio not found: {e}")
        return False
    
    return True

def test_mcp_server():
    """Test if MCP server can be initialized."""
    print("\nTesting MCP server...")
    try:
        # Add src to path
        src_path = Path(__file__).parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        from cellpose_mcp.server import mcp
        print("✅ MCP server initialized successfully")
        
        # Check if tools are registered
        # Note: tools are registered via decorators, so we can't easily count them
        print("✅ Tools module loaded")
        return True
    except Exception as e:
        print(f"❌ MCP server initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cellpose_model():
    """Test if Cellpose model can be loaded."""
    print("\nTesting Cellpose model loading...")
    try:
        from cellpose import models
        
        # Try loading a small model
        print("   Loading cyto2 model...")
        model = models.CellposeModel(model_type="cyto2", gpu=False)
        print("✅ Cellpose model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to load Cellpose model: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Cellpose MCP Server - Installation Test")
    print("=" * 60)
    
    all_passed = True
    
    all_passed &= test_imports()
    all_passed &= test_mcp_server()
    all_passed &= test_cellpose_model()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Cellpose MCP is ready to use.")
        print("\nNext steps:")
        print("  1. Install the package: pip install -e .")
        print("  2. Configure for Cursor: cellpose-mcp-install cursor")
        print("  3. Restart Cursor and start segmenting!")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
