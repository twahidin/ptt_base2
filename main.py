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
        :root {
            --light-green: #90ee90;
            --bright-green: #00ff00;
        }
        
        body, h1, h2, h3, h4, h5, h6, p, div, span, a, li {
            color: var(--light-green) !important;
        }
        
        .header-title h1, .app-container h1, .content-area h2 {
            color: var(--bright-green) !important;
        }
        
        .welcome-text {
            color: var(--light-green) !important;
        }
        
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
        
        .content-area h2 {
            color: var(--bright-green) !important;
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
            color: var(--light-green) !important;
            text-decoration: none;
            border-radius: 6px;
            transition: all 0.2s ease;
        }
        
        .side-menu .menu-item:hover {
            background: var(--primary);
            color: var(--primary-inverse) !important;
        }
        
        .side-menu .menu-item.active {
            background: var(--primary);
            color: var(--primary-inverse) !important;
        }
        
        .side-submenu {
            list-style: none;
            padding: 0 0 0 1.5rem;
            margin: 0.5rem 0 0 0;
            overflow: hidden;
            max-height: 0;
            transition: max-height 0.3s ease-out;
        }
        
        .has-submenu > a {
            position: relative;
        }
        
        .has-submenu > a:after {
            content: "▼";
            font-size: 0.7rem;
            position: absolute;
            right: 1rem;
            top: 50%;
            transform: translateY(-50%);
            transition: transform 0.2s ease;
        }
        
        .has-submenu > a.expanded:after {
            transform: translateY(-50%) rotate(180deg);
        }
        
        .submenu-nav-li {
            margin-bottom: 0.25rem;
        }
        
        .submenu-nav-item {
            display: block;
            padding: 0.5rem 0.75rem;
            color: var(--light-green) !important;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.9rem;
            transition: all 0.2s ease;
        }
        
        .submenu-nav-item:hover {
            background: var(--primary-hover);
            color: var(--primary-inverse) !important;
        }
        
        .submenu-nav-item.active {
            background: var(--primary-focus);
            color: var(--primary-inverse) !important;
        }
        
        .submenu {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
        }
        
        .submenu-item {
            padding: 0.5rem 1rem;
            background: var(--card-background-color);
            border: 1px solid var(--primary);
            border-radius: 4px;
            color: var(--light-green) !important;
            text-decoration: none;
            transition: all 0.2s ease;
        }
        
        .submenu-item:hover {
            background: var(--primary);
            color: var(--primary-inverse) !important;
        }
        
        .submenu-content {
            margin-top: 1.5rem;
            padding: 1rem;
            background: var(--card-background-color);
            border: 1px solid var(--muted-border-color);
            border-radius: 6px;
            min-height: 200px;
        }
        
        .interactive-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-top: 1.5rem;
        }
        
        .interactive-card {
            padding: 1.5rem;
            background: var(--card-sectionning-background-color);
            border-radius: 8px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            height: 100%;
        }
        
        .interactive-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .interactive-card h4 {
            margin-top: 0;
            color: var(--bright-green) !important;
        }
        
        .error {
            color: #842029;
            background-color: #f8d7da;
            border: 1px solid #f5c2c7;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }
        
        /* Make sure header text is visible */
        #content-area h2 {
            color: var(--bright-green) !important;
        }
        
        /* Preview header */
        h2 {
            color: var(--bright-green) !important;
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
        Link(rel="stylesheet", href="/static/css/html5editor.css"),
        Link(rel="stylesheet", href="/static/css/zip-fixes.css"),
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
                Script("""
                    document.addEventListener('DOMContentLoaded', function() {
                        // Get all menu items with submenu
                        var menuItems = document.querySelectorAll('.has-submenu > a');
                        
                        // Add click event to each menu item
                        menuItems.forEach(function(item) {
                            item.addEventListener('click', function(e) {
                                e.preventDefault();
                                
                                // Toggle the active class on the menu item
                                this.classList.toggle('expanded');
                                
                                // Get the submenu
                                var submenu = this.nextElementSibling;
                                
                                // Toggle submenu visibility
                                if (submenu.style.maxHeight) {
                                    submenu.style.maxHeight = null;
                                } else {
                                    submenu.style.maxHeight = submenu.scrollHeight + "px";
                                }
                            });
                        });
                        
                        // Initialize all submenus to be collapsed
                        document.querySelectorAll('.side-submenu').forEach(function(submenu) {
                            submenu.style.maxHeight = null;
                        });
                    });
                """),
                cls="app-container"
            )
        )
    )
        
