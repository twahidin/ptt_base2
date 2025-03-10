from fasthtml.common import *
import base64
from pathlib import Path
import tempfile
import zipfile
import datetime
import io
from PIL import Image
from components.html5_form import create_html5_form, create_code_editors

from dotenv import load_dotenv
load_dotenv()

#try and load the environment variables
if os.getenv("OPENAI_API_KEY") is None:
    os.environ["OPENAI_API_KEY"] = ""
else:
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

if os.getenv("ANTHROPIC_API_KEY") is None:
    os.environ["ANTHROPIC_API_KEY"] = ""
else:  
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")


def extract_components(code):
    """Extract HTML, CSS, and JavaScript components from the generated code"""
    html = ""
    css = ""
    js = ""
    in_html = False
    in_css = False  
    in_js = False
    
    for line in code.splitlines():
        if line.strip().startswith("<body>"):
            in_html = True
            continue
        elif line.strip().startswith("</body>"):
            in_html = False
            continue
        elif line.strip().startswith("<style>"):
            in_css = True
            continue
        elif line.strip().startswith("</style>"):
            in_css = False
            continue
        elif line.strip().startswith("<script>"):
            in_js = True
            continue
        elif line.strip().startswith("</script>"):
            in_js = False
            continue
        
        if in_html:
            html += line + "\n"
        elif in_css:
            css += line + "\n"
        elif in_js:
            js += line + "\n"
    
    return html, css, js


