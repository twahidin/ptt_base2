from fasthtml.common import APIRouter
from .leonardo import routes as leonardo_routes
from .stability import routes as stability_routes
from .auth import routes as auth_routes

def setup_routes(app):
    # Create routers for each module
    leonardo_router = APIRouter(prefix="")
    stability_router = APIRouter(prefix="")
    auth_router = APIRouter(prefix="")
    
    # Add routes to routers
    leonardo_routes(leonardo_router)
    stability_routes(stability_router)
    auth_routes(auth_router)
    
    # Add routers to app
    leonardo_router.to_app(app)
    stability_router.to_app(app)
    auth_router.to_app(app)