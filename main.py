from fasthtml.common import *
from starlette.responses import RedirectResponse
from routes import setup_routes

# Create the app with authentication
login_redir = RedirectResponse('/login', status_code=303)

def user_auth_before(req, sess):
    # Get auth from session
    auth = req.scope['auth'] = sess.get('auth', None)
    print(f"Session auth check: {auth}")  # Debugging
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

# Add base route for index page
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
        ("menuC", "Menu C"),
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


# Add styling for error messages
@rt("/")
def head():
    return Style("""
        .error {
            color: #842029;
            background-color: #f8d7da;
            border: 1px solid #f5c2c7;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
        .menu-list { list-style: none; padding: 0; }
        .menu-list li { margin: 10px 0; }
        .menu-list a { 
            display: block;
            padding: 10px;
            background: var(--primary);
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        .menu-list a:hover {
            background: var(--primary-hover);
        }
    """)

serve()