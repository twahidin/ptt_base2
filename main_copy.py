from fasthtml.common import *
from starlette.responses import RedirectResponse
import requests
import json
import time
from dataclasses import dataclass
import base64
from ptt_bascode.authentication import check_password

# Create the app with authentication
login_redir = RedirectResponse('/login', status_code=303)

def user_auth_before(req, sess):
    auth = req.scope['auth'] = sess.get('auth', None)
    if not auth and req.url.path != '/': 
        return login_redir

beforeware = Beforeware(
    user_auth_before,
    skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', r'.*\.js', '/login']
)

app, rt = fast_app(before=beforeware)

# Mock check_password function for demonstration


def create_login_form(error_message=None):
    """Create the login form with optional error message"""
    form = Form(
        Input(id='username', name='username', placeholder='Username'),
        Input(id='password', name='password', type='password', placeholder='Password'),
        Button('Login', type='submit'),
        action='/login', method='post'
    )
    
    # If there's an error message, wrap both the error and form in a container
    if error_message:
        return Container(
            Div(error_message, cls="error"),
            form
        )
    return Container(form)

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

# Login page handler
@rt("/login")
def get(req):
    # Check if there's an error message in the session
    error_message = req.session.get('login_error')
    if error_message:
        # Clear the error message from session
        del req.session['login_error']
        return Titled("Login", create_login_form(error_message))
    return Titled("Login", create_login_form())

# Login form handler
@dataclass
class Login:
    username: str
    password: str

@rt("/login")
def post(login: Login, sess):
    if not login.username or not login.password:
        sess['login_error'] = "Please enter both username and password."
        return RedirectResponse('/login', status_code=303)
    
    user = check_password(login.username.lower(), login.password)
    if user:
        sess['auth'] = login.username
        return RedirectResponse('/', status_code=303)
    else:
        sess['login_error'] = "Authentication failed. Please check your credentials."
        return RedirectResponse('/login', status_code=303)

# Logout handler
@rt("/logout")
def get(sess):
    if 'auth' in sess:
        del sess['auth']
    return RedirectResponse('/', status_code=303)

# # Main page with menu
# @rt("/")
# def get(req):
#     auth = req.session.get('auth')
    
#     if not auth:
#         return Titled("Public Homepage", 
#             Container(
#                 H1("Welcome to Our App"),
#                 A("Login", href="/login", cls="button")
#             )
#         )
    
#     menu_items = [
#         A("Menu A", href="#menuA"),
#         A("Menu B", href="#menuB"),
#         A("Menu C", href="#menuC"),
#         A("Menu D", href="#menuD"),
#     ]
    
#     return Titled(f"Prompt Testing Tool 2",
#         Container(
#             Grid(
#                 #H1(f"Welcome to AIEd PTT2"),
#                 Div(A("Logout", href="/logout"), style="text-align: right")
#             ),
#             Card(
#                 Ul(*[Li(item) for item in menu_items], cls="menu-list"),
#                 header=H2("Main Menu")
#             )
#         )
#     )

# Leonardo AI API handlers
@dataclass
class LeonardoAIConfig:
    api_key: str
    prompt: str
    num_images: int = 4
    preset_style: str = "DYNAMIC"
    height: int = 768
    width: int = 1024
    model_id: str = "b24e16ff-06e3-43eb-8d33-4416c2d75876"

async def handle_image_upload(form_data):
    # Handle image upload logic here
    image_file = form_data.get('image_file')
    if image_file and image_file.file:
        # Process the uploaded image
        content = await image_file.read()
        # Convert to base64 or handle as needed
        return base64.b64encode(content).decode('utf-8')
    return None

