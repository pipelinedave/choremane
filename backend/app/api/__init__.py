from app.api.routes import api_router
from app.api.mcp_routes import router as mcp_router

# Import these modules to register their routes with the API router
# Using redundant aliases to satisfy linters (these are side-effect imports)
import app.api.chores_archived_endpoint as chores_archived_endpoint  # noqa: F401
import app.api.chore_counts_endpoint as chore_counts_endpoint  # noqa: F401

__all__ = ["api_router", "mcp_router"]
