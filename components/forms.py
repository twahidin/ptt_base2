from fasthtml.common import *
from .progress import create_progress_indicator  # Add this import
import os
import base64
from pathlib import Path
import tempfile
import zipfile
import io


def create_login_form(error_message=None):
    """Create the login form with optional error message"""
    form = Form(
        Div(
            Label("Username:"),
            Input(id='username', name='username', placeholder='Username'),
            cls="form-group"
        ),
        Div(
            Label("Password:"),
            Input(id='password', name='password', type='password', placeholder='Password'),
            cls="form-group"
        ),
        Button('Login', type='submit'),
        action='/login', method='post',
        cls="login-form"
    )
    
    if error_message:
        return Container(
            Div(error_message, cls="error"),
            form
        )
    return Container(form)


def create_image_upload_area(file_input_id, preview_id, container_class="image-input", style="display: none;"):
    """Create a reusable image upload area"""
    return Div(
        Label("Upload Image:"),
        Div(
            Input(type="file", 
                  name="image_file", 
                  accept="image/*",
                  id=file_input_id,
                  cls="file-input"),
            Div(id=preview_id, cls="image-preview"),
            cls="upload-container"
        ),
        cls=container_class,
        style=style
     )

      
def create_stability_form(api_key=None):
    """Create the Stability AI generator form with enhanced input handling and animations"""
    return Div(
        Card(   
            Form(
                # Add the animation styles
                Style("""
                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.5; }
                        100% { opacity: 1; }
                    }
                    .loading-message {
                        animation: pulse 2s infinite;
                    }
                    .loading-spinner {
                        border: 4px solid #f3f3f3;
                        border-radius: 50%;
                        border-top: 4px solid #3498db;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                """),
                
                Label("API Key (To key in if there are none):"),
                Input(id='api_key', name='api_key',
                    value=api_key,
                    type='password', 
                    placeholder='Enter your API Key (if needed)'),
                
                # Generation Type selector with HTMX
                Div(
                    Label("Generation Type:"),
                    Select(
                        Option("Text to Image", value="none"),
                        Option("Sketch to Image", value="sketch"),
                        Option("Structure to Image", value="structure"),
                        id="control-type",
                        name="control_type",
                        hx_trigger="change",
                        hx_post="/stability-type-change",
                        hx_target="#input-area",
                        hx_swap="innerHTML"
                    ),
                    cls="mb-4"
                ),
                
                # Dynamic input area for text/image inputs
                Div(
                    # Default view - text inputs
                    Div(
                        Label("Prompt:"),
                        Textarea("", 
                            id='prompt', 
                            name='prompt', 
                            placeholder='Describe what you want to generate',
                            rows=3),
                        Label("Negative Prompt:"),
                        Textarea("", 
                            id='negative_prompt', 
                            name='negative_prompt', 
                            placeholder='Describe what you want to avoid',
                            rows=2)
                    ),
                    id="input-area",
                    cls="space-y-4"
                ),
                
                # Generation parameters
                H3("Generation Parameters", cls="mt-6 mb-4"),
                Grid(
                    Div(
                        Label("Style Preset:"),
                        Select(
                            Option("3D Model", value="3d-model"),
                            Option("Analog Film", value="analog-film"), 
                            Option("Anime", value="anime"),
                            Option("Cinematic", value="cinematic"),
                            Option("Comic Book", value="comic-book"),
                            Option("Digital Art", value="digital-art"),
                            Option("Enhance", value="enhance"),
                            Option("Fantasy Art", value="fantasy-art"),
                            Option("Isometric", value="isometric"),
                            Option("Line Art", value="line-art"),
                            Option("Low Poly", value="low-poly"),
                            Option("Modeling Compound", value="modeling-compound"),
                            Option("Neon Punk", value="neon-punk"),
                            Option("Origami", value="origami"),
                            Option("Photographic", value="photographic"),
                            Option("Pixel Art", value="pixel-art"),
                            Option("Tile Texture", value="tile-texture"),
                            name='style_preset'
                        )
                    ),                    
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
                        id="control-strength-div",
                        cls="hidden"
                    ),
                    cls="grid grid-cols-2 gap-4 mb-6"
                ),
                
                Button("Generate Image", 
                    type='submit',
                    hx_post="/api/stability/generate",
                    hx_target="#results-area",
                    hx_indicator="#loading-indicator",
                    cls="w-full py-2 px-4 bg-blue-500 text-white rounded hover:bg-blue-600"),
                
                # Loading and results container
                Div(
                    # Loading state
                    Div(
                        P("Generating image... Please wait.", cls="loading-message"),
                        Div(cls="loading-spinner"),
                        id="loading-indicator",
                        cls="htmx-indicator text-center"  # Added text-center for better alignment
                    ),
                    # Results area
                    Div(id="results-area"),
                    # Clear results button
                    Button("Clear Results",
                        hx_post="/clear-stability-results",
                        hx_target="#results-area",
                        cls="mt-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 w-full"),
                    cls="mt-4"
                ),
                cls="space-y-4",
                enctype="multipart/form-data"
            ),
            cls="p-6"
        ),
    )