@rt("/api/generate")
async def post(req):
    form = await req.form()
    api_key = req.session.get('leonardo_ai_key')
    
    if not api_key:
        return JSONResponse({"error": "API key not set"})

    # Get form parameters
    prompt = form.get('prompt')
    num_images = int(form.get('num_images', 4))
    preset_style = form.get('preset_style', 'DYNAMIC')
    height = int(form.get('height', 768))
    width = int(form.get('width', 1024))
    model_id = form.get('model_id', 'b24e16ff-06e3-43eb-8d33-4416c2d75876')
    
    # Handle image upload if present
    image_data = None
    if form.get('use_image') == 'true':
        image_data = await handle_image_upload(form)

    url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    payload = {
        "alchemy": True,
        "height": height,
        "width": width,
        "modelId": model_id,
        "num_images": num_images,
        "presetStyle": preset_style,
        "prompt": prompt,
    }

    if image_data:
        payload["imagePrompts"] = [image_data]

    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}"
    }
    
    try:
        # Start generation
        response = requests.post(url, json=payload, headers=headers)
        generation_id = response.json()['sdGenerationJob']['generationId']
        
        # Return generation ID for polling
        return JSONResponse({"generation_id": generation_id})
    except Exception as e:
        return JSONResponse({"error": str(e)})

@rt("/api/check-status/{generation_id}")
async def get(generation_id: str, req):
    api_key = req.session.get('leonardo_ai_key')
    if not api_key:
        return JSONResponse({"error": "API key not set"})

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {api_key}"
    }
    
    url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
    response = requests.get(url, headers=headers)
    return JSONResponse(response.json())

@rt("/save-api-key")
async def post(req, sess):
    form = await req.form()
    api_key = form.get('api_key')
    if api_key:
        sess['leonardo_ai_key'] = api_key
    return RedirectResponse('/menuA', status_code=303)

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

def create_generator_form(api_key=''):
    return Card(
        Form(
            # Toggle between text and image input
            Div(
                Label("Input Type:"),
                Select(
                    Option("Text Prompt", value="text"),
                    Option("Image Upload", value="image"),
                    id="input-type",
                    name="input_type",
                    hx_on="change",
                    hx_swap="innerHTML",
                    hx_target="#prompt-area"
                ),
                cls="input-toggle"
            ),
            
            # Dynamic prompt area
            Div(
                # Text input option
                Div(
                    Label("Text Prompt:"),
                    Textarea("", 
                            id='prompt', 
                            name='prompt', 
                            placeholder='Enter your prompt',
                            rows=3),
                    cls="prompt-input",
                    style="display: flex; flex-direction: column; gap: 0.5rem;"
                ),
                # Image upload option
                Div(
                    Label("Upload Image:"),
                    Div(
                        Input(type="file", 
                              name="image_file", 
                              accept="image/*",
                              id="file-input",
                              cls="file-input"),
                        Div(id="image-preview", cls="image-preview"),
                        cls="upload-container"
                    ),
                    cls="image-input",
                    style="display: none;"
                ),
                id="prompt-area"
            ),
            
            # Generation parameters
            H3("Generation Parameters"),
            Grid(
                Div(
                    Label("Number of Images:"),
                    Input(id='num_images', name='num_images', 
                          type='number', value='4', min='1', max='8')
                ),
                Div(
                    Label("Preset Style:"),
                    Select(
                        Option("DYNAMIC", value="DYNAMIC"),
                        Option("LEONARDO", value="LEONARDO"),
                        Option("HD", value="HD"),
                        name='preset_style'
                    )
                ),
                Div(
                    Label("Width:"),
                    Input(id='width', name='width', 
                          type='number', value='1024', step='64')
                ),
                Div(
                    Label("Height:"),
                    Input(id='height', name='height', 
                          type='number', value='768', step='64')
                ),
                cls="parameters-grid"
            ),
            
            Button("Generate Images", 
                  type='submit',
                  hx_post="/api/generate",
                  hx_target="#results"),
            cls="generation-form"
        ),
        header=H2("Image Generation")
    )

# Main content handlers
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
                # Header
                Grid(
                    H1(f"Welcome {auth}"),
                    Div(A("Logout", href="/logout"), 
                        style="text-align: right"),
                    cls="header-grid"
                ),
                
                # Main content area with side menu and content
                Div(
                    Div(create_side_menu(), cls="side-menu-container"),
                    Div(id="content-area", cls="content-area"),
                    cls="main-layout"
                ),
                cls="app-container"
            )
        )
    )