def create_side_menu(active_menu=None):
    # Define menu structure with submenus
    menu_structure = [
        {
            "id": "menuD", 
            "name": "HTML5 Interactive Editor",
            "has_submenu": False
        },
        {
            "id": "primary", 
            "name": "Primary School Interactives Gallery (Submission Page)",
            "has_submenu": True,
            "submenu": [
                {"id": "primary/math", "name": "Math"},
                {"id": "primary/science", "name": "Science"},
                {"id": "primary/languages", "name": "Languages"}
            ]
        },
        {
            "id": "secondary", 
            "name": "Secondary School Interactives Gallery (Submission Page)",
            "has_submenu": True,
            "submenu": [
                {"id": "secondary/math", "name": "Math"},
                {"id": "secondary/science", "name": "Science"},
                {"id": "secondary/humanities", "name": "Humanities"},
                {"id": "secondary/craft_tech", "name": "Craft & Technology"},
                {"id": "secondary/languages", "name": "Languages"}
            ]
        },
        {
            "id": "jc_ci", 
            "name": "JC & CI Interactives Gallery (Submission Page)",
            "has_submenu": True,
            "submenu": [
                {"id": "jc_ci/math", "name": "Math"},
                {"id": "jc_ci/science", "name": "Science"},
                {"id": "jc_ci/humanities_arts", "name": "Humanities & Arts"},
                {"id": "jc_ci/languages", "name": "Languages"}
            ]
        },
        {
            "id": "tokens", 
            "name": "Token Usage Monitoring",
            "has_submenu": True,
            "submenu": [
                {"id": "tokens/replace_zip", "name": "Replace Interactive ZIP"}
            ]
        }
    ]
    
    menu_items = []
    for item in menu_structure:
        if item["has_submenu"]:
            # Create main menu item with submenu
            submenu_items = []
            for subitem in item["submenu"]:
                submenu_items.append(
                    Li(
                        A(subitem["name"], 
                          href=f"#{subitem['id']}", 
                          hx_get=f"/{subitem['id']}",
                          hx_target="#content-area",
                          cls=f"submenu-nav-item {'active' if subitem['id'] == active_menu else ''}"),
                        cls="submenu-nav-li"
                    )
                )
            
            menu_items.append(
                Li(
                    A(item["name"], 
                      href=f"#{item['id']}", 
                      hx_get=f"/{item['id']}",
                      hx_target="#content-area",
                      cls=f"menu-item {'active' if item['id'] == active_menu else ''}",
                      id=f"{item['id']}-toggle"),
                    Ul(*submenu_items, cls="side-submenu", id=f"{item['id']}-submenu"),
                    cls="has-submenu"
                )
            )
        else:
            # Create regular menu item without submenu
            menu_items.append(
        Li(
                    A(item["name"], 
                      href=f"#{item['id']}", 
                      hx_get=f"/{item['id']}",
              hx_target="#content-area",
                      cls=f"menu-item {'active' if item['id'] == active_menu else ''}"),
                )
            )
    
    return Ul(*menu_items, cls="side-menu")

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
        H2("HTML5 Interactive Editor", 
           cls="editor-title bright-green", 
           style="color: #ffffff !important; text-shadow: 0 0 5px #ffffff !important;"),
        P("This is the HTML 5 Generator content area.", 
          style="color: #ffffff !important;"),
        Div(
            H2("Preview", 
               cls="preview-title bright-green", 
               style="color: #ffffff !important; text-shadow: 0 0 5px #ffffff !important;"),
            P("Your HTML5 content will appear here", 
              cls="preview-text", 
              style="color: #ffffff !important;"),
            cls="preview-section"
        ),
        Script("""
            document.addEventListener('DOMContentLoaded', function() {
                // Set colors for HTML5 Interactive Editor headings
                const headings = document.querySelectorAll('h2');
                headings.forEach(heading => {
                    if (heading.textContent.includes('HTML5') || 
                        heading.textContent.includes('Interactive') || 
                        heading.textContent.includes('Editor') || 
                        heading.textContent.includes('Preview')) {
                        heading.style.color = '#ffffff';
                        heading.style.textShadow = '0 0 5px #ffffff';
                    }
                });
                
                // Set colors for paragraphs 
                const paragraphs = document.querySelectorAll('p');
                paragraphs.forEach(p => {
                    p.style.color = '#ffffff';
                });
            });
        """),
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
def get(req):
    auth = req.session.get('auth')
    # Redirect to replace_zip page by default
    return Div(
        H2("Token Usage Monitoring"),
        P("Please select an option from the submenu."),
        cls="menu-content"
    )

