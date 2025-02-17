from fasthtml.common import *

def create_api_key_form(api_key='', action='/save-api-key', title="API Configuration"):
    """Create a reusable API key input form"""
    return Card(
        Form(
            Input(id='api_key', name='api_key', 
                  value=api_key, 
                  placeholder='Enter your API Key'),
            Button("Save API Key", type='submit'),
            action=action, method='post'
        ),
        header=H2(title)
    )

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

def create_leonardo_form(api_key=''):
    """Create the Leonardo AI generator form"""
    return Div(
        # API Key Form
        create_api_key_form(
            api_key=api_key, 
            action='/save-leonardo-key',
            title="Leonardo AI Configuration"
        ),
        
        # Generator Form
        Card(
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
                    create_image_upload_area("leonardo-file-input", "leonardo-image-preview"),
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
                      hx_post="/api/leonardo/generate",
                      hx_target="#leonardo-results"),
                cls="generation-form"
            ),
            header=H2("Image Generation")
        ),
        
        # Progress and Results
        Div(
            Div(cls="progress-bar", style="display: none"),
            Div(id="leonardo-results", cls="image-results")
        )
    )

def create_stability_form(api_key=''):
    """Create the Stability AI generator form"""
    return Div(
        # API Key Form
        create_api_key_form(
            api_key=api_key, 
            action='/save-stability-key',
            title="Stability AI Configuration"
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
                
                # Image upload area
                create_image_upload_area(
                    "stability-file-input", 
                    "stability-image-preview",
                    "image-upload-area"
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
                    hx_target="#stability-results",
                    hx_indicator="#loading-indicator"),
                
                Div(
                    Div("Generating image...", 
                        id="loading-indicator",
                        cls="htmx-indicator"),
                    id="stability-results", 
                    cls="image-results"
                ),
                
                cls="generation-form"
            ),
            header=H2("Stability AI Image Generation")
        ),
        
        # Results area
        Div(id="stability-results", cls="image-results")
    )

# def create_login_form(error_message=None):
#     """Create the login form with optional error message"""
#     print("Creating login form")  # Debug print
    
#     form = Form(
#         Div(
#             Label("Username:"),
#             Input(id='username', name='username', placeholder='Username', required=True),
#             cls="form-group"
#         ),
#         Div(
#             Label("Password:"),
#             Input(id='password', name='password', type='password', placeholder='Password', required=True),
#             cls="form-group"
#         ),
#         Button('Login', type='submit'),
#         method='post',  # Ensure method is set
#         action='/login',  # Ensure action is absolute path
#         enctype="application/x-www-form-urlencoded",  # Explicitly set form encoding
#         cls="login-form"
#     )
    
#     if error_message:
#         print(f"Form has error message: {error_message}")  # Debug print
#         return Container(
#             Div(error_message, cls="error"),
#             form
#         )
#     return Container(form)

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