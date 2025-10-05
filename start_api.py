#!/usr/bin/env python3
"""
Startup script for Personal Finance API
Handles proper module imports and path setup
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables
os.environ.setdefault('ENVIRONMENT', 'development')
os.environ.setdefault('HERMES_URL', 'http://127.0.0.1:11434')

# Import and run the main API
if __name__ == "__main__":
    import uvicorn

    # Check if we can import the full app
    try:
        # Add personal-finance directory to path
        personal_finance_path = project_root / "personal-finance"
        sys.path.insert(0, str(personal_finance_path))
        
        from api.main import app
        use_full_app = True
        print("✅ Starting full Personal Finance API with all features")
    except ImportError as e:
        print(f"⚠️  Cannot load full app (missing dependencies: {e})")
        print("📝 Starting simplified API server instead...")

        # Import the test server instead
        sys.path.insert(0, str(project_root))
        import test_api_server
        app = test_api_server.app
        use_full_app = False

    # Configuration
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    host = "0.0.0.0" if is_production else "127.0.0.1"
    port = int(os.getenv("PORT", "8000"))

    print(f"\n🚀 Starting server on http://{host}:{port}")
    print(f"   Mode: {'Production' if is_production else 'Development'}")
    print(f"   API Docs: http://{host}:{port}/docs")
    print(f"   LLM: {os.getenv('HERMES_URL', 'http://127.0.0.1:11434')}")
    if not use_full_app:
        print(f"   ⚠️  Running in simplified mode (limited features)")
    print()

    # Start server
    # Disable reload if running as background service (no TTY)
    enable_reload = (not is_production) and sys.stdin.isatty()

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=enable_reload,
        log_level="info"
    )
