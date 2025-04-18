from fasthtml.common import *
from starlette.responses import RedirectResponse
from routes import setup_routes
from starlette.middleware.sessions import SessionMiddleware
import token_count
import atexit

# Create the app with authentication
login_redir = RedirectResponse('/login', status_code=303)

def user_auth_before(req, sess):
    # Get auth from session
    auth = req.scope['auth'] = sess.get('auth', None)
    
    # List of paths that don't require authentication
    public_paths = ['/', '/login']
    
    # Allow access to public paths
    if req.url.path in public_paths:
        return None
        
    # Require authentication for all other paths
    if not auth:
        return login_redir
    return None

beforeware = Beforeware(
    user_auth_before,
    skip=[
        r'/favicon\.ico',
        r'/static/.*',
        r'.*\.css',
        r'.*\.js',
        '/login'
    ]
)

# Create app with session support
app, rt = fast_app(
    before=beforeware,
    secret_key="your-secret-key-here"  # Add a secret key for session
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-here",  # Use the same secret key
    session_cookie="fastapi_session",
    max_age=14 * 24 * 60 * 60,  # 14 days in seconds
)

# Set up all routes from the routes module
setup_routes(app)

# Initialize token database
token_count.init_db()

# Add styling for the layout and components
@rt("/")
def head():
    return Style("""
        .app-container {
            width: 100%;
            min-height: 100vh;
        }
        
        .header-grid {
            padding: 1rem;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--muted-border-color);
        }
        
        .main-layout {
            display: flex;
            gap: 2rem;
            padding: 0 1rem;
        }
        
        .side-menu-container {
            width: 250px;
            flex-shrink: 0;
        }
        
        .content-area {
            flex-grow: 1;
            padding: 1rem;
            background: var(--card-background-color);
            border-radius: 8px;
            min-height: 500px;
        }
        
        .side-menu {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .side-menu li {
            margin-bottom: 0.5rem;
        }
        
        .side-menu .menu-item {
            display: block;
            padding: 0.75rem 1rem;
            color: var(--primary);
            text-decoration: none;
            border-radius: 6px;
            transition: all 0.2s ease;
        }
        
        .side-menu .menu-item:hover {
            background: var(--primary);
            color: var(--primary-inverse);
        }
        
        .side-menu .menu-item.active {
            background: var(--primary);
            color: var(--primary-inverse);
        }
        
        .error {
            color: #842029;
            background-color: #f8d7da;
            border: 1px solid #f5c2c7;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
    """)

# Base route for index page

@rt("/")
def get(req):
    auth = req.session.get('auth')
    
    if not auth:
        # Show login page if not authenticated
        return Titled("MOE Prompt Testing Tool",
            Container(
                Div(
                    P("Please log in with your PTT credentials to continue."),
                    A("Login", href="/login", cls="button login-button"),
                    cls="login-container"
                )
            ),
           Link(rel="stylesheet", href="/static/css/styles.css")
        )
    
    # Show main application layout if authenticated
    return Titled("MOE PPT Version 2",
        Link(rel="stylesheet", href="/static/css/styles.css"),
        Container(
            Div(
                Grid(
                    Div(
                        H1("MOE PPT Version 2"),
                        Div(f"Welcome {auth}", cls="welcome-text"),
                        cls="header-title"
                    ),
                    Div(A("Logout", href="/logout", cls="logout-btn"), 
                        style="text-align: right"),
                    cls="header-grid"
                ),
                Div(
                    Div(create_side_menu(), cls="side-menu-container"),
                    Div(
                        Div(
                            H2("Welcome to MOE PPT Version 2"),
                            P("Select a generator from the menu on the left to begin."),
                            cls="menu-content"
                        ),
                        id="content-area", 
                        cls="content-area"
                    ),
                    cls="main-layout"
                ),
                cls="app-container"
            )
        )
    )
        
def create_side_menu(active_menu=None):
    menu_items = [
        #("menuA", "Leonardo AI Generator"),
        #("menuB", "Stability AI Generator"),
        #("menuC", "Stability AI Video Generator"),
        ("menuD", "HTML5 Interactive Editor"),
        #("menuE", "Lea Chatbot"),
        ("tokens", "Token Usage Monitoring"),

    ]
    
    return Ul(*[
        Li(
            A(name, 
              href=f"#{id_}", 
              hx_get=f"/{id_}",
              hx_target="#content-area",
              cls=f"menu-item {'active' if id_ == active_menu else ''}"),
        ) for id_, name in menu_items
    ], cls="side-menu")

# Example route for menu content
@rt("/menuA")
def get():
    return Div(
        H2("Leonardo AI Generator"),
        P("This is the Leonardo AI Generator content area."),
        cls="menu-content"
    )

@rt("/menuB")
def get():
    return Div(
        H2("Stability AI Generator"),
        P("This is the Stability AI Generator content area."),
        cls="menu-content"
    )

@rt("/menuC")
def get():
    return Div(
        H2("Stability AI Video Generator"),
        P("This is the Stability AI Video Generator content area."),
        cls="menu-content"
    )

@rt("/menuD")
def get():
    return Div(
        H2("HTML5 Interactive Editor"),
        P("This is the HTML 5 Generator content area."),
        cls="menu-content"
    )

@rt("/menuE")
def get():
    return Div(
        H2("Lea Chatbot"),
        P("This is the Lea Chatbot content area."),
        cls="menu-content"
    )

@rt("/tokens")
def get():
    return Div(
        H2("Token Usage Monitoring"),
        P("This is the Token Usage Monitoring content area."),
        cls="menu-content"
    )

# Register cleanup function to close database connections when application exits
atexit.register(token_count.close_all_connections)

serve()