@rt("/menuA")
def get(req, sess):
    api_key = sess.get('leonardo_ai_key', '')
    
    return Div(
        # API Key Form
        Card(
            Form(
                Input(id='api_key', name='api_key', 
                      value=api_key, placeholder='Enter your Leonardo AI API Key'),
                Button("Save API Key", type='submit'),
                action='/save-api-key', method='post'
            ),
            header=H2("API Configuration")
        ),
        
        # Generator Form
        create_generator_form(api_key),
        
        # Progress and Results
        Div(
            Div(cls="progress-bar", style="display: none"),
            Div(id="results", cls="image-results")
        ),
        
        # Add JavaScript for handling file upload preview and image generation
        Script("""
            // Handle input type switching
            document.getElementById('input-type').addEventListener('change', function(e) {
                const textInput = document.querySelector('.prompt-input');
                const imageInput = document.querySelector('.image-input');
                if (e.target.value === 'image') {
                    textInput.style.display = 'none';
                    imageInput.style.display = 'block';
                } else {
                    textInput.style.display = 'block';
                    imageInput.style.display = 'none';
                }
            });

            // Handle file input changes
            document.getElementById('file-input').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const preview = document.querySelector('#image-preview');
                        preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
                    };
                    reader.readAsDataURL(file);
                }
            });
        """),
        
        # Add JavaScript for handling image generation and polling
        Script("""
            htmx.on('#content-area', 'htmx:afterRequest', function(evt) {
                if (evt.detail.path === '/api/generate') {
                    const response = JSON.parse(evt.detail.xhr.response);
                    if (response.generation_id) {
                        const progressBar = document.querySelector('.progress-bar');
                        progressBar.style.display = 'block';
                        pollGeneration(response.generation_id);
                    }
                }
            });
            
            function pollGeneration(generationId) {
                const progressBar = document.querySelector('.progress-bar');
                const resultsDiv = document.querySelector('#results');
                
                function checkStatus() {
                    fetch(`/api/check-status/${generationId}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'complete') {
                                progressBar.style.display = 'none';
                                // Display images
                                resultsDiv.innerHTML = data.images.map(img => 
                                    `<img src="${img.url}" alt="Generated image">`
                                ).join('');
                            } else {
                                setTimeout(checkStatus, 2000);
                            }
                        });
                }
                
                checkStatus();
            }
        """)
    )

# Add these dataclass definitions
@dataclass
class StabilityAIConfig:
    api_key: str
    prompt: str
    negative_prompt: str = ""
    aspect_ratio: str = "3:2"
    seed: int = 0
    output_format: str = "jpeg"
    control_strength: float = 0.7
    
# Add new API handlers
@rt("/save-stability-key")
async def post(req, sess):
    form = await req.form()
    api_key = form.get('api_key')
    if api_key:
        sess['stability_ai_key'] = api_key
    return RedirectResponse('/menuB', status_code=303)

