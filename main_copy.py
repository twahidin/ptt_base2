from fasthtml.common import *
from starlette.responses import RedirectResponse
from routes import setup_routes

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
    secret_key="your-secret-key-here"  # Add a secret key for sessions
)

# Set up all routes from the routes module
setup_routes(app)

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
        return Titled("MOE Prompt Testing Tool", 
            Container(
                H1("Click the button below to login using your PTT credentials"),
                A("Login", href="/login", cls="button")
            )
        )
    
    return Titled(f"MOE PPT Version 2",
        Container(
            Div(
                Grid(
                    H1(f"Welcome {auth}"),
                    Div(A("Logout", href="/logout"), 
                        style="text-align: right"),
                    cls="header-grid"
                ),
                Div(
                    Div(create_side_menu(), cls="side-menu-container"),
                    Div(id="content-area", cls="content-area"),
                    cls="main-layout"
                ),
                cls="app-container"
            )
        )
    )

def create_side_menu(active_menu="menuA"):
    menu_items = [
        ("menuA", "Leonardo AI Generator"),
        ("menuB", "Stability AI Generator"),
        ("menuC", "Stability AI Video Generator"),
        ("menuD", "Menu D"),
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
        H2("Menu D Content"),
        P("This is the content for Menu D."),
        cls="menu-content"
    )

serve()