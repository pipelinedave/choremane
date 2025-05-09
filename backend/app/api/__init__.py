from app.api.routes import api_router
from app.api.mcp_routes import router as mcp_router

# Import these modules to register their routes with the API router
import app.api.chores_archived_endpoint
import app.api.chore_counts_endpoint

__all__ = ["api_router", "mcp_router"]