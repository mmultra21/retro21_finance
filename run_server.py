#!/usr/bin/env python3
"""
Simple server runner - automatically uses the right setup based on installed dependencies
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_dependencies():
    """Check which dependencies are available."""
    deps = {
        'fastapi': False,
        'uvicorn': False,
        'duckdb': False,
        'beancount': False,
        'pydantic': False
    }

    for dep in deps.keys():
        try:
            __import__(dep)
            deps[dep] = True
        except ImportError:
            pass

    return deps

def main():
    """Start the appropriate server based on available dependencies."""

    print("🔍 Checking dependencies...")
    deps = check_dependencies()

    # Check core dependencies
    if not deps['fastapi'] or not deps['uvicorn']:
        print("\n❌ Missing core dependencies!")
        print("   Install with: pip install fastapi uvicorn pydantic requests")
        sys.exit(1)

    print("✅ Core dependencies found")

    # Determine which server to use
    if deps['duckdb'] and deps['beancount']:
        print("✅ Full dependencies found - using complete application")
        try:
            # Try to import the full app
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "main",
                "personal-finance/api/main.py"
            )
            if spec and spec.loader:
                main_module = importlib.util.module_from_spec(spec)
                sys.modules["main"] = main_module
                spec.loader.exec_module(main_module)
                app = main_module.app
                use_full = True
        except Exception as e:
            print(f"⚠️  Could not load full app: {e}")
            print("📝 Falling back to simplified server...")
            use_full = False
    else:
        print("⚠️  Missing optional dependencies (DuckDB, Beancount)")
        print("   Using simplified test server")
        use_full = False

    # Use test server if full app not available
    if not use_full:
        import test_api_server
        app = test_api_server.app

    # Start server
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    print(f"\n🚀 Starting server...")
    print(f"   URL: http://{host}:{port}")
    print(f"   Docs: http://{host}:{port}/docs")
    print(f"   Press CTRL+C to stop\n")

    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
