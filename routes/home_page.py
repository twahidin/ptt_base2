from fasthtml.common import *

def create_side_menu(active_menu=None):
    """Create the side menu with active state handling"""
    menu_items = [
        ("menuA", "Leonardo AI Generator", "/menuA"),
        ("menuB", "Stability AI Generator", "/menuB"), 
        ("menuC", "Stability AI Video Generator", "/menuC")
    ]
    
    return Div(
        Ul(*[
            Li(
                A(name,
                  href=url,
                  hx_get=url,
                  hx_target="#content-area",
                  cls=f"menu-item {' active' if id_ == active_menu else ''}"),
            ) for id_, name, url in menu_items
        ], cls="side-menu"),
        cls="side-menu-container"
    )

def create_header(auth):
    """Create the page header with auth info"""
    return Div(
        Div(
            H1("MOE PPT Version 2", cls="title"),
            Div(f"Welcome {auth}", cls="welcome-text") if auth else None,
            cls="header-left"
        ),
        Div(
            A("Logout", href="/logout", cls="logout-btn") if auth else None,
            cls="header-right"
        ),
        cls="header"
    )

def create_content_area(content=None):
    """Create the main content area"""
    default_content = Div(
        H2("Welcome to MOE PPT Version 2"),
        P("Select a generator from the menu on the left to begin."),
        cls="welcome-message"
    )
    
    return Div(
        content or default_content,
        id="content-area",
        cls="content-area"
    )

def create_layout(auth, content=None):
    """Create the main application layout"""
    return Div(
        create_header(auth),
        Div(
            create_side_menu(),
            create_content_area(content),
            cls="main-layout"
        ),
        cls="main-container"
    )

def routes(rt):
    @rt("/")
    def get(req):
        auth = req.session.get('auth')
        
        if not auth:
            # Show login page if not authenticated
            return Titled("MOE PPT Login",
                Container(
                    Div(
                        H1("MOE Prompt Testing Tool"),
                        P("Please log in with your PTT credentials to continue."),
                        A("Login", href="/login", cls="button login-button"),
                        cls="login-container"
                    )
                )
            )
        
        # Show main application layout if authenticated
        return Titled("MOE PPT Version 2",
            Container(create_layout(auth))
        )