@rt("/tokens/replace_zip")
def get(req):
    auth = req.session.get('auth')
    
    # Only allow access to joe and super_admin
    if auth not in ["joe", "super_admin"]:
        return Div(
            H2("Access Denied"),
            P("You do not have permission to access this page."),
            cls="menu-content error"
        )
    
    return Div(
        H2("Replace Interactive ZIP File"),
        P("Select an interactive from the table below and upload a new ZIP file to replace the existing one."),
        Div(
            id="interactives-table-container",
            cls="table-container",
            hx_get="/api/gallery/list-interactives",
            hx_trigger="load"
        ),
        Script("""
            function showReplaceForm(id, title) {
                document.getElementById('replace-form-container').style.display = 'block';
                document.getElementById('selected-interactive-id').value = id;
                document.getElementById('selected-interactive-title').textContent = title;
            }
            
            function validateZipFile(fileInput) {
                const zipValidationMessage = document.getElementById('zip-validation-message');
                
                if (fileInput.files.length === 0) {
                    zipValidationMessage.textContent = '';
                    return false;
                }
                
                const file = fileInput.files[0];
                
                // Check file type
                if (!file.name.toLowerCase().endsWith('.zip')) {
                    zipValidationMessage.textContent = 'Please upload a ZIP file.';
                    return false;
                }
                
                // Check file size (max 50MB)
                const maxSize = 50 * 1024 * 1024; // 50MB in bytes
                if (file.size > maxSize) {
                    zipValidationMessage.textContent = 'ZIP file must be less than 50MB.';
                    return false;
                }
                
                zipValidationMessage.textContent = '';
                return true;
            }
            
            async function replaceZipFile() {
                const id = document.getElementById('selected-interactive-id').value;
                const zipFile = document.getElementById('replacement-zip').files[0];
                const resultMessage = document.getElementById('result-message');
                const submitButton = document.getElementById('replace-submit-btn');
                
                if (!id || !zipFile) {
                    resultMessage.innerHTML = '<p class="error">Please select an interactive and upload a ZIP file.</p>';
                    return;
                }
                
                if (!validateZipFile(document.getElementById('replacement-zip'))) {
                    return;
                }
                
                // Show loading state
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner"></span> Uploading...';
                resultMessage.innerHTML = '';
                
                try {
                    // Upload ZIP file to blob storage
                    const zipResponse = await fetch('/api/blob/upload?filename=' + encodeURIComponent(zipFile.name), {
                        method: 'POST',
                        body: zipFile
                    });
                    
                    if (!zipResponse.ok) {
                        throw new Error('Failed to upload ZIP file');
                    }
                    
                    const zipData = await zipResponse.json();
                    
                    // Update the interactive with the new ZIP URL
                    const updateResponse = await fetch('/api/gallery/update-zip', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            id: id,
                            zipUrl: zipData.url
                        })
                    });
                    
                    if (!updateResponse.ok) {
                        throw new Error('Failed to update interactive');
                    }
                    
                    const updateData = await updateResponse.json();
                    
                    // Show success message
                    resultMessage.innerHTML = '<p class="success-message">ZIP file replaced successfully!</p>';
                    
                    // Refresh the interactives table
                    document.getElementById('interactives-table-container').setAttribute('hx-trigger', 'load');
                    
                } catch (error) {
                    console.error('Error replacing ZIP:', error);
                    resultMessage.innerHTML = `<p class="error">Error replacing ZIP: ${error.message}</p>`;
                } finally {
                    // Reset button state
                    submitButton.disabled = false;
                    submitButton.innerHTML = 'Replace ZIP File';
                }
            }
        """),
        
        # Form for replacing ZIP file (initially hidden)
        Div(
            H3("Replace ZIP File"),
            Form(
                Input(type="hidden", id="selected-interactive-id", name="interactive-id"),
                Div(
                    Label("Selected Interactive: ", fr="selected-interactive-title"),
                    Span(id="selected-interactive-title", style="font-weight: bold;"),
                    cls="form-group"
                ),
                Div(
                    Label("Upload new ZIP file", fr="replacement-zip"),
                    Div(
                        Input(
                            type="file",
                            id="replacement-zip",
                            name="replacement-zip",
                            accept=".zip",
                            required=True,
                            cls="form-control",
                            onchange="validateZipFile(this)"
                        ),
                        Div(id="zip-validation-message", cls="text-sm text-red-500 mt-1"),
                        cls="mb-2"
                    ),
                    cls="form-group"
                ),
                Div(
                    Button(
                        "Replace ZIP File",
                        type="button",
                        id="replace-submit-btn",
                        cls="btn btn-primary",
                        onclick="replaceZipFile()"
                    ),
                    cls="form-group"
                ),
                Div(id="result-message"),
                id="replace-zip-form",
                cls="mt-4"
            ),
            id="replace-form-container",
            style="display: none; margin-top: 2rem; padding: 1rem; border: 1px solid #2d3748; border-radius: 8px;"
        ),
        
        Style("""
            .table-container {
                margin-top: 1rem;
                overflow-x: auto;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 1rem;
            }
            
            th, td {
                padding: 0.75rem;
                text-align: left;
                border-bottom: 1px solid #2d3748;
            }
            
            th {
                background-color: #1a202c;
                color: #48bb78 !important;
            }
            
            tr:hover {
                background-color: #2d3748;
            }
            
            .btn-replace {
                padding: 0.375rem 0.75rem;
                background-color: #4299e1;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.875rem;
            }
            
            .btn-replace:hover {
                background-color: #3182ce;
            }
            
            .spinner {
                border: 3px solid rgba(0, 0, 0, 0.1);
                width: 20px;
                height: 20px;
                border-radius: 50%;
                border-left-color: white;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-right: 0.5rem;
                vertical-align: middle;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .error {
                color: #fc8181;
                margin-top: 0.5rem;
            }
            
            .success-message {
                color: #48bb78;
                margin-top: 0.5rem;
            }
        """),
        cls="menu-content"
    )

# Register cleanup function to close database connections when application exits
atexit.register(token_count.close_all_connections)

serve()
