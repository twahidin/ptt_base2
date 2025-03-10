from fasthtml.common import APIRouter
from .leonardo import routes as leonardo_routes
from .stability import routes as stability_routes
from .html_5 import routes as html_5_routes
from .auth import routes as auth_routes
from .home_page import routes as home_page_routes
from .lea_chatbot import routes as lea_chatbot_routes

def setup_routes(app):
    # Create routers for each module

    leonardo_router = APIRouter(prefix="")
    stability_router = APIRouter(prefix="")
    auth_router = APIRouter(prefix="")
    html_5_router = APIRouter(prefix="")
    lea_chatbot_router = APIRouter(prefix="")
    # Add routes to routers

    leonardo_routes(leonardo_router)
    stability_routes(stability_router)
    auth_routes(auth_router)
    html_5_routes(html_5_router)
    lea_chatbot_routes(lea_chatbot_router)
    # Add routers to app

    leonardo_router.to_app(app)
    stability_router.to_app(app)
    auth_router.to_app(app)
    html_5_router.to_app(app)
    lea_chatbot_router.to_app(app)