@rt("/api/stability/generate")
async def post(req):
    form = await req.form()
    api_key = req.session.get('stability_ai_key')
    
    if not api_key:
        return JSONResponse({"error": "API key not set"})

    # Get form parameters
    prompt = form.get('prompt')
    negative_prompt = form.get('negative_prompt', '')
    aspect_ratio = form.get('aspect_ratio', '3:2')
    seed = int(form.get('seed', '0'))
    output_format = form.get('output_format', 'jpeg')
    control_strength = float(form.get('control_strength', '0.7'))
    
    # Handle image upload if present
    image_data = None
    control_type = form.get('control_type', 'none')
    if control_type in ['sketch', 'structure']:
        image_file = form.get('image_file')
        if image_file and image_file.file:
            image_data = await image_file.read()
    
    # Set up API endpoint based on control type
    if control_type == 'none':
        host = "https://api.stability.ai/v2beta/stable-image/generate/ultra"
    else:
        host = f"https://api.stability.ai/v2beta/stable-image/control/{control_type}"
    
    # Prepare request parameters
    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "aspect_ratio": aspect_ratio,
        "seed": seed,
        "output_format": output_format
    }
    
    if control_type != 'none':
        params["control_strength"] = control_strength
    
    headers = {
        "Accept": "image/*",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        files = {}
        if image_data:
            files["image"] = ("image.jpg", image_data, "image/jpeg")
        
        response = requests.post(host, headers=headers, files=files or None, data=params)
        
        if not response.ok:
            return JSONResponse({"error": response.text})
        
        # For successful response, return the image data
        return Response(
            content=response.content,
            media_type="image/jpeg",
            headers={
                "seed": response.headers.get("seed", "0"),
                "finish-reason": response.headers.get("finish-reason", "COMPLETE")
            }
        )
    except Exception as e:
        return JSONResponse({"error": str(e)})

# Update the menuB handler
@rt("/menuB")
def get(req, sess):
    api_key = sess.get('stability_ai_key', '')
    
    return Div(
        # API Key Form
        Card(
            Form(
                Input(id='api_key', name='api_key', 
                      value=api_key, placeholder='Enter your Stability AI API Key'),
                Button("Save API Key", type='submit'),
                action='/save-stability-key', method='post'
            ),
            header=H2("Stability AI Configuration")
        ),
        
        # Generator Form
        Card(
            Form(
                # Control type selector
                Div(
                    Label("Generation Type:"),
                    Select(
                        Option("Text to Image", value="none"),
                        Option("Sketch to Image", value="sketch"),
                        Option("Structure to Image", value="structure"),
                        id="control-type",
                        name="control_type"
                    ),
                    cls="control-type-select"
                ),
                
                # Image upload area (initially hidden)
                Div(
                    Label("Upload Control Image:"),
                    Input(type="file", 
                          name="image_file", 
                          accept="image/*",
                          id="stability-file-input"),
                    Div(id="stability-image-preview", cls="image-preview"),
                    cls="image-upload-area",
                    style="display: none;"
                ),
                
                # Prompt inputs
                Div(
                    Label("Prompt:"),
                    Textarea("", id='prompt', name='prompt', 
                            placeholder='Describe what you want to generate',
                            rows=3),
                    Label("Negative Prompt:"),
                    Textarea("", id='negative_prompt', name='negative_prompt', 
                            placeholder='Describe what you want to avoid',
                            rows=2),
                    cls="prompt-inputs"
                ),
                
                # Generation parameters
                H3("Generation Parameters"),
                Grid(
                    Div(
                        Label("Aspect Ratio:"),
                        Select(
                            Option("21:9", value="21:9"),
                            Option("16:9", value="16:9"),
                            Option("3:2", value="3:2", selected="selected"),
                            Option("5:4", value="5:4"),
                            Option("1:1", value="1:1"),
                            Option("4:5", value="4:5"),
                            Option("2:3", value="2:3"),
                            Option("9:16", value="9:16"),
                            Option("9:21", value="9:21"),
                            name='aspect_ratio'
                        )
                    ),
                    Div(
                        Label("Output Format:"),
                        Select(
                            Option("JPEG", value="jpeg"),
                            Option("PNG", value="png"),
                            Option("WebP", value="webp"),
                            name='output_format'
                        )
                    ),
                    Div(
                        Label("Seed:"),
                        Input(id='seed', name='seed', 
                              type='number', value='0')
                    ),
                    Div(
                        Label("Control Strength:"),
                        Input(id='control_strength', name='control_strength', 
                              type='range', value='0.7', 
                              min='0', max='1', step='0.05'),
                        cls="control-strength",
                        style="display: none;"
                    ),
                    cls="parameters-grid"
                ),
                
                Button("Generate Image", 
                      type='submit',
                      hx_post="/api/stability/generate",
                      hx_target="#stability-results"),
                cls="generation-form"
            ),
            header=H2("Stability AI Image Generation")
        ),
        
        # Results area
        Div(id="stability-results", cls="image-results"),
        
        # JavaScript for handling the UI
        Script("""
            // Handle control type changes
            document.getElementById('control-type').addEventListener('change', function(e) {
                const imageUpload = document.querySelector('.image-upload-area');
                const controlStrength = document.querySelector('.control-strength');
                
                if (e.target.value === 'none') {
                    imageUpload.style.display = 'none';
                    controlStrength.style.display = 'none';
                } else {
                    imageUpload.style.display = 'block';
                    controlStrength.style.display = 'block';
                }
            });
            
            // Handle file input preview
            document.getElementById('stability-file-input').addEventListener('change', function(e) {
                const file = e.target.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const preview = document.querySelector('#stability-image-preview');
                        preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
                    };
                    reader.readAsDataURL(file);
                }
            });
            
            // Handle form submission response
            htmx.on('#stability-results', 'htmx:afterRequest', function(evt) {
                if (evt.detail.successful) {
                    const contentType = evt.detail.xhr.getResponseHeader('Content-Type');
                    if (contentType && contentType.includes('image')) {
                        // Create blob URL from the image data
                        const blob = new Blob([evt.detail.xhr.response], {type: contentType});
                        const imageUrl = URL.createObjectURL(blob);
                        
                        // Display the generated image
                        const resultsDiv = document.querySelector('#stability-results');
                        resultsDiv.innerHTML = `<img src="${imageUrl}" alt="Generated image">`;
                        
                        // Clean up the blob URL after the image loads
                        const img = resultsDiv.querySelector('img');
                        img.onload = () => URL.revokeObjectURL(imageUrl);
                    } else {
                        // Handle error response
                        try {
                            const response = JSON.parse(evt.detail.xhr.response);
                            if (response.error) {
                                document.querySelector('#stability-results').innerHTML = 
                                    `<div class="error">${response.error}</div>`;
                            }
                        } catch (e) {
                            console.error('Error parsing response:', e);
                        }
                    }
                }
            });
        """)
    )



@rt("/menuC")
def get(): return H2("Menu C Content")

@rt("/menuD")
def get(): return H2("Menu D Content")

# Add styling
@rt("/")
def head():
    return Style("""
        .file-input {
            width: 100%;
            padding: 1rem;
            border: 2px dashed var(--primary);
            border-radius: 4px;
            cursor: pointer;
            margin-bottom: 1rem;
        }
        
        .file-input:hover {
            border-color: var(--primary-hover);
        }
        
        .image-preview {
            max-width: 100%;
            min-height: 200px;
            border-radius: 4px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--card-background-color);
            margin-top: 1rem;
        }
        
        .image-preview img {
            max-width: 100%;
            max-height: 300px;
            object-fit: contain;
        }
        
        .upload-container {
            display: flex;
            flex-direction: column;
        }
        .app-container {
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }
        
        .main-layout {
            display: grid;
            grid-template-columns: 250px 1fr;
            gap: 2rem;
            min-height: 80vh;
        }
        
        .side-menu-container {
            background: var(--card-background-color);
            padding: 1rem;
            border-radius: 8px;
            box-shadow: var(--card-box-shadow);
        }
        
        .side-menu {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .side-menu li {
            margin: 0.5rem 0;
        }
        
        .menu-item {
            display: block;
            padding: 0.75rem 1rem;
            color: var(--primary);
            text-decoration: none;
            border-radius: 4px;
            transition: background 0.3s;
        }
        
        .menu-item:hover {
            background: var(--primary);
            color: white;
        }
        
        .menu-item.active {
            background: var(--primary);
            color: white;
        }
        
        .content-area {
            padding: 1rem;
            background: var(--card-background-color);
            border-radius: 8px;
            box-shadow: var(--card-box-shadow);
        }
        
        .generation-form {
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .parameters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .image-results {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
            margin-top: 2rem;
        }
        
        .image-results img {
            width: 100%;
            height: auto;
            border-radius: 4px;
        }
        
        .progress-bar {
            height: 4px;
            background: linear-gradient(90deg, var(--primary) 0%, transparent 50%, var(--primary) 100%);
            background-size: 200% 100%;
            animation: progress 1s linear infinite;
            margin: 1rem 0;
        }
        
        @keyframes progress {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        
        .input-toggle {
            margin-bottom: 1rem;
        }
        
        .prompt-input {
            margin-bottom: 1rem;
        }
        
        .header-grid {
            display: grid;
            grid-template-columns: 1fr auto;
            align-items: center;
            margin-bottom: 2rem;
        }
    """)

serve()