"""
InsureGraph AI — Quick Start Script
Runs the FastAPI server with all required modules.
"""
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    from backend.config import settings
    
    print("=" * 60)
    print("🛡️  InsureGraph AI — Starting Server")
    print(f"📡  Host: http://{settings.app_host}:{settings.app_port}")
    print(f"🔗  API Docs: http://localhost:{settings.app_port}/api/docs")
    print(f"🖥️   Frontend: http://localhost:{settings.app_port}/")
    print("=" * 60)
    
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
        log_level="info",
    )