def create_stability_video_form(api_key=''):
    """Create the Stability AI video generator form with enhanced loading states"""
    return Div(
        Card(
            Form(
                Label("API Key (To key in if there are none):"),
                Input(id='api_key', name='api_key',
                    value=api_key,
                    type='password', 
                    placeholder='Enter your API Key (if needed)'),
                
                # Image upload area
                Div(
                    Label("Source Image:"),
                    Div("Supported dimensions: 1024x576, 576x1024, 768x768",
                        cls="text-muted small mb-2"),
                    Input(type="file", 
                          name="file", 
                          accept=".jpg,.jpeg,.png",
                          id="video-source-input",
                          required=True,
                          hx_on="change: console.log('File selected:', this.files[0]?.name)",
                          cls="file-input"),
                    Div(id="video-image-preview", cls="image-preview"),
                    cls="mb-4"
                ),
                
                H3("Generation Parameters", cls="mb-4"),
                
                # Motion Amount
                Div(
                    Label("Motion Amount:"),
                    Input(id='motion_bucket_id', 
                          name='motion_bucket_id',
                          type='range',
                          value='127',
                          min='1',
                          max='255',
                          cls="w-100"),
                    Div("Lower values = less motion, Higher values = more motion",
                        cls="text-muted small"),
                    cls="mb-4"
                ),
                
                # Image Adherence
                Div(
                    Label("Image Adherence:"),
                    Input(id='cfg_scale',
                          name='cfg_scale',
                          type='range',
                          value='1.8',
                          min='0',
                          max='10',
                          step='0.1',
                          cls="w-100"),
                    Div("How closely the video follows the source image",
                        cls="text-muted small"),
                    cls="mb-4"
                ),
                
                # Seed
                Div(
                    Label("Seed:"),
                    Input(id='seed',
                          name='seed',
                          type='number',
                          value='0',
                          min='0',
                          max='4294967294',
                          cls="form-control"),
                    Div("0 for random seed",
                        cls="text-muted small"),
                    cls="mb-4"
                ),
                
                Button("Generate Video", 
                       type='submit',
                       cls="btn btn-primary w-100",
                       hx_post="/api/stability/generate-video",
                       hx_target="#video-results-area",
                       hx_indicator="#video-loading-indicator",
                       hx_encoding="multipart/form-data"),

                # Enhanced loading and results container
                Div(
                    # Video Loading State
                    Div(
                        Style("""
                            @keyframes pulse {
                                0% { opacity: 1; }
                                50% { opacity: 0.5; }
                                100% { opacity: 1; }
                            }
                            .loading-video {
                                animation: pulse 2s infinite;
                            }
                            .loading-spinner {
                                border: 4px solid #f3f3f3;
                                border-radius: 50%;
                                border-top: 4px solid #3498db;
                                width: 40px;
                                height: 40px;
                                animation: spin 1s linear infinite;
                            }
                            @keyframes spin {
                                0% { transform: rotate(0deg); }
                                100% { transform: rotate(360deg); }
                            }
                        """),
                        Div(
                            P("Generating video... This may take several minutes.", 
                              cls="loading-video"),
                            P("Please do not refresh or close this page.", 
                              cls="loading-video"),
                            Div(cls="loading-spinner"),
                            cls="text-center p-4"
                        ),
                        id="video-loading-indicator",
                        cls="htmx-indicator"
                    ),
                    
                    # Results area
                    Div(id="video-results-area"),
                    
                    # Clear results button
                    Button("Clear Results",
                        hx_post="/clear-stability-results",
                        hx_target="#video-results-area",
                        cls="mt-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 w-full"),
                    cls="mt-4"
                ),
                cls="space-y-4",
                enctype="multipart/form-data"
            ),
            cls="p-6"
        )
    )
    