def create_zip_file(html, css, js):
    """
        Create a ZIP file with index.html containing the HTML5 content
        
        Args:
            html (str): HTML content
            css (str): CSS content
            js (str): JavaScript content
            
        Returns:
            bytes: The ZIP file content as bytes
        """
        # Create a complete HTML document
    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HTML5 Interactive Content</title>
        <style>
    {css}
        </style>
    </head>
    <body>
    {html}
        <script>
    {js}
        </script>
    </body>
    </html>"""

    # Create the ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add index.html to the ZIP
        zip_file.writestr('index.html', html_content)
        
        # Add a README.txt file with information
        readme_content = """HTML5 Interactive Content for SLS

        This ZIP file contains a self-contained HTML5 interactive content that:
        1. Works without requiring an internet connection
        2. Scales proportionally within an iframe or browser window
        3. Uses only included libraries (no external dependencies)

        To use in SLS:
        1. Upload this ZIP file directly in SLS using "File from Device" option
        2. The content will be displayed as an interactive media object
        """
        zip_file.writestr('README.txt', readme_content)
    
    # Get the ZIP data
    zip_buffer.seek(0)
    return zip_buffer.getvalue()



# Image processing helper functions
def process_image_for_claude(base64_data, declared_media_type='image/jpeg'):
    """
    Processes base64 image data to ensure it works with Claude's vision API
    
    Args:
        base64_data (str): The base64-encoded image data (without data URL prefix)
        declared_media_type (str): The media type to declare to the API
        
    Returns:
        tuple: (processed_base64_data, verified_media_type)
    """
    import base64
    import io
    from PIL import Image
    import re
    
    # If empty or None
    if not base64_data:
        return None, None
    
    try:
        # Clean up the base64 data - remove any data URL prefix if present
        if base64_data.startswith('data:'):
            # Extract the media type and data
            match = re.match(r'data:([^;]+);base64,(.+)', base64_data)
            if match:
                extracted_media_type = match.group(1)
                base64_data = match.group(2)
                # Use the extracted media type if it's available
                if extracted_media_type:
                    declared_media_type = extracted_media_type
        
        # Ensure the base64 data is properly padded
        padding_needed = len(base64_data) % 4
        if padding_needed:
            base64_data += '=' * (4 - padding_needed)
            
        # Decode the base64 data to binary
        try:
            binary_data = base64.b64decode(base64_data)
        except Exception as e:
            print(f"Error decoding base64 data: {e}")
            return None, None
            
        # Verify and normalize the image format
        try:
            # Open the image with PIL to verify it's valid
            img = Image.open(io.BytesIO(binary_data))
            
            # For Claude, let's convert everything to PNG for maximum compatibility
            print(f"Converting to PNG for Claude compatibility")
            
            # Convert to PNG
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            binary_data = buffer.getvalue()
            verified_media_type = 'image/png'  # Always use PNG for Claude
            
            # Re-encode to base64
            processed_base64 = base64.b64encode(binary_data).decode('utf-8')
            
            return processed_base64, verified_media_type
            
        except Exception as e:
            print(f"Error processing image with PIL: {e}")
            import traceback
            print(traceback.format_exc())
            return None, None
            
    except Exception as e:
        print(f"Unexpected error in process_image_for_claude: {e}")
        import traceback
        print(traceback.format_exc())
        return None, None

def process_image_for_openai(base64_data):
    """
    Processes base64 image data to ensure it works with OpenAI's vision API
    
    Args:
        base64_data (str): The base64-encoded image data (with or without data URL prefix)
        
    Returns:
        str: A properly formatted data URL for OpenAI
    """
    import base64
    import io
    from PIL import Image
    import re
    
    # If empty or None
    if not base64_data:
        return None
    
    try:
        # Clean up the base64 data - remove any data URL prefix if present
        clean_base64 = base64_data
        if base64_data.startswith('data:'):
            # Extract just the base64 part
            parts = base64_data.split(',', 1)
            if len(parts) == 2:
                clean_base64 = parts[1]
        
        # Ensure the base64 data is properly padded
        padding_needed = len(clean_base64) % 4
        if padding_needed:
            clean_base64 += '=' * (4 - padding_needed)
            
        # Decode the base64 data to binary
        try:
            binary_data = base64.b64decode(clean_base64)
        except Exception as e:
            print(f"Error decoding base64 data: {e}")
            return None
            
        # Process the image with PIL
        try:
            # Open the image to verify it's valid and determine format
            img = Image.open(io.BytesIO(binary_data))
            
            # OpenAI works best with JPEG or PNG
            # Let's standardize on PNG
            print(f"Converting to PNG for OpenAI")
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            binary_data = buffer.getvalue()
            media_type = "image/png"
            
            # Re-encode to base64
            processed_base64 = base64.b64encode(binary_data).decode('utf-8')
            
            # Format as a data URL
            return f"data:{media_type};base64,{processed_base64}"
            
        except Exception as e:
            print(f"Error processing image with PIL: {e}")
            import traceback
            print(traceback.format_exc())
            return None
            
    except Exception as e:
        print(f"Unexpected error in process_image_for_openai: {e}")
        import traceback
        print(traceback.format_exc())
        return None



def routes(rt):
    @rt('/menuD')
    def get(req):
        api_key = os.getenv("OPENAI_API_KEY")
        return Titled("HTML5 Project",
            Link(rel="stylesheet", href="static/css/styles.css"),
            create_html5_form(api_key)
        )

# Complete fix for the preview endpoint with properly escaped JavaScript
# This addresses the issue with leaked code appearing in the preview

    # Modified preview endpoint
    @rt('/api/html5/preview')
    async def post(req):
        """Generate an interactive preview using the code from the editors"""
        try:
            # Get form data
            form = await req.form()
            html = form.get('html-editor', '')
            css = form.get('css-editor', '')
            js = form.get('js-editor', '')
            
            # Prevent empty requests
            if not html and not css and not js:
                return Div("No content to preview", 
                    cls="flex items-center justify-center h-full text-gray-400",
                    style="background-color: #121212;")
                    
            # Debug information to console
            print(f"Preview HTML Length: {len(html)}")
            print(f"Preview CSS Length: {len(css)}")
            print(f"Preview JS Length: {len(js)}")
            
            # Save to session
            req.session['html'] = html
            req.session['css'] = css
            req.session['js'] = js

            # Create a complete HTML document
            preview_content = f"""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                body {{
                    background-color: #121212;
                    color: #ffffff;
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                }}
                /* Default container for content */
                #content-container {{
                    padding: 20px;
                    flex-grow: 1;
                }}
                /* User CSS */
                {css}
                </style>
            </head>
            <body>
                <div id="content-container">
                    {html}
                </div>
                <script>
                // Initialize content and catch errors
                try {{
                    {js}
                }} catch (error) {{
                    console.error('Error in JavaScript execution:', error);
                    const errorDiv = document.createElement('div');
                    errorDiv.style.color = 'red';
                    errorDiv.style.padding = '10px';
                    errorDiv.style.marginTop = '20px';
                    errorDiv.style.border = '1px solid red';
                    errorDiv.style.backgroundColor = '#ffeeee';
                    errorDiv.innerHTML = '<strong>JavaScript Error:</strong><br>' + error.message;
                    document.body.appendChild(errorDiv);
                }}
                </script>
            </body>
            </html>"""
            
            # Encode the content as base64
            import base64
            encoded_content = base64.b64encode(preview_content.encode('utf-8')).decode('utf-8')
            
            # Create an iframe with data URL
            # IMPORTANT: Remove the hx-swap-oob attribute which may be causing issues
            iframe_html = f'''
            <iframe 
                src="data:text/html;base64,{encoded_content}" 
                width="100%" 
                height="100%" 
                frameborder="0" 
                allowfullscreen="true" 
                style="background-color: #121212; display: block;"
                id="preview-frame-{datetime.datetime.now().timestamp()}"
            >
            </iframe>
            '''
            
            return NotStr(iframe_html)
        except Exception as error:
            import traceback
            error_details = traceback.format_exc()
            print(f"Preview error: {str(error)}\n{error_details}")
            return Div(
                f"Error in preview: {str(error)}",
                Pre(error_details, cls="text-xs mt-2"),
                cls="p-4 bg-red-100 text-red-800 rounded"
            )

    # Updated clear preview endpoint in html_5.py
    @rt('/api/html5/clear-preview')
    async def post(req):
        """Clear the preview and code"""
        # Clear session data
        if 'html' in req.session:
            del req.session['html']
        if 'css' in req.session:
            del req.session['css']
        if 'js' in req.session:
            del req.session['js']
        
        # Return a clean placeholder div
        clean_preview_html = """
        <div class="flex items-center justify-center h-full text-gray-400" 
            style="background-color: #121212;">
            Your HTML5 content will appear here
        </div>
        <script>
            // Clear the code editors container
            var editorsContainer = document.getElementById('code-editors-container');
            if (editorsContainer) {
                editorsContainer.innerHTML = '';
            }
            
            // Hide buttons
            var runButton = document.getElementById('run-preview-button');
            var clearButton = document.getElementById('clear-button');
            
            if (runButton) runButton.classList.add('hidden');
            if (clearButton) clearButton.classList.add('hidden');
            
            // Reset iterative mode
            var iterativeToggle = document.getElementById('iterative-toggle');
            if (iterativeToggle) {
                iterativeToggle.checked = false;
                if (typeof updateIterativeBadge === 'function') {
                    updateIterativeBadge();
                }
            }
            
            // Reset prompt to original state if in TinyMCE
            if (typeof tinymce !== 'undefined' && tinymce.get('prompt')) {
                tinymce.get('prompt').setContent('');
            }
        </script>
        """
        
        return NotStr(clean_preview_html)


    @rt('/api/html5/preview-content')
    async def get(req):
        """Endpoint to serve the preview content"""
        html = req.session.get('html', '')
        css = req.session.get('css', '')
        js = req.session.get('js', '')
        
        # Enhanced debug logging
        print(f"Session data - HTML exists: {'Yes' if 'html' in req.session else 'No'}")
        print(f"Session data - CSS exists: {'Yes' if 'css' in req.session else 'No'}")
        print(f"Session data - JS exists: {'Yes' if 'js' in req.session else 'No'}")
        print(f"Serving preview content - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
        
        # Fix for empty preview - check if code exists and force direct HTML
        if len(html) == 0 and len(css) == 0 and len(js) == 0:
            # Let's check if we can extract code from the current form submission
            test_html = '''
            <h1>Thermometer Simulation</h1>
            <div class="container">
                <div class="beaker">
                    <div class="water"></div>
                    <div class="thermometer">
                        <div class="mercury"></div>
                    </div>
                </div>
                <div class="controls">
                    <input type="range" id="heat-slider" min="0" max="100" value="0">
                    <span id="temp-display">25°C</span>
                </div>
            </div>
            '''
            
            test_css = '''
            .container {
                display: flex;
                flex-direction: column;
                align-items: center;
                gap: 20px;
                padding: 20px;
            }
            
            .beaker {
                position: relative;
                width: 150px;
                height: 200px;
                border: 3px solid #ccc;
                border-radius: 0 0 20px 20px;
                overflow: hidden;
            }
            
            .water {
                position: absolute;
                bottom: 0;
                width: 100%;
                height: 80%;
                background-color: #3498db;
                transition: background-color 0.5s;
            }
            
            .thermometer {
                position: absolute;
                left: 50%;
                transform: translateX(-50%);
                width: 10px;
                height: 150px;
                background-color: #fff;
                border: 1px solid #999;
            }
            
            .mercury {
                position: absolute;
                bottom: 0;
                width: 100%;
                height: 30%;
                background-color: #e74c3c;
                transition: height 0.5s;
            }
            
            .controls {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            '''
            
            test_js = '''
            const slider = document.getElementById('heat-slider');
            const mercury = document.querySelector('.mercury');
            const water = document.querySelector('.water');
            const tempDisplay = document.getElementById('temp-display');
            
            slider.addEventListener('input', () => {
                const heatLevel = slider.value;
                const mercuryHeight = 30 + (heatLevel * 0.7);
                const temp = 25 + (heatLevel * 0.75);
                
                mercury.style.height = mercuryHeight + '%';
                tempDisplay.textContent = temp.toFixed(1) + '°C';
                
                // Change water color based on temperature
                const blue = Math.max(0, 219 - (temp * 1.5));
                const red = Math.min(255, 52 + (temp * 2));
                water.style.backgroundColor = `rgb(${red}, 149, ${blue})`;
            });
            '''
            
            # Use the test content
            html = test_html
            css = test_css
            js = test_js
            
            # Store in session for subsequent requests
            req.session['html'] = html
            req.session['css'] = css
            req.session['js'] = js
            
            print("Using default thermometer simulation as fallback")
        
        preview_html = f"""<!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
            body {{
                background-color: #121212;
                color: #ffffff;
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            /* Default container for content */
            #content-container {{
                padding: 20px;
                flex-grow: 1;
            }}
            /* User CSS */
            {css}
            </style>
        </head>
        <body>
            <div id="content-container">
                {html}
            </div>
            <script>
            // Initialize content and catch errors
            try {{
                {js}
            }} catch (error) {{
                console.error('Error in JavaScript execution:', error);
                const errorDiv = document.createElement('div');
                errorDiv.style.color = 'red';
                errorDiv.style.padding = '10px';
                errorDiv.style.marginTop = '20px';
                errorDiv.style.border = '1px solid red';
                errorDiv.style.backgroundColor = '#ffeeee';
                errorDiv.innerHTML = '<strong>JavaScript Error:</strong><br>' + error.message;
                document.body.appendChild(errorDiv);
            }}
            </script>
        </body>
        </html>"""
        
        return HTMLResponse(preview_html, media_type="text/html")

    @rt('/api/html5/create-zip')
    async def post(req):
        """Create a downloadable ZIP file with index.html for SLS"""
        try:
            # Get form data
            form = await req.form()
            html = form.get('html-editor', '')
            css = form.get('css-editor', '')
            js = form.get('js-editor', '')
            
            # Prevent empty requests
            if not html and not css and not js:
                return """
                <div class="bg-gray-800 p-4 rounded border border-amber-500">
                    <h4 class="text-lg font-bold text-amber-400 mb-2">No Content Found</h4>
                    <p>Please add some HTML, CSS, or JavaScript content first.</p>
                </div>
                """
            
            # Generate a timestamp for the filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"html5_content_{timestamp}.zip"
            
            # Create the ZIP file
            zip_data = create_zip_file(html, css, js)
            
            # Encode the ZIP data as base64 for direct download
            encoded_zip = base64.b64encode(zip_data).decode('utf-8')
            
            # Return a download link as plain HTML instead of FT components
            # This avoids potential HTMX parsing issues
            return NotStr(f"""
            <div class="bg-gray-800 p-4 rounded border border-green-600">
                <h4 class="text-lg font-bold text-green-500 mb-2">SLS Package Ready!</h4>
                <p class="text-sm mb-2">Your HTML5 content has been packaged into a ZIP file ready for SLS.</p>
                <a href="data:application/zip;base64,{encoded_zip}" 
                download="{filename}" 
                class="inline-block bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded flex items-center w-fit">
                    <svg viewBox="0 0 24 24" width="20" height="20" class="mr-2">
                        <path d="M19 9h-4V3H9v6H5l7 7 7-7zm-8 2V5h2v6h1.17L12 13.17 9.83 11H11zm-6 7h14v2H5v-2z" fill="currentColor"></path>
                    </svg>
                    <span>Download ZIP</span>
                </a>
                <p class="text-xs text-gray-400 mt-2">Upload this ZIP directly to SLS as a media object.</p>
            </div>
            """)
            
        except Exception as error:
            import traceback
            error_details = traceback.format_exc()
            print(f"ZIP creation error: {str(error)}\n{error_details}")
            
            # Return error information as plain HTML
            return NotStr(f"""
            <div class="bg-gray-800 p-4 rounded border border-red-500">
                <h4 class="text-lg font-bold text-red-500 mb-2">Error Creating ZIP</h4>
                <p class="mb-2">Error: {str(error)}</p>
                <div class="text-xs p-2 bg-gray-900 overflow-auto max-h-32">
                    <pre>{error_details}</pre>
                </div>
            </div>
            """)


    @rt('/api/html5/generate-code')
    async def post(req):
        """Generate HTML5 code based on reference images and user prompt"""
        try:
            # Parse form data
            form = await req.form()
            print("----- Starting form parsing -----")
            print(f"Form keys: {list(form.keys())}")
            prompt = form.get('prompt', '')
            openai_key = os.environ["OPENAI_API_KEY"]
            anthropic_key = os.environ["ANTHROPIC_API_KEY"]
            model = form.get('model', 'gpt-4o')  # Default to GPT-4o
            
            # Check for iterative mode
            is_iterative = form.get('iterative-toggle') == 'on'
            print(f"Iterative mode setting from form: {form.get('iterative-toggle')}")
            print(f"Iterative mode: {'ON' if is_iterative else 'OFF'}")
            
            # IMPORTANT: Enhanced session debugging
            print("----- SESSION DEBUG -----")
            print(f"Session keys: {list(req.session.keys())}")
            for key in req.session.keys():
                value = req.session.get(key, '')
                value_len = len(str(value)) if value else 0
                print(f"Session[{key}] length: {value_len}")
                if value_len > 0 and value_len < 100 and isinstance(value, str):
                    print(f"Session[{key}] preview: {value}")
                elif value_len > 0 and isinstance(value, str):
                    print(f"Session[{key}] preview: {value[:100]}...")
            
            # Get code from both session and form data (belt and suspenders approach)
            # First try to get from session
            existing_html = req.session.get('html', '')
            existing_css = req.session.get('css', '')
            existing_js = req.session.get('js', '')
            
            # Then check form data directly from code editors as backup
            if not (existing_html or existing_css or existing_js):
                print("No code found in session, trying form data...")
                existing_html = form.get('html-editor', '')
                existing_css = form.get('css-editor', '')
                existing_js = form.get('js-editor', '')
            
            # Detailed debug output for retrieved code
            print(f"Retrieved HTML content length: {len(existing_html)}")
            print(f"Retrieved CSS content length: {len(existing_css)}")
            print(f"Retrieved JS content length: {len(existing_js)}")
            
            # Show short previews of the retrieved content
            if existing_html:
                print(f"HTML preview: {existing_html[:100]}...")
            if existing_css:
                print(f"CSS preview: {existing_css[:100]}...")
            if existing_js:
                print(f"JS preview: {existing_js[:100]}...")
            
            # Check for API keys
            if not openai_key and model.startswith(("gpt", "o1", "o3")):
                return Div("Please configure your OpenAI API key first", 
                        cls="error alert alert-warning")
            if not anthropic_key and model.startswith("claude"):
                return Div("Please configure your Anthropic API key first", 
                        cls="error alert alert-warning")
            
            if not prompt:
                return Div("Please provide a prompt for code generation", 
                        cls="error alert alert-warning")

            # Process uploaded images with improved logging
            print("----- Processing image uploads -----")
            
            # For Claude: base64 data + media_type pairs
            claude_image_data_list = []
            # For OpenAI: data URLs
            openai_image_data_list = []
            
            for i in range(5):
                base64_data = form.get(f'image-data-{i}', '')
                
                if base64_data and len(base64_data) > 100:  # Simple check to ensure it's likely valid base64 data
                    print(f"Processing image data for slot {i}")
                    
                    # Process for Claude
                    claude_processed_data, claude_media_type = process_image_for_claude(base64_data)
                    if claude_processed_data:
                        claude_image_data_list.append({
                            'data': claude_processed_data,
                            'media_type': claude_media_type
                        })
                        print(f"Successfully processed image {i} for Claude (format: {claude_media_type})")
                    
                    # Process for OpenAI
                    openai_data_url = process_image_for_openai(base64_data)
                    if openai_data_url:
                        openai_image_data_list.append(openai_data_url)
                        print(f"Successfully processed image {i} for OpenAI")
            
            # Continue with model selection and API calls
            print(f"Total images processed: {len(claude_image_data_list)} for Claude, {len(openai_image_data_list)} for OpenAI")
            print(f"Using model: {model}")
            
            # System prompt design with reference to images
            system_prompt = """
            You are a web developer specialized in HTML5 game and interactive content creation.
            
            Important:
            - Use the provided reference images as inspiration or as elements to reference in your code.
            - The images are provided as references only and should not be treated as the main objects of the interactive content.
            - Your code should work without requiring these exact images to be available.
            - Always return the complete code, with no omissions.
            - Your code has three separate components (HTML, CSS, JavaScript), each properly wrapped.
            - The HTML code must be properly wrapped in `<body>` and `</body>` tags.
            - The CSS code must be properly wrapped in `<style>` and `</style>` tags.
            - The JavaScript code must be properly wrapped in `<script>` and `</script>` tags.
            - Do **not** include any other code or text outside these tags.
            - Your code should be standalone, interactive, and visually engaging.
            """
            
            # Create a visual banner for iterative mode
            iterative_banner = None
            if is_iterative:
                iterative_banner = Div(
                    H3("🔄 Iterative Mode Active", cls="text-xl font-bold mb-2"),
                    P("Modifying existing code based on your instructions", cls="mb-0"),
                    cls="bg-blue-600 text-white p-4 mb-4 rounded-lg shadow-md"
                )
                
                # Add iterative mode instructions to system prompt
                system_prompt += """
                
                ITERATIVE MODE INSTRUCTIONS:
                - You are modifying existing HTML, CSS, and JavaScript code that the user has provided.
                - Maintain the same overall structure while making the improvements requested in the user's instructions.
                - Focus on addressing the specific requests while preserving the existing functionality.
                - Return the complete improved code with all three components properly wrapped.
                """
                
                # Only add code to prompt if we actually have some code
                has_existing_code = existing_html.strip() or existing_css.strip() or existing_js.strip()
                if has_existing_code:
                    print("Found existing code - adding to prompt for iteration")
                    
                    # Create a formatted version of the existing code to append to the prompt
                    existing_code_block = """
                    EXISTING CODE FOR ITERATION:

                    HTML:
                    ```html
                    {}
                    ```

                    CSS:
                    ```css
                    {}
                    ```

                    JavaScript:
                    ```javascript
                    {}
                    ```

                    Please modify the above code according to my instructions while maintaining the same overall structure.
                    """.format(existing_html, existing_css, existing_js)

                    # Append the existing code to the prompt
                    prompt = prompt + "\n\n" + existing_code_block
                    
                    # Debug output
                    print("Prompt updated with existing code for iteration")
                    print(f"Final prompt length: {len(prompt)}")
                else:
                    print("No existing code found for iteration")
            
            print("Final system prompt:", system_prompt)
            print(f"Starting API call to {model}...")
        
        # Rest of your code continues here...


    

            # Determine which AI service to use based on the model
            if model.startswith("claude"):
                # Use Anthropic/Claude
                import anthropic
                from anthropic._exceptions import OverloadedError, APIStatusError
                
                try:
                    client = anthropic.Anthropic(api_key=anthropic_key)
                    
                    # Build message content with images if available
                    message_content = [
                        {
                            "type": "text",
                            "text": f"{system_prompt} \n\nYour task is: {prompt}"
                        }
                    ]
                    
                    # Add images to the message content
                    for img_data in claude_image_data_list:
                        message_content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": img_data['media_type'],
                                "data": img_data['data']
                            }
                        })
                    
                    response = client.messages.create(
                        model=model,
                        max_tokens=4096,
                        temperature=0.2,
                        messages=[
                            {
                                "role": "user",
                                "content": message_content
                            }
                        ]
                    )
                    
                    if response:
                        code = response.content[0].text.strip()
                        # Extract components
                        html, css, js = extract_components(code)
                        
                        # When code is successfully generated, after storing in session:
                        # Store in session
                        req.session['html'] = html
                        req.session['css'] = css
                        req.session['js'] = js
                        print(f"Storing in session - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")


    
                        # CHANGE HERE: Instead of using the preview-content endpoint,
                        # create the complete HTML document directly
                        preview_content = f"""<!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <style>
                            body {{
                                background-color: #121212;
                                color: #ffffff;
                                margin: 0;
                                padding: 0;
                                font-family: Arial, sans-serif;
                                min-height: 100vh;
                                display: flex;
                                flex-direction: column;
                            }}
                            /* User CSS */
                            {css}
                            </style>
                        </head>
                        <body>
                            <div id="content-container">
                                {html}
                            </div>
                            <script>
                            // Initialize content and catch errors
                            try {{
                                {js}
                            }} catch (error) {{
                                console.error('Error in JavaScript execution:', error);
                                const errorDiv = document.createElement('div');
                                errorDiv.style.color = 'red';
                                errorDiv.style.padding = '10px';
                                errorDiv.innerHTML = '<strong>JavaScript Error:</strong><br>' + error.message;
                                document.body.appendChild(errorDiv);
                            }}
                            </script>
                        </body>
                        </html>"""
                        
                        # Encode the content as base64
                        import base64
                        encoded_content = base64.b64encode(preview_content.encode('utf-8')).decode('utf-8')
                        
                        # Return with a data URL for the iframe instead of a URL to preview-content
                        return [
                            iterative_banner if is_iterative else None,
                            create_code_editors(html, css, js),
                            NotStr(f"""
                            <script>
                            (function() {{
                                // Show the buttons
                                document.getElementById('run-preview-button').classList.remove('hidden');
                                document.getElementById('clear-button').classList.remove('hidden');
                                
                                // Update the preview directly with the data URL
                                document.getElementById('preview-container').innerHTML = `
                                    <iframe 
                                        src="data:text/html;base64,{encoded_content}" 
                                        width="100%" height="100%" 
                                        frameborder="0" 
                                        allowfullscreen="true" 
                                        style="background-color: #121212; display: block;">
                                    </iframe>
                                `;
                            }})();
                            </script>
                            """)
                        ]
                
                except OverloadedError:
                    # Handle Claude API overload gracefully
                    return Div(
                        H3("Claude API is Currently Overloaded", cls="text-xl font-bold text-amber-600 mb-4"),
                        P("The Claude API is experiencing high traffic right now. Please try one of the following:", 
                        cls="mb-4"),
                        Ul(
                            Li("Wait a few minutes and try again"),
                            Li("Switch to an OpenAI model using the dropdown above"),
                            Li("Try with a slightly shorter prompt"),
                            cls="list-disc pl-5 mb-4"
                        ),
                        Button(
                            "Try with GPT-4o instead",
                            cls="px-4 py-2 bg-blue-500 text-white rounded",
                            hx_post="/api/html5/generate-code",
                            hx_include="closest form",
                            hx_vals='{"model": "gpt-4o"}',
                            hx_target="#code-editors-container",
                            hx_indicator="#loading-indicator"
                        ),
                        cls="p-4 border border-amber-400 bg-amber-50 rounded"
                    )
                    
                except APIStatusError as e:
                    # Handle other API errors
                    return Div(
                        H3("Claude API Error", cls="text-xl font-bold text-red-600 mb-4"),
                        P(f"Error: {str(e)}", cls="mb-4"),
                        P("Please try an OpenAI model instead.", cls="mb-2"),
                        Button(
                            "Try with GPT-4o instead",
                            cls="px-4 py-2 bg-blue-500 text-white rounded",
                            hx_post="/api/html5/generate-code",
                            hx_include="closest form",
                            hx_vals='{"model": "gpt-4o"}',
                            hx_target="#code-editors-container",
                            hx_indicator="#loading-indicator"
                        ),
                        cls="p-4 border border-red-400 bg-red-50 rounded"
                    )
            else:
                # Use OpenAI
                from openai import OpenAI
                
                try:
                    client = OpenAI(api_key=openai_key)
                    
                    # Build messages with images if available
                    messages = [
                        {"role": "system", "content": system_prompt}
                    ]
                    
                    # Add user message with images if available
                    user_message_content = []
                    
                    # Add text prompt
                    user_message_content.append({
                        "type": "text",
                        "text": prompt
                    })
                    
                    # Add images to the content
                    for data_url in openai_image_data_list:
                        user_message_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": data_url
                            }
                        })
                    
                    # Add the user message with content
                    messages.append({
                        "role": "user",
                        "content": user_message_content
                    })
                    
                    response = client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=0.2,
                    )
                    
                    if response:
                        code = response.choices[0].message.content.strip()
                        # Extract components
                        html, css, js = extract_components(code)
                        
                        # When code is successfully generated, after storing in session:
                        # Store in session
                        req.session['html'] = html
                        req.session['css'] = css
                        req.session['js'] = js
                        
                        # Create iframe HTML for direct preview
                        preview_content = f"""<!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <style>
                            body {{
                                background-color: #121212;
                                color: #ffffff;
                                margin: 0;
                                padding: 0;
                                font-family: Arial, sans-serif;
                                min-height: 100vh;
                                display: flex;
                                flex-direction: column;
                            }}
                            /* User CSS */
                            {css}
                            </style>
                        </head>
                        <body>
                            <div id="content-container">
                                {html}
                            </div>
                            <script>
                            // Initialize content and catch errors
                            try {{
                                {js}
                            }} catch (error) {{
                                console.error('Error in JavaScript execution:', error);
                                const errorDiv = document.createElement('div');
                                errorDiv.style.color = 'red';
                                errorDiv.style.padding = '10px';
                                errorDiv.innerHTML = '<strong>JavaScript Error:</strong><br>' + error.message;
                                document.body.appendChild(errorDiv);
                            }}
                            </script>
                        </body>
                        </html>"""
                        
                        # Encode the content as base64
                        import base64
                        encoded_content = base64.b64encode(preview_content.encode('utf-8')).decode('utf-8')
                        
                        # Return with a data URL for the iframe instead of a URL to preview-content
                        return [
                            iterative_banner if is_iterative else None,
                            create_code_editors(html, css, js),
                            NotStr(f"""
                            <script>
                            (function() {{
                                // Show the buttons
                                document.getElementById('run-preview-button').classList.remove('hidden');
                                document.getElementById('clear-button').classList.remove('hidden');
                                
                                // Update the preview directly with the data URL
                                document.getElementById('preview-container').innerHTML = `
                                    <iframe 
                                        src="data:text/html;base64,{encoded_content}" 
                                        width="100%" height="100%" 
                                        frameborder="0" 
                                        allowfullscreen="true" 
                                        style="background-color: #121212; display: block;">
                                    </iframe>
                                `;
                            }})();
                            </script>
                            """)
                        ]
                        
                except Exception as e:
                    return Div(
                        H3("OpenAI API Error", cls="text-xl font-bold text-red-600 mb-4"),
                        P(f"Error: {str(e)}", cls="mb-4"),
                        cls="p-4 border border-red-400 bg-red-50 rounded"
                    )
                    
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return Div(
                H3("Error Generating Code", cls="text-xl font-bold text-red-600 mb-4"),
                P(f"Error: {str(e)}", cls="mb-2"),
                details := Details(
                    Summary("View Error Details", cls="cursor-pointer text-blue-500"),
                    Pre(error_details, cls="mt-2 p-4 bg-gray-100 overflow-auto text-xs")
                ),
                # Add a button to try with OpenAI instead
                Div(
                    P("You can try using a different model:", cls="mt-4 mb-2"),
                    Button(
                        "Try with GPT-4o instead",
                        cls="px-4 py-2 bg-blue-500 text-white rounded mr-2",
                        hx_post="/api/html5/generate-code",
                        hx_include="closest form",
                        hx_vals='{"model": "gpt-4o"}',
                        hx_target="#code-editors-container",
                        hx_indicator="#loading-indicator"
                    ),
                    cls="mt-2"
                ),
                cls="error alert alert-danger p-4"
            )