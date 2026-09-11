"""Main entry point for starting the Context Sync MCP server."""

import uvicorn
from src.config import settings

def start():
    """Start the Uvicorn server."""
    uvicorn.run(
        "src.api:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )

if __name__ == "__main__":
    start()