def create_leonardo_form(api_key=None):
    """Create the Leonardo AI generator form with HTMX handling and loading animations"""
    return Div(
        Card(
            Form(
                # Add the animation styles
                Style("""
                    @keyframes pulse {
                        0% { opacity: 1; }
                        50% { opacity: 0.5; }
                        100% { opacity: 1; }
                    }
                    .loading-message {
                        animation: pulse 2s infinite;
                    }
                    .loading-spinner {
                        border: 4px solid #f3f3f3;
                        border-radius: 50%;
                        border-top: 4px solid #3498db;
                        width: 40px;
                        height: 40px;
                        animation: spin 1s linear infinite;
                        margin: 20px auto;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                """),
                
                Label("API Key (To key in if there are none):"),
                Input(id='api_key', name='api_key',
                    value=api_key,
                    type='password', 
                    placeholder='Enter your API Key (if needed)'),
                
                Div(
                    Label("Input Type:"),
                    Select(
                        Option("Text Prompt", value="text"),
                        Option("Image Upload", value="image"),
                        id="input-type",
                        name="input_type",
                        hx_trigger="change",
                        hx_post="/input-type-change",
                        hx_target="#prompt-area",
                        hx_swap="innerHTML"
                    ),
                    cls="input-toggle mb-4"
                ),
                
                # Dynamic prompt area that will be swapped by HTMX
                Div(
                    # Default view - text prompt
                    Div(
                        Label("Text Prompt:"),
                        Textarea("", 
                                id='prompt', 
                                name='prompt', 
                                placeholder='Enter your prompt',
                                rows=3),
                        id="text-input",
                        cls="prompt-input"
                    ),
                    id="prompt-area"
                ),
                
                # Generation parameters
                H3("Generation Parameters", cls="mt-6 mb-4"),
                Grid(
                    Div(
                        Label("Number of Images:"),
                        Input(id='num_images', name='num_images', 
                              type='number', value='4', min='1', max='8')
                    ),
                    Div(
                        Label("Preset Style:"),
                        Select(
                            Option("ANIME", value="ANIME"),
                            Option("BOKEH", value="BOKEH"),
                            Option("CINEMATIC", value="CINEMATIC"),
                            Option("CINEMATIC CLOSEUP", value="CINEMATIC_CLOSEUP"),
                            Option("CREATIVE", value="CREATIVE"),
                            Option("DYNAMIC", value="DYNAMIC"),
                            Option("ENVIRONMENT", value="ENVIRONMENT"),
                            Option("FASHION", value="FASHION"),
                            Option("FILM", value="FILM"),
                            Option("FOOD", value="FOOD"),
                            Option("GENERAL", value="GENERAL"),
                            Option("HDR", value="HDR"),
                            Option("ILLUSTRATION", value="ILLUSTRATION"),
                            Option("LEONARDO", value="LEONARDO"),
                            Option("LONG EXPOSURE", value="LONG_EXPOSURE"),
                            Option("MACRO", value="MACRO"),
                            Option("MINIMALISTIC", value="MINIMALISTIC"),
                            Option("MONOCHROME", value="MONOCHROME"),
                            Option("MOODY", value="MOODY"),
                            Option("NONE", value="NONE"),
                            Option("NEUTRAL", value="NEUTRAL"),
                            Option("PHOTOGRAPHY", value="PHOTOGRAPHY"),
                            Option("PORTRAIT", value="PORTRAIT"),
                            Option("RAYTRACED", value="RAYTRACED"),
                            Option("RENDER 3D", value="RENDER_3D"),
                            Option("RETRO", value="RETRO"),
                            Option("SKETCH B&W", value="SKETCH_BW"),
                            Option("SKETCH COLOR", value="SKETCH_COLOR"),
                            Option("STOCK PHOTO", value="STOCK_PHOTO"),
                            Option("VIBRANT", value="VIBRANT"),
                            Option("UNPROCESSED", value="UNPROCESSED"),
                            name='preset_style',
                            value="DYNAMIC"  # Set default value to DYNAMIC
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
                    cls="grid grid-cols-2 gap-4 mb-6"
                ),
                
                Button("Generate Images", 
                      type='submit',
                      hx_post="/api/leonardo/generate",
                      hx_target="#leonardo-results",
                      hx_indicator="#loading-indicator",  # Add the loading indicator reference
                      cls="w-full py-2 px-4 bg-blue-500 text-white rounded hover:bg-blue-600"),
                cls="space-y-4",
                enctype="multipart/form-data"
            ),
            cls="p-6"
        ),
        
        # Results area with loading state and clear button
        Div(
            # Loading state
            Div(
                P("Generating images... Please wait.", cls="loading-message"),
                Div(cls="loading-spinner"),
                id="loading-indicator",
                cls="htmx-indicator text-center"  # htmx-indicator class for HTMX loading state handling
            ),
            # Results area
            Div(id="leonardo-results", cls="mt-6 grid grid-cols-2 gap-4"),
            # Clear button
            Button("Clear Results",
                   hx_post="/clear-results",
                   hx_target="#leonardo-results",
                   cls="mt-4 px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"),
            cls="mt-4"
        )
    )
    
    
def create_zip_file(html, css, js, sprites):
    """Create a zip file with HTML, CSS, JS and sprites"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('index.html', html)
        zf.writestr('styles.css', css)
        zf.writestr('script.js', js)
        for name, content in sprites.items():
            if content:
                zf.writestr(f'sprites/{name}', content)
    return zip_buffer.getvalue()

def handle_file_upload(file_data):
    """Handle file upload and return file content"""
    if file_data and hasattr(file_data, 'file'):
        return file_data.read()
    return None

def create_chat_component():
    """Create the chat interface component"""
    return Div(
        Textarea(
            placeholder="Enter your HTML5 creation prompt here...",
            id="chat-input",
            rows="4",
            cls="w-full p-2 border rounded"
        ),
        Button(
            "Generate",
            type="button",
            id="generate-btn",
            cls="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
        ),
        Div(id="chat-history", cls="mt-4 h-48 overflow-y-auto border rounded p-2"),
        cls="mb-4"
    )

def create_code_editors():
    """Create code editor components"""
    return Div(
        details := Details(
            Summary("Code Editors", cls="cursor-pointer p-2 bg-gray-100"),
            Grid(
                Div(
                    H3("HTML"),
                    Textarea(id="html-editor", rows="10", cls="w-full p-2 font-mono border rounded"),
                    cls="p-2"
                ),
                Div(
                    H3("CSS"),
                    Textarea(id="css-editor", rows="10", cls="w-full p-2 font-mono border rounded"),
                    cls="p-2"
                ),
                Div(
                    H3("JavaScript"),
                    Textarea(id="js-editor", rows="10", cls="w-full p-2 font-mono border rounded"),
                    cls="p-2"
                ),
                cls="grid-cols-1 gap-4"
            )
        ),
        cls="mt-4"
    )

def create_sprite_upload():
    """Create sprite upload component"""
    return Form(
        H3("Sprite Upload", cls="mb-4"),
        Grid(
            Div(
                Label("Background (PNG/JPEG)"),
                Input(
                    type="file",
                    name="background",
                    accept=".png,.jpg,.jpeg",
                    id="background-upload",
                    cls="block w-full"
                ),
                Div(id="background-preview", cls="mt-2 h-24 bg-gray-100 flex items-center justify-center")
            ),
            Div(
                Label("Main Object (PNG/JPEG)"),
                Input(
                    type="file",
                    name="main_object",
                    accept=".png,.jpg,.jpeg",
                    id="main-object-upload",
                    cls="block w-full"
                ),
                Div(id="main-object-preview", cls="mt-2 h-24 bg-gray-100 flex items-center justify-center")
            ),
            *[Div(
                Label(f"Support {i} (PNG/JPEG)"),
                Input(
                    type="file",
                    name=f"support_{i}",
                    accept=".png,.jpg,.jpeg",
                    id=f"support-{i}-upload",
                    cls="block w-full"
                ),
                Div(id=f"support-{i}-preview", cls="mt-2 h-24 bg-gray-100 flex items-center justify-center")
            ) for i in range(3, 6)],
            cls="grid-cols-2 gap-4"
        ),
        cls="mt-4"
    )

def create_html5_form(api_key=0):
    return Grid(
        # Left Column
        Div(
            H2("Generator Chat", cls="mb-4"),
            create_chat_component(),
            create_code_editors(),
            cls="p-4 border-r"
        ),
        # Right Column
        Div(
            # Preview Section
            Div(
                H2("Preview", cls="mb-4"),
                Iframe(
                    id="preview-frame",
                    cls="w-full h-64 border rounded",
                    sandbox="allow-scripts"
                ),
                cls="mb-8"
            ),
            # Sprite Upload Section
            create_sprite_upload(),
            # File Upload/Download Section
            Div(
                H3("Project Files", cls="mb-4"),
                Form(
                    Input(
                        type="file",
                        name="project_zip",
                        accept=".zip",
                        id="project-upload",
                        cls="block w-full mb-4"
                    ),
                    Button(
                        "Upload Project",
                        type="submit",
                        cls="px-4 py-2 bg-blue-500 text-white rounded"
                    ),
                    action="/upload",
                    method="post",
                    enctype="multipart/form-data"
                ),
                Button(
                    "Download Project",
                    id="download-btn",
                    cls="mt-4 px-4 py-2 bg-green-500 text-white rounded",
                    hx_get="/download",
                    hx_trigger="click"
                ),
                cls="mt-8"
            ),
            cls="p-4"
        ),
        cls="grid grid-cols-2 gap-4"  # Modified this line to enable two-column layout
    )