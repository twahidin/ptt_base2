from fasthtml.common import APIRouter
from .leonardo import routes as leonardo_routes
from .stability import routes as stability_routes
from .html_5 import routes as html_5_routes
from .auth import routes as auth_routes
from .home_page import routes as home_page_routes
from .lea_chatbot import routes as lea_chatbot_routes
from .token_routes import routes as token_routes
from .primary_school import routes as primary_school_routes
from .secondary_school import routes as secondary_school_routes
from .jc_ci import routes as jc_ci_routes
from .api import routes as api_routes
from .acp_edit import routes as acp_edit_routes

def setup_routes(app):
    # Create routers for each module

    leonardo_router = APIRouter(prefix="")
    stability_router = APIRouter(prefix="")
    auth_router = APIRouter(prefix="")
    html_5_router = APIRouter(prefix="")
    lea_chatbot_router = APIRouter(prefix="")
    token_router = APIRouter(prefix="")
    primary_school_router = APIRouter(prefix="")
    secondary_school_router = APIRouter(prefix="")
    jc_ci_router = APIRouter(prefix="")
    api_router = APIRouter(prefix="")
    acp_edit_router = APIRouter(prefix="")
    
    # Add routes to routers

    leonardo_routes(leonardo_router)
    stability_routes(stability_router)
    auth_routes(auth_router)
    html_5_routes(html_5_router)
    lea_chatbot_routes(lea_chatbot_router)
    token_routes(token_router)
    primary_school_routes(primary_school_router)
    secondary_school_routes(secondary_school_router)
    jc_ci_routes(jc_ci_router)
    api_routes(api_router)
    acp_edit_routes(acp_edit_router)
    
    # Add routers to app

    leonardo_router.to_app(app)
    stability_router.to_app(app)
    auth_router.to_app(app)
    html_5_router.to_app(app)
    lea_chatbot_router.to_app(app)
    token_router.to_app(app)
    primary_school_router.to_app(app)
    secondary_school_router.to_app(app)
    jc_ci_router.to_app(app)
    api_router.to_app(app)
    acp_edit_router.to_app(app)