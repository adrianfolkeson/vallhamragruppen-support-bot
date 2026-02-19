"""
SUPPORT STARTER AI - MAIN ENTRY POINT
=====================================
Railway-compatible entry point
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and expose the app
from server import app

# For Railway deployment, also expose the app directly
__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
