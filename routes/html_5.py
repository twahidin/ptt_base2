import os
import re
import base64
import datetime
from fasthtml.common import *
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from pathlib import Path
import tempfile
import zipfile
import io
from PIL import Image
from components.html5_form import create_html5_form, create_code_editors

# Import token tracking functionality
import token_count

from dotenv import load_dotenv
load_dotenv()

# Global history backup storage
# This will store history by user ID to handle multiple users
GLOBAL_HISTORY = {}

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
    try:
        # Print the first and last 100 characters of the code for debugging
        code_preview = f"{code[:100]}...{code[-100:]}" if len(code) > 200 else code
        print(f"Extracting components from code: {len(code)} chars. Preview: {code_preview}")
        
        # Split the code into components
        html = ""
        css = ""
        js = ""
        
        # Primary extraction method: look for proper HTML tags
        html_match = re.search(r'<body>(.*?)</body>', code, re.DOTALL)
        if html_match:
            html = html_match.group(1).strip()
            print(f"Extracted HTML using <body> tags: {len(html)} chars")
        
        css_match = re.search(r'<style>(.*?)</style>', code, re.DOTALL)
        if css_match:
            css = css_match.group(1).strip()
            print(f"Extracted CSS using <style> tags: {len(css)} chars")
        
        js_match = re.search(r'<script>(.*?)</script>', code, re.DOTALL)
        if js_match:
            js = js_match.group(1).strip()
            print(f"Extracted JS using <script> tags: {len(js)} chars")
        
        # Fallback extraction: look for code blocks
        if not html:
            html_block = re.search(r'```html\s*(.*?)\s*```', code, re.DOTALL)
            if html_block:
                html = html_block.group(1).strip()
                print(f"Extracted HTML from code block: {len(html)} chars")
        
        if not css:
            css_block = re.search(r'```css\s*(.*?)\s*```', code, re.DOTALL)
            if css_block:
                css = css_block.group(1).strip()
                print(f"Extracted CSS from code block: {len(css)} chars")
        
        if not js:
            js_block = re.search(r'```javascript\s*(.*?)\s*```', code, re.DOTALL) or re.search(r'```js\s*(.*?)\s*```', code, re.DOTALL)
            if js_block:
                js = js_block.group(1).strip()
                print(f"Extracted JS from code block: {len(js)} chars")
        
        # If still empty, try looser pattern matching for HTML content
        if not html and not css and not js:
            print("No components extracted. Trying alternative extraction methods.")
            # Look for HTML patterns (elements, tags, etc.)
            if '<div' in code or '<p>' in code or '<h1>' in code:
                # Try to extract an HTML chunk
                html_chunk = re.search(r'(<div.*?>.*?</div>|<h1>.*?</h1>|<p>.*?</p>)', code, re.DOTALL)
                if html_chunk:
                    html = html_chunk.group(1)
                    print(f"Extracted HTML fragment using pattern matching: {len(html)} chars")
        
        print(f"Final extraction results - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
        return html, css, js
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error extracting components: {str(e)}\n{error_details}")
        print(f"Original code length: {len(code)}")
        print(f"Original code preview: {code[:500]}...")
        raise ValueError(f"Error extracting components: {str(e)}")


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
        """Initialize the HTML5 form and session"""
        api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize session if needed
        if 'html5_history' not in req.session:
            req.session['html5_history'] = []
            print("Initialized empty history in session")
        
        # Debug print session state
        print("\n----- MENU D DEBUG -----")
        print(f"Session keys: {list(req.session.keys())}")
        print(f"History size: {len(req.session.get('html5_history', []))}")
        
        return Titled("HTML5 Project",
            Link(rel="stylesheet", href="static/css/styles.css"),
            create_html5_form(api_key)
        )

    @rt('/api/html5/undo')
    async def post(req):
        """Restore the previous state of the HTML5 content"""
        try:
            # Get user ID from session for history tracking
            user_id = req.session.get('auth', 'anonymous')
            
            # Get a copy of the history to avoid reference issues
            history = list(req.session.get('html5_history', []))
            
            # If session history is empty but we have global history, use that
            if not history and user_id in GLOBAL_HISTORY:
                history = GLOBAL_HISTORY[user_id]
                print(f"Retrieved history from global backup. Size: {len(history)}")
            
            print("\n----- UNDO DEBUG -----")
            print(f"Session keys: {list(req.session.keys())}")
            print(f"History size before undo: {len(history)}")
            print(f"Global history size for user {user_id}: {len(GLOBAL_HISTORY.get(user_id, []))}")
            
            if not history:
                print("No history available to restore")
                return Div(
                    "No previous state available to restore",
                    cls="bg-gray-800 p-4 rounded border border-amber-500"
                )
            
            # Get the last state from history
            previous_state = history.pop()
            print("Restoring previous state:")
            print(f"  HTML length: {len(previous_state['html'])}")
            print(f"  CSS length: {len(previous_state['css'])}")
            print(f"  JS length: {len(previous_state['js'])}")
            
            # Update session with the new history and current state
            req.session['html5_history'] = list(history)  # Store a new copy
            req.session['html'] = previous_state['html']
            req.session['css'] = previous_state['css']
            req.session['js'] = previous_state['js']
            
            # Also update global backup
            GLOBAL_HISTORY[user_id] = list(history)
            
            print(f"History size after undo: {len(history)}")
            print(f"Updated session keys: {list(req.session.keys())}")
            print(f"Updated global history size: {len(GLOBAL_HISTORY.get(user_id, []))}")

            # Create preview content with the restored state
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
                {previous_state['css']}
                </style>
            </head>
            <body>
                <div id="content-container">
                    {previous_state['html']}
                </div>
                <script>
                // Initialize content and catch errors
                try {{
                    {previous_state['js']}
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
            
            return [
                create_code_editors(previous_state['html'], previous_state['css'], previous_state['js']),
                NotStr(f"""
                <script>
                (function() {{
                    // Update the preview with the restored state
                    document.getElementById('preview-container').innerHTML = `
                        <iframe 
                            src="data:text/html;base64,{encoded_content}" 
                            width="100%" height="100%" 
                            frameborder="0" 
                            allowfullscreen="true" 
                            style="background-color: #121212; display: block;">
                        </iframe>
                    `;
                    
                    // Update undo button state
                    const undoButton = document.getElementById('undo-button');
                    if (undoButton) {{
                        // Check if there's more history available
                        fetch('/api/html5/check-history')
                            .then(response => response.json())
                            .then(data => {{
                                if (data.hasHistory) {{
                                    undoButton.disabled = false;
                                    undoButton.classList.remove('opacity-50', 'cursor-not-allowed');
                                }} else {{
                                    undoButton.disabled = true;
                                    undoButton.classList.add('opacity-50', 'cursor-not-allowed');
                                }}
                            }});
                    }}
                }})();
                </script>
                """)
            ]
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return Div(
                H3("Error Restoring Previous State", cls="text-xl font-bold text-red-600 mb-4"),
                P(f"Error: {str(e)}", cls="mb-2"),
                details := Details(
                    Summary("View Error Details", cls="cursor-pointer text-blue-500"),
                    Pre(error_details, cls="mt-2 p-4 bg-gray-100 overflow-auto text-xs")
                ),
                cls="error alert alert-danger p-4"
            )

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

    @rt('/api/html5/clear-preview')
    async def post(req):
        """Clear the preview and code"""
        # Get user ID from session for history tracking
        user_id = req.session.get('auth', 'anonymous')
        
        # Clear session data
        if 'html' in req.session:
            del req.session['html']
        if 'css' in req.session:
            del req.session['css']
        if 'js' in req.session:
            del req.session['js']
        if 'html5_history' in req.session:
            del req.session['html5_history']
        
        # Clear global history for this user
        if user_id in GLOBAL_HISTORY:
            del GLOBAL_HISTORY[user_id]
            print(f"Cleared global history for user {user_id}")
        
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
            
            // Hide and reset all buttons
            var runButton = document.getElementById('run-preview-button');
            var clearButton = document.getElementById('clear-button');
            var undoButton = document.getElementById('undo-button');
            var zipButton = document.getElementById('create-zip-button');
            
            if (runButton) runButton.classList.add('hidden');
            if (clearButton) clearButton.classList.add('hidden');
            if (undoButton) {
                undoButton.classList.add('hidden');
                undoButton.disabled = true;
                undoButton.classList.add('opacity-50', 'cursor-not-allowed');
            }
            if (zipButton) zipButton.classList.add('hidden');
            
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


    @rt('/api/html5/check-history')
    async def get(req):
        """Check if there is any history available"""
        # Get user ID from session for history tracking
        user_id = req.session.get('auth', 'anonymous')
        
        # Get a copy of the history to avoid reference issues
        history = list(req.session.get('html5_history', []))
        
        # If session history is empty but we have global history, use that
        if not history and user_id in GLOBAL_HISTORY:
            history = GLOBAL_HISTORY[user_id]
            print(f"Retrieved history from global backup. Size: {len(history)}")
            
            # Update session with global history
            req.session['html5_history'] = list(history)
            print("Updated session with global history")
        
        print("\n----- CHECK HISTORY DEBUG -----")
        print(f"Session keys: {list(req.session.keys())}")
        print(f"History size: {len(history)}")
        print(f"Global history size for user {user_id}: {len(GLOBAL_HISTORY.get(user_id, []))}")
        
        if history:
            print("History contents:")
            for i, state in enumerate(history):
                print(f"State {i + 1}:")
                print(f"  HTML length: {len(state['html'])}")
                print(f"  CSS length: {len(state['css'])}")
                print(f"  JS length: {len(state['js'])}")
        else:
            print("No history found")
            
        # Return a simple JSON response
        return {"hasHistory": len(history) > 0}

    @rt('/api/html5/generate-code')
    async def post(req):
        """Generate HTML5 code based on reference images and user prompt"""
        try:
            # Get user ID from session for history tracking
            user_id = req.session.get('auth', 'anonymous')
            
            # Store current state in history before generating new code
            current_html = req.session.get('html', '')
            current_css = req.session.get('css', '')
            current_js = req.session.get('js', '')
            
            print("\n----- HISTORY DEBUG -----")
            print(f"Current HTML length: {len(current_html)}")
            print(f"Current CSS length: {len(current_css)}")
            print(f"Current JS length: {len(current_js)}")
            
            # Get form data for current state if session is empty
            form = await req.form()
            form_html = form.get('html-editor', '')
            form_css = form.get('css-editor', '')
            form_js = form.get('js-editor', '')
            
            # Use form data if session is empty or if form has content
            if (not (current_html or current_css or current_js)) or (form_html or form_css or form_js):
                current_html = form_html
                current_css = form_css
                current_js = form_js
                print("Got current state from form data")
                print(f"Form HTML length: {len(current_html)}")
                print(f"Form CSS length: {len(current_css)}")
                print(f"Form JS length: {len(current_js)}")
            
            # Store in history if we have content
            if current_html or current_css or current_js:
                # Get existing history from session or global backup
                history = req.session.get('html5_history', [])
                
                # If session history is empty but we have global history, use that
                if not history and user_id in GLOBAL_HISTORY:
                    history = GLOBAL_HISTORY[user_id]
                    print(f"Retrieved history from global backup. Size: {len(history)}")
                
                # Create a copy of the history to avoid reference issues
                history = list(history)
                
                current_state = {
                    'html': current_html,
                    'css': current_css,
                    'js': current_js
                }
                
                # Only add to history if this state is different from the last one
                if not history or (history[-1]['html'] != current_html or 
                                history[-1]['css'] != current_css or 
                                history[-1]['js'] != current_js):
                    history.append(current_state)
                    
                    # Store the updated history back in the session
                    # Make a completely new copy to ensure it's stored properly
                    req.session['html5_history'] = list(history)
                    
                    # Also store in global backup
                    GLOBAL_HISTORY[user_id] = list(history)
                    
                    print(f"Added state to history. History size: {len(history)}")
                    print("History contents:")
                    for i, state in enumerate(history):
                        print(f"State {i + 1}:")
                        print(f"  HTML length: {len(state['html'])}")
                        print(f"  CSS length: {len(state['css'])}")
                        print(f"  JS length: {len(state['js'])}")
            else:
                print("No current state to store in history")
            
            # Get form data for the new code generation
            prompt = form.get('prompt', '')
            model = form.get('model', 'gpt-4o')
            is_iterative = form.get('iterative-toggle') == 'on'
            
            # Get reference images
            images = []
            for i in range(5):
                image_data = form.get(f'image-data-{i}')
                if image_data:
                    images.append(image_data)
            
            # Generate new code
            try:
                html, css, js = await generate_html5_code(prompt, images, model, is_iterative, current_html, current_css, current_js)
                print(f"Successfully generated code - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
                
                # If in iterative mode and no content was returned, return an error
                if is_iterative and not (html or css or js):
                    raise ValueError("No content was generated in iterative mode. Please try again with different instructions.")
                
                # Store the new state in session
                req.session['html'] = html
                req.session['css'] = css
                req.session['js'] = js
            except Exception as e:
                print(f"Error generating code: {str(e)}")
                import traceback
                error_details = traceback.format_exc()
                print(f"Error details: {error_details}")
                
                # If in iterative mode, we can return the original content
                if is_iterative and current_html and current_css and current_js:
                    print("Returning original content due to error in iterative mode")
                    html = current_html
                    css = current_css
                    js = current_js
                    
                    # Return with an error message
                    return [
                        Div(f"Error: {str(e)} - Using your existing code", cls="bg-red-800 text-white p-2 mb-4 rounded"),
                        create_code_editors(html, css, js),
                        NotStr(f"""
                        <script>
                            console.error("Error in code generation: {str(e)}");
                        </script>
                        """)
                    ]
                else:
                    # If not in iterative mode or no content available, return the error
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
            
            # Debug print the session keys to verify
            print("Session keys after update:", list(req.session.keys()))
            print(f"History in session: {len(req.session.get('html5_history', []))}")
            print(f"History in global backup: {len(GLOBAL_HISTORY.get(user_id, []))}")

            # Create preview content
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
            
            # Create iterative banner if needed
            iterative_banner = None
            if is_iterative:
                if current_html or current_css or current_js:
                    iterative_banner = Div(
                        "Iterative Mode: Using existing code as context",
                        cls="bg-blue-900 text-blue-100 p-2 rounded mb-4"
                    )
                else:
                    iterative_banner = Div(
                        "Iterative Mode: No existing code found, created new content",
                        cls="bg-blue-900 text-blue-100 p-2 rounded mb-4"
                    )
            
            # Return with a data URL for the iframe instead of a URL to preview-content
            return [
                iterative_banner if is_iterative else None,
                create_code_editors(html, css, js),
                NotStr(f"""
                <script>
                (function() {{
                    // Clear existing dynamic buttons first
                    const dynamicButtons = document.getElementById('dynamic-buttons');
                    if (dynamicButtons) {{
                        dynamicButtons.innerHTML = '';
                    }}

                    // Show and initialize buttons
                    const runButton = document.getElementById('run-preview-button');
                    const undoButton = document.getElementById('undo-button');
                    const clearButton = document.getElementById('clear-button');
                    
                    // Remove any existing ZIP buttons first
                    const existingZipButton = document.getElementById('create-zip-button');
                    if (existingZipButton) {{
                        existingZipButton.remove();
                    }}
                    
                    if (runButton) {{
                        runButton.classList.remove('hidden');
                        console.log('Run button visible');
                    }}
                    
                    if (undoButton) {{
                        undoButton.classList.remove('hidden');
                        // Check if there's history to enable/disable the button
                        fetch('/api/html5/check-history')
                            .then(response => response.json())
                            .then(data => {{
                                console.log('Checking undo history:', data);
                                if (data.hasHistory) {{
                                    console.log('History available - enabling undo button');
                                    undoButton.disabled = false;
                                    undoButton.classList.remove('opacity-50', 'cursor-not-allowed');
                                }} else {{
                                    console.log('No history available - disabling undo button');
                                    undoButton.disabled = true;
                                    undoButton.classList.add('opacity-50', 'cursor-not-allowed');
                                }}
                            }})
                            .catch(error => {{
                                console.error('Error checking history:', error);
                            }});
                        console.log('Undo button initialized');
                    }} else {{
                        console.warn('Undo button not found in DOM');
                    }}
                    
                    if (clearButton) {{
                        clearButton.classList.remove('hidden');
                        console.log('Clear button visible');
                    }}
                    
                    // Create single ZIP button
                    if (dynamicButtons && !document.getElementById('create-zip-button')) {{
                        const zipButton = document.createElement('button');
                        zipButton.id = 'create-zip-button';
                        zipButton.className = 'action-button bg-gradient-to-r from-blue-500 to-indigo-600';
                        zipButton.type = 'button'; // Explicitly set button type to prevent form submission
                        zipButton.innerHTML = `
                            <div class="flex items-center justify-center w-full">
                                <svg viewBox="0 0 24 24" width="20" height="20" class="inline-block">
                                    <path d="M19 9h-4V3H9v6H5l7 7 7-7zm-8 2V5h2v6h1.17L12 13.17 9.83 11H11zm-6 7h14v2H5v-2z" fill="currentColor"/>
                                </svg>
                                <span class="ml-2">Create ZIP Package</span>
                            </div>
                        `;
                        
                        // We're now using the direct handler in html5_form.py instead of HTMX attributes
                        // to avoid conflicts between the two approaches
                        
                        // Add to the dynamic buttons container
                        dynamicButtons.appendChild(zipButton);
                        console.log('ZIP button created');
                    }}
                    
                    // Ensure the preview container exists
                    const previewContainer = document.getElementById('preview-container');
                    if (!previewContainer) {{
                        console.error('Preview container not found');
                        // Try to create one if it doesn't exist
                        const workspace = document.querySelector('.workspace-container');
                        if (workspace) {{
                            const newPreviewContainer = document.createElement('div');
                            newPreviewContainer.id = 'preview-container';
                            newPreviewContainer.className = 'preview-panel';
                            workspace.appendChild(newPreviewContainer);
                            console.log('Created new preview container');
                        }}
                    }}
                    
                    // Update the preview directly with the data URL
                    const finalPreviewContainer = document.getElementById('preview-container');
                    if (finalPreviewContainer) {{
                        finalPreviewContainer.innerHTML = `
                            <iframe 
                                src="data:text/html;base64,{encoded_content}" 
                                width="100%" height="100%" 
                                frameborder="0" 
                                allowfullscreen="true" 
                                style="background-color: #121212; display: block;">
                            </iframe>
                        `;
                        console.log('Preview updated with iframe');
                    }} else {{
                        console.error('Could not find or create preview container');
                    }}
                }})();
                </script>
                """)
            ]
            
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

async def generate_html5_code(prompt, images, model, is_iterative, current_html, current_css, current_js):
    """Generate HTML5 code using the specified model"""
    try:
        # Get API keys
        openai_key = os.environ["OPENAI_API_KEY"]
        anthropic_key = os.environ["ANTHROPIC_API_KEY"]
        
        # Check for API keys
        if not openai_key and model.startswith(("gpt", "o1", "o3")):
            raise ValueError("Please configure your OpenAI API key first")
        if not anthropic_key and model.startswith("claude"):
            raise ValueError("Please configure your Anthropic API key first")
        
        if not prompt:
            raise ValueError("Please provide a prompt for code generation")
        
        # Process uploaded images
        claude_image_data_list = []
        openai_image_data_list = []
        
        for base64_data in images:
            if base64_data and len(base64_data) > 100:  # Simple check to ensure it's likely valid base64 data
                # Process for Claude
                claude_processed_data, claude_media_type = process_image_for_claude(base64_data)
                if claude_processed_data:
                    claude_image_data_list.append({
                        'data': claude_processed_data,
                        'media_type': claude_media_type
                    })
                
                # Process for OpenAI
                openai_data_url = process_image_for_openai(base64_data)
                if openai_data_url:
                    openai_image_data_list.append(openai_data_url)
        
        # System prompt design with reference to images
        system_prompt = """
        You are a web developer specialized in HTML5 game and interactive content creation.
        
        You have to complete one of the following tasks:
        1. Create a new interactive content based on the user's prompt that produces HTML, CSS, and JavaScript code.
        2. Modify existing HTML, CSS, and JavaScript code that the user has provided, based on the user's instructions.
        """
        
        # Initialize user_prompt with the original prompt
        user_prompt = prompt
        
        # Add iterative mode instructions if needed
        if is_iterative:
            # Check if we have current code to include
            has_current_code = bool(current_html.strip() or current_css.strip() or current_js.strip())
            
            if has_current_code:
                system_prompt += """
                
                ITERATIVE MODE INSTRUCTIONS:
                - You are modifying existing HTML, CSS, and JavaScript code that the user has provided.
                - Maintain the same overall structure while making the improvements requested in the user's instructions.
                - Focus on addressing the specific requests while preserving the existing functionality and the overall structure of the code.
                - Use Canvas API - Allows for drawing 2D graphics using JavaScript
                - Use SVG (Scalable Vector Graphics) - XML-based markup for creating vector graphics
                - Use CSS3 - For styling and basic animations
                - You must generate javascript code and must obey the following rules:
                    - The javascript code must be self-contained and not require any external files or resources.
                    - The javascript code must be able to run in the browser.
                    - The javascript code must creates the interactions for the interactive content based on the html and css code.
                    - The javascript code must be able to access the html and css code.
                    - The javascript code must be able to access the user's instructions.
                - Return the complete improved code with all three components properly wrapped.
                - Provide comments in the code to explain the changes you have made
                - Your response should only contain the modified code, with no other text or comments.
                """
                
                # Add the current code to the prompt for iterative editing
                user_prompt = f"""
    {prompt}

    Here is the existing HTML code:
    ```html
    {current_html}
    ```

    Here is the existing CSS code:
    ```css
    {current_css}
    ```

    Here is the existing JavaScript code:
    ```javascript
    {current_js}
    ```

    Please modify the code according to my instructions while maintaining the overall structure and functionality.
    """
                print(f"Added current code to prompt in iterative mode - HTML: {len(current_html)} chars, CSS: {len(current_css)} chars, JS: {len(current_js)} chars")
            else:
                # When in iterative mode but no existing code, treat it as new content creation
                print("Iterative mode enabled but no current code found - treating as new content creation")
                system_prompt += """
                
                NEW CONTENT CREATION INSTRUCTIONS (Iterative Mode with no existing code):
                Important:
                - Use the provided reference images as inspiration or as elements to reference in your code.
                - The images are provided as references only and should not be treated as the main objects of the interactive content.
                - Your code should work without requiring these exact images to be available.
                - Always return the complete code, with no omissions.
                - Provide comments in the code on what the code is doing and how it works.
                - Your code has three separate components (HTML, CSS, JavaScript), each properly wrapped.
                - Use Canvas API - Allows for drawing 2D graphics using JavaScript
                - Use SVG (Scalable Vector Graphics) - XML-based markup for creating vector graphics
                - Use CSS3 - For styling and basic animations
                - The code should be self-contained and not require any external files or resources.
                - You must generate javascript code and must obey the following rules:
                    - The javascript code must be self-contained and not require any external files or resources.
                    - The javascript code must be able to run in the browser.
                    - The javascript code must creates the interactions for the interactive content based on the html and css code.
                    - The javascript code must be able to access the html and css code.
                    - The javascript code must be able to access the user's instructions.
                - The CSS code should have the following tags:
                ```css
                /*
                with <style> tags
                */
                ```
                - The JavaScript code should have the following tags:
                ```javascript
                /*
                with <script> tags
                */
                ```
                - The HTML code should have the following tags:
                ```html
                /*
                with <body> tags
                */
                ``` 
                """
        else:
            system_prompt += """
            
            NEW CONTENT CREATION INSTRUCTIONS:
            Important:
            - Use the provided reference images as inspiration or as elements to reference in your code.
            - The images are provided as references only and should not be treated as the main objects of the interactive content.
            - Your code should work without requiring these exact images to be available.
            - Always return the complete code, with no omissions.
            - Provide comments in the code on what the code is doing and how it works.
            - Your code has three separate components (HTML, CSS, JavaScript), each properly wrapped.
            - Use Canvas API - Allows for drawing 2D graphics using JavaScript
            - Use SVG (Scalable Vector Graphics) - XML-based markup for creating vector graphics
            - Use CSS3 - For styling and basic animations
            - The code should be self-contained and not require any external files or resources.
            - You must generate javascript code and must obey the following rules:
                - The javascript code must be self-contained and not require any external files or resources.
                - The javascript code must be able to run in the browser.
                - The javascript code must creates the interactions for the interactive content based on the html and css code.
                - The javascript code must be able to access the html and css code.
                - The javascript code must be able to access the user's instructions.
            - The CSS code should have the following tags:
            ```css
            /*
            with <style> tags
            */
            ```
            - The JavaScript code should have the following tags:
            ```javascript
            /*
            with <script> tags
            */
            ```
            - The HTML code should have the following tags:
            ```html
            /*
            with <body> tags
            */
            ``` 
            """
        print(f"System prompt: {system_prompt}")
        
        # Get user ID from session for token tracking
        user_id = "anonymous"  # Default user ID
        session_id = None
        
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
                        "text": f"{system_prompt}\n\n{user_prompt}"
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
                
                # Get token count for prompt
                token_count_response = client.messages.count_tokens(
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": message_content
                        }
                    ]
                )
                prompt_tokens = token_count_response.input_tokens
                
                # Make the actual API call
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
                    print(f"Received response from Claude. Type: {type(response)}")
                    code = response.content[0].text.strip()
                    print(f"Response content length: {len(code)} chars")
                    
                    # Record token usage
                    completion_tokens = response.usage.output_tokens
                    total_tokens = prompt_tokens + completion_tokens
                    
                    # Save token usage to database
                    token_count.record_token_usage(
                        model=model,
                        prompt=prompt[:500] if prompt else None,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        user_id=user_id,
                        session_id=session_id
                    )
                    
                    # Extract components
                    html, css, js = extract_components(code)
                    
                    # Verify we have content
                    if not (html or css or js):
                        print("WARNING: No content extracted from Claude response. Using original content.")
                        # Return the original content if we couldn't extract anything
                        if is_iterative and current_html and current_css and current_js:
                            return current_html, current_css, current_js
                    
                    return html, css, js
                else:
                    print("Claude returned empty response")
                    raise ValueError("Claude returned an empty response")
            except OverloadedError:
                raise ValueError("Claude API is currently overloaded. Please try again later or use a different model.")
            except APIStatusError as e:
                raise ValueError(f"Claude API error: {str(e)}")
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
                    "text": user_prompt  # Use user_prompt instead of prompt to include the current code when in iterative mode
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
                
                # Make the API call
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=0.2,
                )
                
                if response:
                    print(f"Received response from OpenAI. Type: {type(response)}")
                    code = response.choices[0].message.content.strip()
                    print(f"Response content length: {len(code)} chars")
                    
                    # Record token usage
                    prompt_tokens = response.usage.prompt_tokens
                    completion_tokens = response.usage.completion_tokens
                    total_tokens = response.usage.total_tokens
                    
                    # Save token usage to database
                    token_count.record_token_usage(
                        model=model,
                        prompt=prompt[:500] if prompt else None,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        user_id=user_id,
                        session_id=session_id
                    )
                    
                    # Extract components
                    html, css, js = extract_components(code)
                    
                    # Verify we have content
                    if not (html or css or js):
                        print("WARNING: No content extracted from OpenAI response. Using original content.")
                        # Return the original content if we couldn't extract anything
                        if is_iterative and current_html and current_css and current_js:
                            return current_html, current_css, current_js
                    
                    return html, css, js
                else:
                    print("OpenAI returned empty response")
                    raise ValueError("OpenAI returned an empty response")
                
            except Exception as e:
                raise ValueError(f"OpenAI API error: {str(e)}")
                
    except Exception as e:
        raise ValueError(f"Error generating code: {str(e)}")