import os
import re
import base64
import datetime
import json
from fasthtml.common import *
from starlette.responses import RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from pathlib import Path
import tempfile
import zipfile
import io
from PIL import Image
from components.html5_form import create_html5_form, create_code_editors
import yaml  # Add import for yaml config

# Import token tracking functionality
import token_count

from dotenv import load_dotenv
load_dotenv()

# Load config.yaml for settings
try:
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    SETTINGS = config.get('settings', {})
    EXTENDED_THINKING_MODE = SETTINGS.get('extended_thinking_mode', False)
    print(f"Loaded settings from config.yaml. Extended thinking mode: {EXTENDED_THINKING_MODE}")
except Exception as e:
    print(f"Error loading config.yaml: {e}. Using default settings.")
    EXTENDED_THINKING_MODE = False
    SETTINGS = {}

# Global history backup storage
# This will store history by user ID to handle multiple users
GLOBAL_HISTORY = {}

# New simplified global storage for current and previous states
# Format: { user_id: { 'current': { 'html': '...', 'css': '...', 'js': '...' }, 'previous': { 'html': '...', 'css': '...', 'js': '...' } } }
GLOBAL_CODE_STORAGE = {}

# Redis client for drafts storage
redis_client = None
try:
    import redis
    REDIS_URL = os.environ.get('HTML5_REDIS_URL')
    if not REDIS_URL:
        print("Warning: HTML5_REDIS_URL environment variable not set. Using default localhost connection.")
        REDIS_URL = "redis://localhost:6379/0"
    
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()  # Test connection
    print("Connected to Redis successfully for drafts storage")
except Exception as e:
    print(f"Error connecting to Redis for drafts: {str(e)}. Using fallback in-memory storage.")
    redis_client = None

# In-memory fallback for drafts when Redis is not available
DRAFTS_MEMORY = {}

# Draft management functions
def save_draft(user_id, html, css, js):
    """
    Save a draft of HTML5 content to Redis or memory fallback
    
    Args:
        user_id (str): User ID
        html (str): HTML content
        css (str): CSS content
        js (str): JavaScript content
        
    Returns:
        str: Draft ID
    """
    if not user_id:
        user_id = "anonymous"
    
    timestamp = datetime.datetime.now().isoformat()
    draft_data = {
        "html": html,
        "css": css,
        "js": js,
        "timestamp": timestamp
    }
    
    # Create a unique draft ID using timestamp
    unique_draft_id = f"{int(datetime.datetime.now().timestamp())}"
    
    if redis_client:
        try:
            # Check if we've reached the draft limit (10)
            user_drafts_key = f"html5_drafts:{user_id}"
            current_drafts = redis_client.hkeys(user_drafts_key)
            if len(current_drafts) >= 10:
                return None, "Draft limit reached"
            
            # Save the draft with unique ID
            redis_client.hset(user_drafts_key, unique_draft_id, json.dumps(draft_data))
            
            print(f"Saved draft {unique_draft_id} for user {user_id}")
            return unique_draft_id, None
        except Exception as e:
            print(f"Error saving draft to Redis: {str(e)}. Falling back to memory.")
            
            # Fallback to memory
            if user_id not in DRAFTS_MEMORY:
                DRAFTS_MEMORY[user_id] = {}
            
            # Check if we've reached the draft limit
            if len(DRAFTS_MEMORY[user_id]) >= 10:
                return None, "Draft limit reached"
            
            DRAFTS_MEMORY[user_id][unique_draft_id] = draft_data
            
            return unique_draft_id, None
    else:
        # Direct memory storage
        if user_id not in DRAFTS_MEMORY:
            DRAFTS_MEMORY[user_id] = {}
        
        # Check if we've reached the draft limit
        if len(DRAFTS_MEMORY[user_id]) >= 10:
            return None, "Draft limit reached"
        
        DRAFTS_MEMORY[user_id][unique_draft_id] = draft_data
        
        return unique_draft_id, None

def get_all_drafts(user_id):
    """
    Get all drafts for a user
    
    Args:
        user_id (str): User ID
        
    Returns:
        list: List of draft objects with id and timestamp
    """
    if not user_id:
        user_id = "anonymous"
    
    drafts = []
    
    if redis_client:
        try:
            # Get all drafts for this user
            user_drafts_key = f"html5_drafts:{user_id}"
            draft_ids = redis_client.hkeys(user_drafts_key)
            
            for draft_id in draft_ids:
                draft_id_str = draft_id.decode('utf-8') if isinstance(draft_id, bytes) else draft_id
                draft_data_str = redis_client.hget(user_drafts_key, draft_id)
                if draft_data_str:
                    draft_data = json.loads(draft_data_str)
                    drafts.append({
                        "id": draft_id_str,
                        "timestamp": draft_data.get("timestamp", "Unknown")
                    })
            
            # Sort drafts by timestamp (newest first)
            drafts.sort(key=lambda x: x["timestamp"], reverse=True)
            return drafts
        except Exception as e:
            print(f"Error getting drafts from Redis: {str(e)}. Falling back to memory.")
            
            # Fallback to memory
            if user_id in DRAFTS_MEMORY:
                for draft_id, draft_data in DRAFTS_MEMORY[user_id].items():
                    drafts.append({
                        "id": draft_id,
                        "timestamp": draft_data.get("timestamp", "Unknown")
                    })
                
                # Sort drafts by timestamp (newest first)
                drafts.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return drafts
    else:
        # Direct memory retrieval
        if user_id in DRAFTS_MEMORY:
            for draft_id, draft_data in DRAFTS_MEMORY[user_id].items():
                drafts.append({
                    "id": draft_id,
                    "timestamp": draft_data.get("timestamp", "Unknown")
                })
            
            # Sort drafts by timestamp (newest first)
            drafts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return drafts

def get_draft(user_id, draft_id):
    """
    Get a specific draft for a user
    
    Args:
        user_id (str): User ID
        draft_id (str): Draft ID
        
    Returns:
        dict: Draft data or None if not found
    """
    if not user_id:
        user_id = "anonymous"
    
    if redis_client:
        try:
            # Get the draft from Redis
            user_drafts_key = f"html5_drafts:{user_id}"
            draft_data_str = redis_client.hget(user_drafts_key, draft_id)
            
            if draft_data_str:
                return json.loads(draft_data_str)
            return None
        except Exception as e:
            print(f"Error getting draft from Redis: {str(e)}. Falling back to memory.")
            
            # Fallback to memory
            if user_id in DRAFTS_MEMORY and draft_id in DRAFTS_MEMORY[user_id]:
                return DRAFTS_MEMORY[user_id][draft_id]
            return None
    else:
        # Direct memory retrieval
        if user_id in DRAFTS_MEMORY and draft_id in DRAFTS_MEMORY[user_id]:
            return DRAFTS_MEMORY[user_id][draft_id]
        return None

def delete_draft(user_id, draft_id):
    """
    Delete a specific draft for a user
    
    Args:
        user_id (str): User ID
        draft_id (str): Draft ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not user_id:
        user_id = "anonymous"
    
    if redis_client:
        try:
            # Delete the draft from Redis
            user_drafts_key = f"html5_drafts:{user_id}"
            result = redis_client.hdel(user_drafts_key, draft_id)
            
            return result > 0
        except Exception as e:
            print(f"Error deleting draft from Redis: {str(e)}. Falling back to memory.")
            
            # Fallback to memory
            if user_id in DRAFTS_MEMORY and draft_id in DRAFTS_MEMORY[user_id]:
                del DRAFTS_MEMORY[user_id][draft_id]
                return True
            return False
    else:
        # Direct memory deletion
        if user_id in DRAFTS_MEMORY and draft_id in DRAFTS_MEMORY[user_id]:
            del DRAFTS_MEMORY[user_id][draft_id]
            return True
        return False

def delete_all_drafts(user_id):
    """
    Delete all drafts for a user
    
    Args:
        user_id (str): User ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not user_id:
        user_id = "anonymous"
    
    if redis_client:
        try:
            # Delete all drafts from Redis
            user_drafts_key = f"html5_drafts:{user_id}"
            # Get all draft IDs first
            draft_ids = redis_client.hkeys(user_drafts_key)
            
            if draft_ids:
                # Delete each draft individually
                for draft_id in draft_ids:
                    redis_client.hdel(user_drafts_key, draft_id)
                
                print(f"Deleted all {len(draft_ids)} drafts for user {user_id}")
                return True
            return False
        except Exception as e:
            print(f"Error deleting all drafts from Redis: {str(e)}. Falling back to memory.")
            
            # Fallback to memory
            if user_id in DRAFTS_MEMORY:
                DRAFTS_MEMORY[user_id] = {}
                return True
            return False
    else:
        # Direct memory deletion
        if user_id in DRAFTS_MEMORY:
            DRAFTS_MEMORY[user_id] = {}
            return True
        return False

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
        
        # Pre-process code to handle section headers
        # This helps with AI responses that include markdown headers like "## HTML", "## CSS", "## JavaScript"
        processed_code = code
        
        # Look for section patterns and add appropriate tags if missing
        html_section = re.search(r'## HTML\s*(```(?:html)?\s*(.*?)\s*```)', processed_code, re.DOTALL)
        if html_section and '<body>' not in html_section.group(1):
            # If we find an HTML section without body tags, wrap it
            html_content = html_section.group(2).strip()
            wrapped_html = f"<body>\n{html_content}\n</body>"
            processed_code = processed_code.replace(html_section.group(1), f"```html\n{wrapped_html}\n```")
            print("Pre-processed HTML section to add body tags")
            
        css_section = re.search(r'## CSS\s*(```(?:css)?\s*(.*?)\s*```)', processed_code, re.DOTALL)
        if css_section and '<style>' not in css_section.group(1):
            # If we find a CSS section without style tags, wrap it
            css_content = css_section.group(2).strip()
            wrapped_css = f"<style>\n{css_content}\n</style>"
            processed_code = processed_code.replace(css_section.group(1), f"```css\n{wrapped_css}\n```")
            print("Pre-processed CSS section to add style tags")
            
        js_section = re.search(r'## JavaScript\s*(```(?:javascript|js)?\s*(.*?)\s*```)', processed_code, re.DOTALL)
        if js_section and '<script>' not in js_section.group(1):
            # If we find a JavaScript section without script tags, wrap it
            js_content = js_section.group(2).strip()
            wrapped_js = f"<script>\n{js_content}\n</script>"
            processed_code = processed_code.replace(js_section.group(1), f"```javascript\n{wrapped_js}\n```")
            print("Pre-processed JavaScript section to add script tags")
        
        # Split the code into components
        html = ""
        css = ""
        js = ""
        
        # Primary extraction method: look for proper HTML tags
        html_match = re.search(r'<body>(.*?)</body>', processed_code, re.DOTALL)
        if html_match:
            html = html_match.group(1).strip()
            print(f"Extracted HTML using <body> tags: {len(html)} chars")
        
        css_match = re.search(r'<style>(.*?)</style>', processed_code, re.DOTALL)
        if css_match:
            css = css_match.group(1).strip()
            print(f"Extracted CSS using <style> tags: {len(css)} chars")
        
        # Improved script tag extraction - more permissive with whitespace and attributes
        js_match = re.search(r'<script[^>]*>(.*?)</script>', processed_code, re.DOTALL)
        if js_match:
            js = js_match.group(1).strip()
            print(f"Extracted JS using <script> tags: {len(js)} chars")
        else:
            print("No JS found using <script> tags pattern")
            # For debugging, let's look for script tags in the original code
            script_tags = re.findall(r'<script[^>]*>.*?</script>', processed_code, re.DOTALL)
            if script_tags:
                print(f"Found {len(script_tags)} script tags, but couldn't extract content")
                for i, tag in enumerate(script_tags[:2]):  # Show first two for debugging
                    print(f"Script tag {i+1} preview: {tag[:100]}...")
            else:
                print("No script tags found in the content")
        
        # Fallback extraction: look for code blocks
        if not html:
            html_block = re.search(r'```html\s*(.*?)\s*```', processed_code, re.DOTALL)
            if html_block:
                html = html_block.group(1).strip()
                print(f"Extracted HTML from code block: {len(html)} chars")
        
        if not css:
            css_block = re.search(r'```css\s*(.*?)\s*```', processed_code, re.DOTALL)
            if css_block:
                css = css_block.group(1).strip()
                print(f"Extracted CSS from code block: {len(css)} chars")
        
        if not js:
            # Try multiple JavaScript code block patterns
            js_block = re.search(r'```javascript\s*(.*?)\s*```', processed_code, re.DOTALL) or re.search(r'```js\s*(.*?)\s*```', processed_code, re.DOTALL)
            if js_block:
                js = js_block.group(1).strip()
                print(f"Extracted JS from code block: {len(js)} chars")
        
        # Additional fallback for JavaScript extraction
        if not js:
            # Look for JavaScript without script tags in code blocks
            js_section = re.search(r'## JavaScript\s*```(?:javascript|js)?\s*(.*?)\s*```', processed_code, re.DOTALL)
            if js_section:
                js = js_section.group(1).strip()
                print(f"Extracted JS from markdown section: {len(js)} chars")
        
        # Last resort: Look for JavaScript patterns without any tags
        if not js:
            # Look for code that contains common JS patterns
            js_patterns = [
                r'document\.addEventListener\([\'"]DOMContentLoaded[\'"],\s*function',  # DOMContentLoaded
                r'function\s+\w+\s*\([^)]*\)\s*\{',  # function declarations
                r'const\s+\w+\s*=',  # const declarations
                r'let\s+\w+\s*=',  # let declarations
                r'var\s+\w+\s*=',  # var declarations
                r'document\.getElementById\(',  # DOM manipulation
                r'addEventListener\([\'"]click[\'"]',  # event listeners
                r'new\s+Chart\(',  # Chart.js initialization
                r'setInterval\(',  # timers
                r'fetch\(',  # fetch API
            ]
            
            # Check if the code contains multiple JS patterns
            js_pattern_count = 0
            for pattern in js_patterns:
                if re.search(pattern, processed_code, re.DOTALL):
                    js_pattern_count += 1
            
            # If we find multiple JS patterns, extract what seems to be JS code
            if js_pattern_count >= 2:
                # Look for what appears to be a JavaScript block without tags
                js_block_candidates = re.findall(r'```(?:javascript|js)?\s*(.*?)\s*```', processed_code, re.DOTALL)
                for candidate in js_block_candidates:
                    # Skip if it's clearly HTML or CSS
                    if '<html' in candidate or '<style' in candidate or '<body' in candidate:
                        continue
                    
                    # Count JS patterns in this candidate
                    candidate_js_count = sum(1 for pattern in js_patterns if re.search(pattern, candidate, re.DOTALL))
                    
                    if candidate_js_count >= 2:
                        js = candidate.strip()
                        print(f"Extracted JS using pattern matching: {len(js)} chars (matched {candidate_js_count} patterns)")
                        break
        
        # If still empty, try looser pattern matching for HTML content
        if not html and not css and not js:
            print("No components extracted. Trying alternative extraction methods.")
            # Look for HTML patterns (elements, tags, etc.)
            if '<div' in processed_code or '<p>' in processed_code or '<h1>' in processed_code:
                # Try to extract an HTML chunk
                html_chunk = re.search(r'(<div.*?>.*?</div>|<h1>.*?</h1>|<p>.*?</p>)', processed_code, re.DOTALL)
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
        Create a ZIP file with separate files for HTML, CSS, and JavaScript
        
        Args:
            html (str): HTML content
            css (str): CSS content
            js (str): JavaScript content
            
        Returns:
            bytes: The ZIP file content as bytes
        """
    # Create a complete HTML document that references external CSS and JS files
    html_content = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HTML5 Interactive Content</title>
        <link rel="stylesheet" href="styles.css">
    </head>
    <body>
    {html}
        <script src="script.js"></script>
    </body>
    </html>"""

    # Create the ZIP file in memory
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add separate files to the ZIP
        zip_file.writestr('index.html', html_content)
        zip_file.writestr('styles.css', css)
        zip_file.writestr('script.js', js)
        
        # Add a README.txt file with information
        readme_content = """HTML5 Interactive Content for SLS

        This ZIP file contains HTML5 interactive content with:
        1. index.html - The main HTML document
        2. styles.css - CSS styles
        3. script.js - JavaScript code for interactivity
        
        This content:
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
        
        # Get user ID for storage
        user_id = req.session.get('auth', 'anonymous')
        
        # Initialize simplified storage if needed
        if user_id not in GLOBAL_CODE_STORAGE:
            GLOBAL_CODE_STORAGE[user_id] = {}
            print(f"Initialized empty storage for user {user_id}")
        
        # Debug print storage state
        print("\n----- MENU D DEBUG -----")
        print(f"Session keys: {list(req.session.keys())}")
        if user_id in GLOBAL_CODE_STORAGE:
            has_current = 'current' in GLOBAL_CODE_STORAGE[user_id]
            has_previous = 'previous' in GLOBAL_CODE_STORAGE[user_id]
            print(f"Storage state: has_current={has_current}, has_previous={has_previous}")
        
        return Titled("",
            Link(rel="stylesheet", href="static/css/styles.css"),
            create_html5_form(api_key)
        )

    @rt('/api/html5/preview')
    async def post(req):
        """Generate an interactive preview using the code from the editors"""
        try:
            # Get user ID for storage
            user_id = req.session.get('auth', 'anonymous')
            
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
            
            # Check if we need to save the previous state
            if user_id in GLOBAL_CODE_STORAGE and 'current' in GLOBAL_CODE_STORAGE[user_id]:
                # Only save previous if content actually changed
                current = GLOBAL_CODE_STORAGE[user_id]['current']
                current_html = current.get('html', '')
                current_css = current.get('css', '')
                current_js = current.get('js', '')
                
                # Check if content has changed before saving
                if (html != current_html or css != current_css or js != current_js):
                    print(f"\n----- PREVIEW SAVING PREVIOUS STATE -----")
                    print(f"Saving previous content for user {user_id}")
                    print(f"Current content being saved as previous - HTML: {len(current_html)}, CSS: {len(current_css)}, JS: {len(current_js)}")
                    GLOBAL_CODE_STORAGE[user_id]['previous'] = dict(GLOBAL_CODE_STORAGE[user_id]['current'])
                else:
                    print(f"Content unchanged, not updating previous state")
            
            # Initialize user storage if not exists
            if user_id not in GLOBAL_CODE_STORAGE:
                GLOBAL_CODE_STORAGE[user_id] = {}
            
            # Update current state
            GLOBAL_CODE_STORAGE[user_id]['current'] = {
                'html': html,
                'css': css,
                'js': js
            }
            
            # Save to session as well for compatibility
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
                /* Reset some basic elements */
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    min-height: 100vh;
                }}
                /* Default container for content */
                #content-container {{
                    padding: 20px;
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
                style="background-color: white; display: block;"
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
        
        # Clear simplified storage for this user
        if user_id in GLOBAL_CODE_STORAGE:
            del GLOBAL_CODE_STORAGE[user_id]
            print(f"Cleared global code storage for user {user_id}")
            
        # Refinement history feature removed – no action required
        
        # Clear old history for backward compatibility
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
            var zipButton = document.getElementById('create-zip-button');
            // Previous interactive button removed
            
            if (runButton) runButton.classList.add('hidden');
            if (clearButton) clearButton.classList.add('hidden');
            if (zipButton) zipButton.classList.add('hidden');
            
            // Clear HTML5 Prompt text area directly
            var promptTextarea = document.getElementById('prompt');
            if (promptTextarea) {
                promptTextarea.value = '';
            }
            
            // Clear refinement prompt too if it exists
            var refinementTextarea = document.getElementById('refinement_prompt');
            if (refinementTextarea) {
                refinementTextarea.value = '';
            }
            
            // Refresh any iterative badges (but don't change the toggle state)
            if (typeof updateIterativeBadge === 'function') {
                updateIterativeBadge();
            }
        </script>
        """
        
        return NotStr(clean_preview_html)

    @rt('/api/html5/load-previous')
    async def post(req):
        """Load the previous interactive content from global storage"""
        # Get user ID from session for storage
        user_id = req.session.get('auth', 'anonymous')
        
        print(f"\n----- LOAD PREVIOUS DEBUG -----")
        print(f"Loading previous content for user {user_id}")
        
        # Debug global storage state
        if user_id in GLOBAL_CODE_STORAGE:
            print(f"GLOBAL_CODE_STORAGE keys for user {user_id}: {GLOBAL_CODE_STORAGE[user_id].keys()}")
            if 'current' in GLOBAL_CODE_STORAGE[user_id]:
                current = GLOBAL_CODE_STORAGE[user_id]['current']
                print(f"Current content sizes - HTML: {len(current.get('html', ''))}, CSS: {len(current.get('css', ''))}, JS: {len(current.get('js', ''))}")
            if 'previous' in GLOBAL_CODE_STORAGE[user_id]:
                previous = GLOBAL_CODE_STORAGE[user_id]['previous']
                print(f"Previous content sizes - HTML: {len(previous.get('html', ''))}, CSS: {len(previous.get('css', ''))}, JS: {len(previous.get('js', ''))}")
                # Debug first 100 chars of each component
                print(f"Previous HTML preview: {previous.get('html', '')[:100]}...")
                print(f"Previous CSS preview: {previous.get('css', '')[:100]}...")
                print(f"Previous JS preview: {previous.get('js', '')[:100]}...")
        else:
            print(f"No storage found for user {user_id}")
        
        # Check if user has previous content
        if user_id in GLOBAL_CODE_STORAGE and 'previous' in GLOBAL_CODE_STORAGE[user_id]:
            # Get previous content
            previous = GLOBAL_CODE_STORAGE[user_id]['previous']
            html = previous.get('html', '')
            css = previous.get('css', '')
            js = previous.get('js', '')
            
            # Check if previous content is different from current content
            is_different = True
            if 'current' in GLOBAL_CODE_STORAGE[user_id]:
                current = GLOBAL_CODE_STORAGE[user_id]['current']
                current_html = current.get('html', '')
                current_css = current.get('css', '')
                current_js = current.get('js', '')
                
                if html == current_html and css == current_css and js == current_js:
                    is_different = False
                    print("Previous content is identical to current content")
            
            if not is_different:
                return Div(
                    Div(
                        Svg(
                            Path(d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z", fill="currentColor"),
                            viewBox="0 0 24 24", 
                            width="24", 
                            height="24",
                            cls="inline-block mr-2"
                        ),
                        Span("No different previous version available", cls="align-middle"),
                        cls="flex items-center"
                    ),
                    P("The previous version is identical to your current version. Make changes to create a new version.", cls="mt-2 text-sm"),
                    cls="bg-amber-900 text-amber-100 p-4 rounded mb-4 border border-amber-700"
                )
            
            print(f"Previous content found - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
            
            # Update session data
            req.session['html'] = html
            req.session['css'] = css
            req.session['js'] = js
            
            # Create code editors with previous content
            return [
                Div(
                    "Loaded Previous Interactive Content",
                    cls="bg-blue-900 text-blue-100 p-2 rounded mb-4"
                ),
                create_code_editors(html, css, js),
                NotStr(f"""
                <script>
                    // Show buttons
                    const runButton = document.getElementById('run-preview-button');
                    const clearButton = document.getElementById('clear-button');
                    const zipButton = document.getElementById('create-zip-button');
                    // Previous interactive button removed
                    
                    if (runButton) runButton.classList.remove('hidden');
                    if (clearButton) clearButton.classList.remove('hidden');
                    if (zipButton) zipButton.classList.remove('hidden');
                    
                    // Auto-trigger preview
                    setTimeout(function() {{
                        if (runButton) {{
                            runButton.click();
                        }}
                    }}, 300);
                </script>
                """)
            ]
        else:
            # No previous content found
            print(f"No previous content found for user {user_id}")
            return Div(
                Div(
                    Svg(
                        Path(d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z", fill="currentColor"),
                        viewBox="0 0 24 24", 
                        width="24", 
                        height="24",
                        cls="inline-block mr-2"
                    ),
                    Span("No previous interactive content available", cls="align-middle"),
                    cls="flex items-center"
                ),
                P("You need to create at least two versions before using this feature.", cls="mt-2 text-sm"),
                cls="bg-amber-900 text-amber-100 p-4 rounded mb-4 border border-amber-700"
            )

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
            /* Reset some basic elements */
            body {{
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                min-height: 100vh;
            }}
            /* Default container for content */
            #content-container {{
                padding: 20px;
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
        
        return HTMLResponse(preview_html, media_type="text/html")

    @rt('/api/html5/create-zip')
    async def post(req):
        """Create a downloadable ZIP file with index.html for SLS"""
        try:
            # Get user ID from session
            user_id = req.session.get('auth', 'anonymous')
            
            # Get form data
            form = await req.form()
            html = form.get('html-editor', '')
            css = form.get('css-editor', '')
            js = form.get('js-editor', '')
            
            # When creating a ZIP, delete all drafts
            delete_all_drafts(user_id)
            print(f"Deleted all drafts for user {user_id} after ZIP creation")
            
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
                <h4 class="text-lg font-bold text-gray-400 mb-2">SLS Package Ready!</h4>
                <p class="text-sm mb-2 text-gray-400" style="color: #4b5563 !important;">Your HTML5 content has been packaged into a ZIP file ready for SLS.</p>
                <a href="data:application/zip;base64,{encoded_zip}" 
                download="{filename}" 
                type="application/zip"
                class="inline-block bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded flex items-center w-fit download-link">
                    <svg viewBox="0 0 24 24" width="20" height="20" class="mr-2">
                        <path d="M19 9h-4V3H9v6H5l7 7 7-7zm-8 2V5h2v6h1.17L12 13.17 9.83 11H11zm-6 7h14v2H5v-2z" fill="currentColor"></path>
                    </svg>
                    <span class="text-gray-200" style="color: #4b5563 !important;">Download ZIP</span>
                </a>
                <p class="text-xs text-gray-400 mt-2" style="color: #4b5563 !important;">Upload this ZIP directly to SLS as a media object.</p>
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
        """Generate HTML5 interactive code based on prompt and reference images"""
        try:
            # Get user ID from session for storage
            user_id = req.session.get('auth', 'anonymous')
            
            # Delete all drafts when generating new code
            delete_all_drafts(user_id)
            print(f"Deleted all drafts for user {user_id} before new generation")
            
            # Clear any existing refinement history
            if user_id in GLOBAL_CODE_STORAGE:
                del GLOBAL_CODE_STORAGE[user_id]
                print(f"Cleared refinement history for user {user_id} before new generation")
                
            # Get current state from session or global storage
            current_html = req.session.get('html', '')
            current_css = req.session.get('css', '')
            current_js = req.session.get('js', '')
            
            if not (current_html or current_css or current_js) and user_id in GLOBAL_CODE_STORAGE and 'current' in GLOBAL_CODE_STORAGE[user_id]:
                # Get current state from global storage if session is empty
                current_html = GLOBAL_CODE_STORAGE[user_id]['current']['html']
                current_css = GLOBAL_CODE_STORAGE[user_id]['current']['css']
                current_js = GLOBAL_CODE_STORAGE[user_id]['current']['js']
                print("Retrieved current state from global storage")
            
            print("\n----- GENERATION DEBUG -----")
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
            
            # If we have valid current state, save it before generating new code
            if current_html or current_css or current_js:
                # Initialize storage for this user if needed
                if user_id not in GLOBAL_CODE_STORAGE:
                    GLOBAL_CODE_STORAGE[user_id] = {}
                
                # Check if we have a current state to move to previous
                if 'current' in GLOBAL_CODE_STORAGE[user_id]:
                    # Save current state as previous before updating
                    print(f"\n----- GENERATE SAVING PREVIOUS STATE -----")
                    print(f"Saving previous content for user {user_id}")
                    current = GLOBAL_CODE_STORAGE[user_id]['current']
                    GLOBAL_CODE_STORAGE[user_id]['previous'] = dict(current)
                    print("Saved current state as previous")
            
            # Get the prompt and model from the form
            prompt = form.get('prompt', '')
            model = form.get('model', 'gpt-4o')
            is_iterative = form.get('iterative-toggle') == 'on'
            
            # Get reference images - modified to handle prefixed fields
            images = []
            # First look for generation tab images
            for i in range(5):
                image_data = form.get(f"gen-image-data-{i}")
                if image_data:
                    images.append(image_data)
                
            # If no images found, try without prefix (backward compatibility)
            if not images:
                for i in range(5):
                    image_data = form.get(f"image-data-{i}")
                    if image_data:
                        images.append(image_data)
            
            # Generate new code
            try:
                html, css, js = await generate_html5_code(prompt, images, model, is_iterative, current_html, current_css, current_js, user_id=user_id, session_id=req.session.session_id if hasattr(req.session, 'session_id') else None)
                print(f"Successfully generated code - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
                
                # If in iterative mode and no content was returned, return an error
                if is_iterative and not (html or css or js):
                    raise ValueError("No content was generated in iterative mode. Please try again with different instructions.")
                
                # Store the new state in session
                req.session['html'] = html
                req.session['css'] = css
                req.session['js'] = js
                
                # Store the new state in global storage
                if user_id not in GLOBAL_CODE_STORAGE:
                    GLOBAL_CODE_STORAGE[user_id] = {}
                
                # Store new code as current state
                GLOBAL_CODE_STORAGE[user_id]['current'] = {
                    'html': html,
                    'css': css,
                    'js': js
                }
                
                print("Stored new generated code in global storage and session")
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
                    
                # OpenAI API error fallback, suggest alternative model
                if model.startswith("gpt") and "rate_limit" in str(e).lower():
                    return Div(
                        Div(f"OpenAI API Rate Limit Error: {str(e)}", cls="text-lg mb-2"),
                        P("The OpenAI API is rate-limited. Try with Claude or try again later.", cls="mb-3"),
                        Div(
                            Button(
                                "Try with Claude 3.5 Haiku",
                                cls="px-4 py-2 bg-blue-500 text-white rounded mr-2",
                                hx_post="/api/html5/generate-code",
                                hx_include="closest form",
                                hx_vals='{"model": "claude-3-5-haiku-20241022"}',
                                hx_target="#code-editors-container",
                                hx_indicator="#loading-indicator"
                            ),
                            Button(
                                "Try Again",
                                cls="px-4 py-2 bg-green-500 text-white rounded",
                                hx_post="/api/html5/generate-code",
                                hx_include="closest form",
                                hx_target="#code-editors-container",
                                hx_indicator="#loading-indicator"
                            ),
                            cls="mt-2"
                        ),
                        cls="error alert alert-danger p-4"
                    )
                
                # General error message
                return Div(
                    Div(f"Error: {str(e)}", cls="text-lg mb-2"),
                    P("Please try again with different instructions or a different model", cls="mb-3"),
                    Div(
                        Button(
                            "Try with Claude 3.7 Sonnet",
                            cls="px-4 py-2 bg-purple-500 text-white rounded mr-2",
                            hx_post="/api/html5/generate-code",
                            hx_include="closest form",
                            hx_vals='{"model": "claude-3-7-sonnet-20250219"}',
                            hx_target="#code-editors-container",
                            hx_indicator="#loading-indicator"
                        ),
                        Button(
                            "Try with GPT-4o",
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

            # Create preview content
            preview_content = f"""<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                /* Reset some basic elements */
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    min-height: 100vh;
                }}
                /* Default container for content */
                #content-container {{
                    padding: 20px;
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
                    // Add a create ZIP button after generation
                    const dynamicButtonsContainer = document.getElementById('dynamic-buttons');
                    if (dynamicButtonsContainer) {{
                        // Create a ZIP button
                        const zipButton = document.createElement('button');
                        zipButton.id = 'create-zip-button';
                        zipButton.innerHTML = `
                            <div class="flex items-center justify-center w-full">
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                                    <path d="M20 6h-3V4c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-5-2v2H9V4h6zM4 8h16v3H4V8zm0 11v-6h16v6H4z"/>
                                </svg>
                                <span class="ml-2">Create ZIP</span>
                            </div>`;
                        zipButton.className = 'action-button bg-gradient-to-r from-indigo-600 to-indigo-500';
                        // Add explicit onclick handler to call createZipPackage function directly
                        zipButton.onclick = function(e) {{
                            e.preventDefault();
                            console.log("ZIP button clicked with direct onclick handler");
                            createZipPackage();
                            return false;
                        }};
                        dynamicButtonsContainer.appendChild(zipButton);
                    }}
                </script>
                """),
                NotStr(f"""
                <script>
                    // Add data URL to iframe src
                    window.setTimeout(function() {{
                        const iframe = document.createElement('iframe');
                        iframe.src = "data:text/html;base64,{encoded_content}";
                        iframe.style.width = '100%';
                        iframe.style.height = '100%';
                        iframe.style.border = 'none';
                        
                        const container = document.getElementById('preview-container');
                        if (container) {{
                            container.innerHTML = '';
                            container.appendChild(iframe);
                        }}
                    }}, 300);
                </script>
                """)
            ]
                
        except Exception as e:
            print(f"Error in generate-code route: {str(e)}")
            import traceback
            traceback.print_exc()
            return Div(
                f"Error: {str(e)}",
                cls="error alert alert-danger p-4"
            )
            
    @rt('/api/html5/refine-code')
    async def post(req):
        """Refine existing HTML5 code based on reference images and refinement instructions"""
        try:
            # Get user ID from session for storage
            user_id = req.session.get('auth', 'anonymous')
            
            # Get form data for refinement
            form = await req.form()
            
            # Get current HTML/CSS/JS for refinement
            # First try to get from form (in case it was explicitly provided)
            current_html = form.get('current_html', '')
            current_css = form.get('current_css', '')
            current_js = form.get('current_js', '')
            
            # If not provided in form, try to get from global storage
            if not (current_html or current_css or current_js):
                if user_id in GLOBAL_CODE_STORAGE and 'current' in GLOBAL_CODE_STORAGE[user_id]:
                    current_html = GLOBAL_CODE_STORAGE[user_id]['current']['html']
                    current_css = GLOBAL_CODE_STORAGE[user_id]['current']['css']
                    current_js = GLOBAL_CODE_STORAGE[user_id]['current']['js']
                    print("Got current code from global storage")
                else:
                    # As a last resort, try to get from session
                    current_html = req.session.get('html', '')
                    current_css = req.session.get('css', '')
                    current_js = req.session.get('js', '')
                    print("Got current code from session")
            
            print(f"Current code lengths - HTML: {len(current_html)}, CSS: {len(current_css)}, JS: {len(current_js)}")
            
            if current_html or current_css or current_js:
                # Before refining, save current content as a draft
                draft_id, error = save_draft(user_id, current_html, current_css, current_js)
                
                if error:
                    print(f"Warning: Could not save draft: {error}")
                else:
                    print(f"Saved draft {draft_id} for user {user_id} before refinement")
            
            # Store current code as previous before refinement
            if current_html or current_css or current_js:
                # Initialize storage for this user if needed
                if user_id not in GLOBAL_CODE_STORAGE:
                    GLOBAL_CODE_STORAGE[user_id] = {}
                
                # Save current state as previous before updating
                if 'current' in GLOBAL_CODE_STORAGE[user_id]:
                    print(f"\n----- REFINE SAVING PREVIOUS STATE -----")
                    print(f"Saving previous content for user {user_id}")
                    current = GLOBAL_CODE_STORAGE[user_id]['current']
                    GLOBAL_CODE_STORAGE[user_id]['previous'] = dict(current)
                    print("Saved current state as previous before refinement")
                
                # Update current state (will be replaced after refinement)
                GLOBAL_CODE_STORAGE[user_id]['current'] = {
                    'html': current_html,
                    'css': current_css,
                    'js': current_js
                }
            else:
                print("No current code to refine")
                return Div(
                    "Error: No code to refine. Please generate code first.",
                    cls="error alert alert-danger p-4"
                )
            
            # Get refinement instructions and model
            prompt = form.get('prompt', '')
            model = form.get('model', 'gpt-4o')
            
            # Refinement history feature removed – do not store prompts
            
            # For refinement, always use iterative mode
            is_iterative = True
            
            # Get reference images - use iteration tab prefixes
            images = []
            for i in range(5):
                image_data = form.get(f"iter-image-data-{i}")
                if image_data:
                    images.append(image_data)
                
            # If no images found, try without prefix (backward compatibility)
            if not images:
                for i in range(5):
                    image_data = form.get(f"image-data-{i}")
                    if image_data:
                        images.append(image_data)
            
            # Generate refined code
            try:
                html, css, js = await generate_html5_code(prompt, images, model, is_iterative, current_html, current_css, current_js, user_id=user_id, session_id=req.session.session_id if hasattr(req.session, 'session_id') else None)
                print(f"Successfully refined code - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
                
                # If no content was returned, return an error
                if not (html or css or js):
                    raise ValueError("No content was generated from refinement. Please try again with different instructions.")
                
                # Store the refined code in session
                req.session['html'] = html
                req.session['css'] = css
                req.session['js'] = js
                
                # Store the refined code in global storage
                if user_id not in GLOBAL_CODE_STORAGE:
                    GLOBAL_CODE_STORAGE[user_id] = {}
                
                # Store refined code as current state
                GLOBAL_CODE_STORAGE[user_id]['current'] = {
                    'html': html,
                    'css': css,
                    'js': js
                }
                
                print("Stored refined code in global storage and session")
                
                # Create preview content with the refined code
                preview_content = f"""<!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                    /* Reset some basic elements */
                    body {{
                        margin: 0;
                        padding: 0;
                        font-family: Arial, sans-serif;
                        min-height: 100vh;
                    }}
                    /* Default container for content */
                    #content-container {{
                        padding: 20px;
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
                encoded_content = base64.b64encode(preview_content.encode('utf-8')).decode('utf-8')
                
                # Create code editors with the new code
                return [
                    Div(
                        "Code Successfully Refined",
                        cls="bg-green-900 text-green-100 p-2 rounded mb-4"
                    ),
                    create_code_editors(html, css, js),
                    NotStr(f"""
                    <script>
                        // Add a create ZIP button after refinement
                        const dynamicButtonsContainer = document.getElementById('dynamic-buttons');
                        if (dynamicButtonsContainer) {{
                            // Create a ZIP button
                            const zipButton = document.createElement('button');
                            zipButton.id = 'create-zip-button';
                            zipButton.innerHTML = `
                                <div class="flex items-center justify-center w-full">
                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                                        <path d="M20 6h-3V4c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-5-2v2H9V4h6zM4 8h16v3H4V8zm0 11v-6h16v6H4z"/>
                                    </svg>
                                    <span class="ml-2">Create ZIP</span>
                                </div>`;
                            zipButton.className = 'action-button bg-gradient-to-r from-indigo-600 to-indigo-500';
                            // Add explicit onclick handler to call createZipPackage function directly
                            zipButton.onclick = function(e) {{
                                e.preventDefault();
                                console.log("ZIP button clicked with direct onclick handler");
                                createZipPackage();
                                return false;
                            }};
                            dynamicButtonsContainer.appendChild(zipButton);
                        }}
                    </script>
                    """),
                    NotStr(f"""
                    <script>
                        // Add data URL to iframe src
                        window.setTimeout(function() {{
                            const iframe = document.createElement('iframe');
                            iframe.src = "data:text/html;base64,{encoded_content}";
                            iframe.style.width = '100%';
                            iframe.style.height = '100%';
                            iframe.style.border = 'none';
                            
                            const container = document.getElementById('preview-container');
                            if (container) {{
                                container.innerHTML = '';
                                container.appendChild(iframe);
                            }}
                        }}, 300);
                    </script>
                    """)
                ]
            except Exception as e:
                print(f"Error refining code: {str(e)}")
                import traceback
                error_details = traceback.format_exc()
                print(f"Error details: {error_details}")
                
                # Return the original content with an error message
                return [
                    Div(f"Error: {str(e)} - Using your existing code", cls="bg-red-800 text-white p-2 mb-4 rounded"),
                    create_code_editors(current_html, current_css, current_js),
                    NotStr(f"""
                    <script>
                        console.error("Error in code refinement: {str(e)}");
                    </script>
                    """)
                ]
                
        except Exception as e:
            print(f"Error in refine-code route: {str(e)}")
            import traceback
            traceback.print_exc()
            return Div(
                f"Error: {str(e)}",
                cls="error alert alert-danger p-4"
            )

    @rt('/api/html5/upload-zip')
    async def post(req):
        """Upload a ZIP file and extract HTML, CSS, and JS"""
        try:
            # Get user ID from session for storage
            user_id = req.session.get('auth', 'anonymous')
            
            # Clear any existing refinement history
            if user_id in GLOBAL_CODE_STORAGE:
                del GLOBAL_CODE_STORAGE[user_id]
                print(f"Cleared refinement history for user {user_id} after ZIP upload")
                
            print(f"\n----- UPLOAD ZIP DEBUG -----")
            print(f"Processing ZIP upload for user {user_id}")
            
            # Get the form data
            form = await req.form()
            
            # Enhanced debugging of form data
            print(f"Form data keys: {list(form.keys())}")
            print(f"Form data types:")
            for key in form.keys():
                value = form.get(key)
                print(f"  Key: {key}, Type: {type(value)}, Value preview: {str(value)[:100] if isinstance(value, str) else 'non-string'}")
            
            # Get the uploaded file from form data
            upload_file = form.get('zipfile')
            if not upload_file:
                # If zipfile not found, try checking other keys
                print("No 'zipfile' key found, checking if other keys contain file data")
                for key in form.keys():
                    value = form.get(key)
                    if hasattr(value, 'filename') or isinstance(value, bytes):
                        print(f"Found potential file data in key: {key}")
                        upload_file = value
                        break
                
                if not upload_file:
                    return Div(
                        "Error: No file uploaded. Please select a ZIP file.",
                        cls="bg-red-800 text-white p-2 mb-4 rounded"
                    )
            
            # Debug the upload_file type
            print(f"Upload file type: {type(upload_file)}")
            
            # Debug more file info
            if hasattr(upload_file, 'filename'):
                print(f"File name: {upload_file.filename}")
            if hasattr(upload_file, 'content_type'):
                print(f"Content type: {upload_file.content_type}")
            
            # Check if we have actual form file data
            try:
                # Get the file content
                if isinstance(upload_file, bytes):
                    # Already bytes, use directly
                    content = upload_file
                    print(f"Using raw bytes: {len(content)} bytes")
                elif hasattr(upload_file, 'read'):
                    # File-like object with read method
                    content = await upload_file.read()
                    print(f"Read content using read() method: {len(content)} bytes")
                elif isinstance(upload_file, str):
                    if upload_file.startswith('data:'):
                        # Base64 data URL
                        try:
                            parts = upload_file.split(',', 1)
                            if len(parts) == 2 and ';base64,' in parts[0]:
                                content = base64.b64decode(parts[1])
                                print(f"Decoded base64 data: {len(content)} bytes")
                            else:
                                raise ValueError("Invalid data URL format")
                        except Exception as e:
                            print(f"Error decoding base64: {e}")
                            return Div(f"Error decoding base64 data: {str(e)}", cls="bg-red-800 text-white p-2 mb-4 rounded")
                    elif os.path.exists(upload_file):
                        # File path
                        with open(upload_file, 'rb') as f:
                            content = f.read()
                        print(f"Read from file path: {len(content)} bytes")
                    else:
                        # Try to encode the string as bytes
                        try:
                            # Try UTF-8 first
                            content = upload_file.encode('utf-8')
                            print(f"Encoded string as UTF-8: {len(content)} bytes")
                        except UnicodeError:
                            # Fall back to latin1 which can encode any string
                            content = upload_file.encode('latin1')
                            print(f"Encoded string as latin1: {len(content)} bytes")
                else:
                    print(f"Unsupported upload_file type: {type(upload_file)}")
                    return Div(f"Error: Unsupported file type. Expected file upload.", cls="bg-red-800 text-white p-2 mb-4 rounded")
                
                # Debug: dump first 100 bytes as hex for inspection
                print(f"First 100 bytes: {content[:100].hex()}")
                
                # Check if it's a valid ZIP file
                # Proper way to test if data is a valid ZIP file
                try:
                    # Create a BytesIO object from the content
                    content_stream = io.BytesIO(content)
                    
                    # Try to open it as a ZIP file
                    with zipfile.ZipFile(content_stream) as zf:
                        # List all files to verify it's valid
                        file_list = zf.namelist()
                        print(f"Valid ZIP file with {len(file_list)} files: {file_list[:10]}")
                except zipfile.BadZipFile as e:
                    print(f"Not a valid ZIP file: {e}")
                    return Div(
                        "Error: The uploaded file is not a valid ZIP file. Please upload a ZIP file containing HTML, CSS, and JS content.",
                        cls="bg-red-800 text-white p-2 mb-4 rounded"
                    )
                except Exception as e:
                    print(f"Error validating ZIP: {e}")
                    return Div(f"Error validating ZIP file: {str(e)}", cls="bg-red-800 text-white p-2 mb-4 rounded")
                
            except Exception as e:
                print(f"Error reading file: {e}")
                import traceback
                print(traceback.format_exc())
                return Div(f"Error reading uploaded file: {str(e)}", cls="bg-red-800 text-white p-2 mb-4 rounded")
            
            # Create a file-like object from the content
            zip_file = io.BytesIO(content)
            
            # Open the ZIP file
            html_content = ""
            css_content = ""
            js_content = ""
            html_content_raw = ""
            
            try:
                with zipfile.ZipFile(zip_file) as zf:
                    # List all files in the ZIP
                    file_list = zf.namelist()
                    print(f"Files in ZIP: {file_list}")
                    
                    # Filter files by extension
                    html_files = [f for f in file_list if f.lower().endswith(('.html', '.htm'))]
                    css_files = [f for f in file_list if f.lower().endswith('.css')]
                    js_files = [f for f in file_list if f.lower().endswith('.js')]
                    
                    print(f"Found files by type - HTML: {html_files}, CSS: {css_files}, JS: {js_files}")
                    
                    # Extract content from HTML file (prioritize index.html or similar)
                    priority_html_names = ['index.html', 'main.html', 'default.html', 'home.html']
                    html_file = None
                    
                    # First try priority files
                    for priority_name in priority_html_names:
                        if priority_name in html_files:
                            html_file = priority_name
                            print(f"Using priority HTML file: {html_file}")
                            break
                            
                    # If no priority file found, use the first HTML file
                    if not html_file and html_files:
                        html_file = html_files[0]
                        print(f"Using first available HTML file: {html_file}")
                    
                    if html_file:
                        try:
                            html_content_raw = zf.read(html_file).decode('utf-8')
                            print(f"Read HTML file: {html_file} ({len(html_content_raw)} bytes)")
                            
                            # Extract the body content from the HTML file
                            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content_raw, re.DOTALL | re.IGNORECASE)
                            if body_match:
                                html_content = body_match.group(1).strip()
                                print(f"Extracted body content: {len(html_content)} chars")
                            else:
                                # If no body tags, try a broader approach to extract the main content
                                # Look for a div with id="content" or similar
                                content_div_match = re.search(r'<div[^>]*id=["\'](content|main|container|app)["\'][^>]*>(.*?)</div>', 
                                                           html_content_raw, re.DOTALL | re.IGNORECASE)
                                if content_div_match:
                                    html_content = content_div_match.group(2).strip()
                                    print(f"Extracted content from main div: {len(html_content)} chars")
                                else:
                                    # If no specific content found, extract everything between <html> and </html>
                                    html_match = re.search(r'<html[^>]*>(.*?)</html>', html_content_raw, re.DOTALL | re.IGNORECASE)
                                    if html_match:
                                        # Remove <head> section if present
                                        html_content = re.sub(r'<head>.*?</head>', '', html_match.group(1), flags=re.DOTALL | re.IGNORECASE)
                                        # Remove any remaining script and style tags
                                        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                                        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
                                        html_content = html_content.strip()
                                        print(f"Extracted content from html tags: {len(html_content)} chars")
                                    else:
                                        # Last resort: use the whole content
                                        html_content = html_content_raw
                                        print(f"Using full HTML file content: {len(html_content)} chars")
                        except UnicodeDecodeError:
                            # Try different encodings if UTF-8 fails
                            for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
                                try:
                                    html_content_raw = zf.read(html_file).decode(encoding)
                                    # If successful, extract content as above
                                    body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content_raw, re.DOTALL | re.IGNORECASE)
                                    if body_match:
                                        html_content = body_match.group(1).strip()
                                    else:
                                        html_content = html_content_raw
                                    print(f"Decoded HTML using {encoding}: {len(html_content)} chars")
                                    break
                                except UnicodeDecodeError:
                                    continue
                    
                    # Extract content from CSS files (prioritize styles.css or similar)
                    priority_css_names = ['styles.css', 'style.css', 'main.css', 'default.css']
                    css_file = None
                    
                    # First try priority files
                    for priority_name in priority_css_names:
                        if priority_name in css_files:
                            css_file = priority_name
                            print(f"Using priority CSS file: {css_file}")
                            break
                            
                    # If no priority file found, use the first CSS file
                    if not css_file and css_files:
                        css_file = css_files[0]
                        print(f"Using first available CSS file: {css_file}")
                    
                    if css_file:
                        try:
                            css_content = zf.read(css_file).decode('utf-8')
                            print(f"Read CSS file: {css_file} ({len(css_content)} bytes)")
                        except UnicodeDecodeError:
                            # Try different encodings if UTF-8 fails
                            for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
                                try:
                                    css_content = zf.read(css_file).decode(encoding)
                                    print(f"Decoded CSS using {encoding}: {len(css_content)} chars")
                                    break
                                except UnicodeDecodeError:
                                    continue
                    
                    # Extract content from JS files (prioritize script.js or similar)
                    priority_js_names = ['script.js', 'main.js', 'index.js', 'app.js']
                    js_file = None
                    
                    # First try priority files
                    for priority_name in priority_js_names:
                        if priority_name in js_files:
                            js_file = priority_name
                            print(f"Using priority JS file: {js_file}")
                            break
                            
                    # If no priority file found, use the first JS file
                    if not js_file and js_files:
                        js_file = js_files[0]
                        print(f"Using first available JS file: {js_file}")
                    
                    if js_file:
                        try:
                            js_content = zf.read(js_file).decode('utf-8')
                            print(f"Read JS file: {js_file} ({len(js_content)} bytes)")
                        except UnicodeDecodeError:
                            # Try different encodings if UTF-8 fails
                            for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
                                try:
                                    js_content = zf.read(js_file).decode(encoding)
                                    print(f"Decoded JS using {encoding}: {len(js_content)} chars")
                                    break
                                except UnicodeDecodeError:
                                    continue
                    
                    # If we didn't find the files by name, try alternative approaches
                    # Check if CSS is embedded in HTML
                    if not css_content and html_content_raw:
                        style_tags = re.findall(r'<style[^>]*>(.*?)</style>', html_content_raw, re.DOTALL | re.IGNORECASE)
                        if style_tags:
                            css_content = '\n\n'.join(style_tags)
                            print(f"Extracted CSS from HTML style tags: {len(css_content)} chars")
                            
                    # Check if JS is embedded in HTML
                    if not js_content and html_content_raw:
                        script_tags = re.findall(r'<script[^>]*>(.*?)</script>', html_content_raw, re.DOTALL | re.IGNORECASE)
                        if script_tags:
                            # Filter out empty scripts and those with src attributes
                            valid_scripts = [script for script in script_tags 
                                            if script.strip() and not re.search(r'<script[^>]*src=', script)]
                            if valid_scripts:
                                js_content = '\n\n'.join(valid_scripts)
                                print(f"Extracted JS from HTML script tags: {len(js_content)} chars")
                                
                    # Check for CSS in external files referenced in HTML
                    if not css_content and html_content_raw:
                        link_tags = re.findall(r'<link[^>]*href=["\'](.*?)["\'][^>]*>', html_content_raw, re.IGNORECASE)
                        css_links = [link for link in link_tags if link.lower().endswith('.css')]
                        for css_link in css_links:
                            if css_link in file_list:
                                try:
                                    css_content = zf.read(css_link).decode('utf-8')
                                    print(f"Read CSS from linked file: {css_link} ({len(css_content)} bytes)")
                                    break
                                except Exception as e:
                                    print(f"Error reading linked CSS file {css_link}: {e}")
                                
                    # Check for JS in external files referenced in HTML
                    if not js_content and html_content_raw:
                        script_srcs = re.findall(r'<script[^>]*src=["\'](.*?)["\'][^>]*>', html_content_raw, re.IGNORECASE)
                        js_links = [src for src in script_srcs if src.lower().endswith('.js')]
                        for js_link in js_links:
                            if js_link in file_list:
                                try:
                                    js_content = zf.read(js_link).decode('utf-8')
                                    print(f"Read JS from script src: {js_link} ({len(js_content)} bytes)")
                                    break
                                except Exception as e:
                                    print(f"Error reading linked JS file {js_link}: {e}")
            except Exception as e:
                print(f"Error extracting ZIP contents: {e}")
                import traceback
                print(traceback.format_exc())
                return Div(
                    f"Error extracting ZIP contents: {str(e)}",
                    cls="bg-red-800 text-white p-2 mb-4 rounded"
                )
                
            # Check if we have HTML content after all extraction attempts
            if not html_content:
                return Div(
                    "Error: No HTML content could be extracted from the ZIP file. Please ensure your ZIP contains an HTML file with valid content.",
                    cls="bg-red-800 text-white p-2 mb-4 rounded"
                )
            
            # Store the extracted content
            # Check if we need to save the previous state
            if user_id in GLOBAL_CODE_STORAGE and 'current' in GLOBAL_CODE_STORAGE[user_id]:
                print(f"\n----- UPLOAD SAVING PREVIOUS STATE -----")
                print(f"Saving previous content for user {user_id}")
                current = GLOBAL_CODE_STORAGE[user_id]['current']
                GLOBAL_CODE_STORAGE[user_id]['previous'] = dict(current)
                print("Saved current state as previous")
            
            # Initialize user storage if needed
            if user_id not in GLOBAL_CODE_STORAGE:
                GLOBAL_CODE_STORAGE[user_id] = {}
            
            # Update current state with the extracted content
            GLOBAL_CODE_STORAGE[user_id]['current'] = {
                'html': html_content,
                'css': css_content,
                'js': js_content
            }
            
            # Save to session as well for compatibility
            req.session['html'] = html_content
            req.session['css'] = css_content
            req.session['js'] = js_content
            
            print(f"Stored extracted content in global storage and session")
            
            # Create a success message
            success_message = Div(
                "ZIP file successfully uploaded and content extracted",
                cls="bg-green-800 text-white p-2 mb-4 rounded"
            )
            
            # Return the success message and code editors with the extracted content
            return [
                success_message,
                create_code_editors(html_content, css_content, js_content),
                NotStr(f"""
                <script>
                    // Show buttons
                    const runButton = document.getElementById('run-preview-button');
                    const clearButton = document.getElementById('clear-button');
                    const zipButton = document.getElementById('create-zip-button');
                    
                    if (runButton) runButton.classList.remove('hidden');
                    if (clearButton) clearButton.classList.remove('hidden');
                    if (zipButton) zipButton.classList.remove('hidden');
                    
                    // Auto-trigger preview
                    setTimeout(function() {{
                        if (runButton) {{
                            runButton.click();
                        }}
                    }}, 300);
                </script>
                """)
            ]
            
        except Exception as e:
            print(f"Error in upload-zip route: {str(e)}")
            import traceback
            error_details = traceback.format_exc()
            print(f"Error details: {error_details}")
            
            return Div(
                f"Error processing ZIP file: {str(e)}",
                Pre(error_details, cls="text-xs mt-2"),
                cls="bg-red-800 text-white p-2 mb-4 rounded"
            )

    @rt('/api/html5/get-drafts')
    async def get(req):
        """Get all drafts for the current user"""
        # Get user ID from session
        user_id = req.session.get('auth', 'anonymous')
        
        # Get all drafts for this user
        drafts = get_all_drafts(user_id)
        
        # Return the drafts
        return JSONResponse({
            "success": True,
            "drafts": drafts
        })
    
    @rt('/api/html5/load-draft/{draft_id}')
    async def get(req):
        """Load a specific draft for the current user"""
        # Get user ID from session
        user_id = req.session.get('auth', 'anonymous')
        
        # Get the draft ID from the path
        draft_id = req.path_params.get("draft_id")
        
        if not draft_id:
            return JSONResponse({
                "success": False,
                "error": "No draft ID provided"
            }, status_code=400)
        
        # Get the draft
        draft = get_draft(user_id, draft_id)
        
        if not draft:
            return JSONResponse({
                "success": False,
                "error": "Draft not found"
            }, status_code=404)
        
        # Update session with draft content
        req.session['html'] = draft.get('html', '')
        req.session['css'] = draft.get('css', '')
        req.session['js'] = draft.get('js', '')
        
        # Update global storage
        if user_id not in GLOBAL_CODE_STORAGE:
            GLOBAL_CODE_STORAGE[user_id] = {}
        
        # Save current state as previous before updating with draft
        if 'current' in GLOBAL_CODE_STORAGE[user_id]:
            GLOBAL_CODE_STORAGE[user_id]['previous'] = dict(GLOBAL_CODE_STORAGE[user_id]['current'])
        
        # Update current state with draft content
        GLOBAL_CODE_STORAGE[user_id]['current'] = {
            'html': draft.get('html', ''),
            'css': draft.get('css', ''),
            'js': draft.get('js', '')
        }
        
        # Return the draft content
        return JSONResponse({
            "success": True,
            "html": draft.get('html', ''),
            "css": draft.get('css', ''),
            "js": draft.get('js', ''),
            "timestamp": draft.get('timestamp')
        })
    
    @rt('/api/html5/delete-draft/{draft_id}')
    async def delete(req):
        """Delete a specific draft for the current user"""
        # Get user ID from session
        user_id = req.session.get('auth', 'anonymous')
        
        # Get the draft ID from the path
        draft_id = req.path_params.get("draft_id")
        
        if not draft_id:
            return JSONResponse({
                "success": False,
                "error": "No draft ID provided"
            }, status_code=400)
        
        # Delete the draft
        success = delete_draft(user_id, draft_id)
        
        if not success:
            return JSONResponse({
                "success": False,
                "error": "Draft not found or could not be deleted"
            }, status_code=404)
        
        # Return success
        return JSONResponse({
            "success": True,
            "message": "Draft deleted successfully"
        })

    @rt('/api/html5/delete-draft-post/{draft_id}')
    async def post(req):
        """Delete a specific draft using POST method (alternative to DELETE)"""
        # Get user ID from session
        user_id = req.session.get('auth', 'anonymous')
        
        # Get the draft ID from the path
        draft_id = req.path_params.get("draft_id")
        
        if not draft_id:
            return JSONResponse({
                "success": False,
                "error": "No draft ID provided"
            }, status_code=400)
        
        # Delete the draft
        success = delete_draft(user_id, draft_id)
        
        if not success:
            return JSONResponse({
                "success": False,
                "error": "Draft not found or could not be deleted"
            }, status_code=404)
        
        # Return success
        return JSONResponse({
            "success": True,
            "message": "Draft deleted successfully"
        })

async def generate_html5_code(prompt, images, model, is_iterative, current_html, current_css, current_js, user_id="anonymous", session_id=None):
    """Generate HTML5 code using the specified model"""
    try:
        # Start timing the generation
        start_time = datetime.datetime.now()
        
        # Get API keys
        openai_key = os.environ["OPENAI_API_KEY"]
        anthropic_key = os.environ["ANTHROPIC_API_KEY"]
        gemini_key = os.environ.get("GEMINI_API_KEY")
        
        # Check for API keys
        if not openai_key and model.startswith(("gpt", "o1", "o3")):
            raise ValueError("Please configure your OpenAI API key first")
        if not anthropic_key and model.startswith("claude"):
            raise ValueError("Please configure your Anthropic API key first")
        if not gemini_key and model.startswith("gemini"):
            raise ValueError("Please configure your Gemini API key first")
        
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
        You are a web developer specialising in creating Educational HTML5 interactive content.

        You have to complete one of the following tasks:"""
        
        # Initialize user_prompt with the original prompt
        user_prompt = prompt
        
        # Add iterative mode instructions if needed
        if is_iterative:
            # Check if we have current code to include
            has_current_code = bool(current_html.strip() or current_css.strip() or current_js.strip())
            
            if has_current_code:
                system_prompt += f"""

                ITERATIVE MODE INSTRUCTIONS:
                - You are modifying existing HTML, CSS, and JavaScript code that the user has provided.
                - Focus on addressing the specific requests while preserving the existing functionality and the overall structure of the code. 
                - As far as possible only add, remove or modify code to align with the user's instructions and leave the rest of the code unchanged.
                - Provide comments in the code to explain the changes you have made

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
                **IMPORTANT**: JavaScript is REQUIRED for all interactive content. You MUST include JavaScript code in your response, even for simple interactions. Without JavaScript, the HTML5 content will not be interactive.
                **CRITICAL**: Use the extract_code_components tool to return your code in a structured format.
                User request and instructions:
                """         

                print(f"Added current code to prompt in iterative mode - HTML: {len(current_html)} chars, CSS: {len(current_css)} chars, JS: {len(current_js)} chars")
            else:
                # When in iterative mode but no existing code, treat it as new content creation
                print("Iterative mode enabled but no current code found - treating as new content creation")
                system_prompt += """
            
            NEW CONTENT CREATION INSTRUCTIONS:
            Important:
            - Use the provided reference images as references on how to create the content.
            - Provide comments in the code on what the code is doing and how it works.
            **IMPORTANT**: JavaScript is REQUIRED for all interactive content. You MUST include JavaScript code in your response, even for simple interactions. Without JavaScript, the HTML5 content will not be interactive.
            **CRITICAL**: Use the extract_code_components tool to generate three separate components (HTML, CSS, JavaScript) in a structured format.

            User request and instructions:
            """
        else:
                system_prompt += """
            
            NEW CONTENT CREATION INSTRUCTIONS:
            Important:
            - Use the provided reference images as references on how to create the content.
            - Provide comments in the code on what the code is doing and how it works.
            **IMPORTANT**: JavaScript is REQUIRED for all interactive content. You MUST include JavaScript code in your response, even for simple interactions. Without JavaScript, the HTML5 content will not be interactive.
            **CRITICAL**: Use the extract_code_components tool to generate three separate components (HTML, CSS, JavaScript) in a structured format.

            User request and instructions:
            """
            
        # print(f"System prompt: {system_prompt}")
        
        # User ID and session ID are now passed as parameters
        # No need to set user_id = "anonymous" here anymore
        
        # Determine which AI service to use based on the model
        if model.startswith("claude"):
            # Use Anthropic/Claude
            import anthropic
            from anthropic._exceptions import OverloadedError, APIStatusError
            
            try:
                client = anthropic.Anthropic(api_key=anthropic_key, timeout=360.0)
                
                # Build message content with images if available
                message_content = [
                    {
                        "type": "text",
                        "text": system_prompt + user_prompt
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
                print("Message content: ", message_content)                # Create API call parameters
                api_params = {
                    "model": model,
                    "max_tokens": 16000,  # Default token limit
                    "temperature": 0.4,
                    "tools": [
                        {
                            "name": "extract_code_components",
                            "description": "Extract HTML, CSS, and JavaScript components from the generated code. All three components MUST be included for a complete interactive HTML5 experience.",
                            "input_schema": {
                                "type": "object",
                                "properties": {
                                    "html": {
                                        "type": "string",
                                        "description": "HTML content without the body tags"
                                    },
                                    "css": {
                                        "type": "string",
                                        "description": "CSS content without the style tags"
                                    },
                                    "javascript": {
                                        "type": "string",
                                        "description": "JavaScript content without the script tags. This is REQUIRED for interactive content."
                                    }
                                },
                                "required": ["html", "css", "javascript"]
                            }
                        }
                    ],
                    "messages": [
                        {
                            "role": "user",
                            "content": message_content
                        }
                    ]
                }
                
                # Claude API doesn't support both thinking mode and forced tool_choice together
                # So we need to choose one approach or the other
                if EXTENDED_THINKING_MODE:
                    try:
                        print("Using extended thinking mode without forced tool_choice")
                        # First try with thinking enabled but without forcing tool_choice
                        thinking_params = api_params.copy()
                        thinking_params["thinking"] = {
                            "type": "enabled",
                            "budget_tokens": 8192 # Allocate budget for extended thinking
                        }
                        # Set max_tokens higher than thinking budget_tokens
                        thinking_params["max_tokens"] = 10000 # Must be greater than budget_tokens
                        #set temperature to 1
                        thinking_params["temperature"] = 1
                        # Don't force tool choice when using thinking mode
                        # Let the model decide whether to use the tool
                        
                        # STEP 1: Make the initial API call with thinking mode
                        initial_response = client.messages.create(**thinking_params)
                        
                        # Extract thinking and tool_use blocks from the response
                        thinking_block = None
                        tool_use_block = None
                        text_content = ""
                        
                        if initial_response and hasattr(initial_response, 'content') and len(initial_response.content) > 0:
                            for content in initial_response.content:
                                if content.type == 'thinking':
                                    thinking_block = content
                                    print(f"Received thinking content: {len(content.thinking)} chars")
                                    # Save thinking content if available
                                    try:
                                        thinking_dir = Path("thinking_logs")
                                        thinking_dir.mkdir(exist_ok=True)
                                        thinking_file = thinking_dir / f"thinking_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                                        with open(thinking_file, "w") as f:
                                            f.write(content.thinking)
                                        print(f"Saved thinking content to {thinking_file}")
                                    except Exception as e:
                                        print(f"Could not save thinking content: {e}")
                                elif content.type == 'tool_use':
                                    tool_use_block = content
                                    print(f"Received tool use: {content.name}")
                                elif content.type == 'text':
                                    text_content += content.text + "\n"
                        
                        # Check if we got both thinking and tool use blocks
                        if thinking_block and tool_use_block and tool_use_block.name == 'extract_code_components':
                            # Extract tool input (the code components)
                            tool_input = tool_use_block.input
                            html = tool_input.get('html', '')
                            css = tool_input.get('css', '')
                            js = tool_input.get('javascript', '')
                            
                            print(f"Initial tool extraction - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
                            
                            # If we already have complete code components, we can return them
                            if html and (css or True) and js:  # CSS is optional
                                # Record token usage
                                completion_tokens = initial_response.usage.output_tokens
                                total_tokens = prompt_tokens + completion_tokens
                                
                                # Calculate generation time
                                end_time = datetime.datetime.now()
                                generation_time_ms = (end_time - start_time).total_seconds() * 1000
                                
                                # Save token usage to database
                                token_count.record_token_usage(
                                    model=model,
                                    prompt=prompt if prompt else None,
                                    prompt_tokens=prompt_tokens,
                                    completion_tokens=completion_tokens,
                                    total_tokens=total_tokens,
                                    user_id=user_id,
                                    session_id=session_id,
                                    generation_time_ms=generation_time_ms
                                )
                                
                                return html, css, js
                            
                            # STEP 2: If we need to process the tool result, send a follow-up request
                            # Create tool result message with the initial result
                            tool_result = {
                                "type": "tool_result",
                                "tool_use_id": tool_use_block.id,
                                "content": json.dumps({
                                    "status": "success",
                                    "message": "Code components extracted successfully"
                                })
                            }
                            
                            # Create continuation request
                            continuation_params = thinking_params.copy()  # Use the same parameters
                            continuation_params["messages"] = [
                                # Original message
                                {"role": "user", "content": message_content},
                                
                                # Assistant message with thinking and tool use
                                {"role": "assistant", "content": [thinking_block, tool_use_block]},
                                
                                # Tool result message
                                {"role": "user", "content": [tool_result]}
                            ]
                            
                            print("Sending continuation request with tool result")
                            final_response = client.messages.create(**continuation_params)
                            
                            # Handle the final response - should contain complete code
                            if final_response and hasattr(final_response, 'content') and len(final_response.content) > 0:
                                final_text_content = ""
                                for content in final_response.content:
                                    if content.type == 'text':
                                        final_text_content += content.text + "\n"
                                    # Check for additional tool use in final response
                                    elif content.type == 'tool_use' and content.name == 'extract_code_components':
                                        final_tool_input = content.input
                                        html = final_tool_input.get('html', '')
                                        css = final_tool_input.get('css', '')
                                        js = final_tool_input.get('javascript', '')
                                        print(f"Final tool extraction - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
                                
                                # If we don't have complete components from tool use, try extracting from text
                                if not (html and (css or True) and js):
                                    print("Extracting components from final text content")
                                    html, css, js = extract_components(final_text_content)
                                
                                # Record token usage for both requests combined
                                initial_tokens = initial_response.usage.output_tokens
                                final_tokens = final_response.usage.output_tokens
                                completion_tokens = initial_tokens + final_tokens
                                total_tokens = prompt_tokens + completion_tokens
                                
                                # Calculate generation time
                                end_time = datetime.datetime.now()
                                generation_time_ms = (end_time - start_time).total_seconds() * 1000
                                
                                # Save token usage to database
                                token_count.record_token_usage(
                                    model=model,
                                    prompt=prompt if prompt else None,
                                    prompt_tokens=prompt_tokens,
                                    completion_tokens=completion_tokens,
                                    total_tokens=total_tokens,
                                    user_id=user_id,
                                    session_id=session_id,
                                    generation_time_ms=generation_time_ms
                                )
                                
                                return html, css, js
                        else:
                            # We didn't get both thinking and tool use blocks
                            # Try to extract components from text content
                            print("Did not receive both thinking and tool use blocks, extracting from text")
                            html, css, js = extract_components(text_content)
                            
                            if html and (css or True) and js:  # CSS is optional
                                # Record token usage
                                completion_tokens = initial_response.usage.output_tokens
                                total_tokens = prompt_tokens + completion_tokens
                                
                                # Save token usage to database
                                token_count.record_token_usage(
                                    model=model,
                                    prompt=prompt if prompt else None,
                                    prompt_tokens=prompt_tokens,
                                    completion_tokens=completion_tokens,
                                    total_tokens=total_tokens,
                                    user_id=user_id,
                                    session_id=session_id
                                )
                                
                                return html, css, js
                    
                    except Exception as e:
                        print(f"Thinking mode attempt failed: {str(e)}. Falling back to regular tool approach.")
                
                # Either thinking mode is disabled, or thinking mode attempt failed
                # Use the standard approach with forced tool_choice but no thinking
                api_params["tool_choice"] = {"type": "tool", "name": "extract_code_components"}
                print("Using standard approach with forced tool_choice")
                
                # Make the actual API call with the parameters
                response = client.messages.create(**api_params)
                
                if response:
                    print(f"Received response from Claude. Type: {type(response)}")
                    
                    # Check if tool use was returned
                    if hasattr(response, 'content') and len(response.content) > 0:
                        tool_use_found = False
                        text_content = ""
                        thinking_content = ""
                        
                        # First pass: look for tool use and thinking content
                        for content in response.content:
                            if content.type == 'tool_use':
                                tool_use_found = True
                                tool_name = content.name
                                tool_input = content.input
                                
                                # Print the raw JSON for debugging
                                import json
                                #print(f"TOOL USE JSON DATA:")
                                #print(json.dumps(tool_input, indent=2))
                                
                                if tool_name == 'extract_code_components':
                                    html = tool_input.get('html', '')
                                    css = tool_input.get('css', '')
                                    js = tool_input.get('javascript', '')
                                    
                                    print(f"Successfully extracted components using tool - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
                                    
                                    # Print JS for debugging
                                    #print(f"JavaScript content (first 500 chars):")
                                    #print(js[:500] + "..." if len(js) > 500 else js)
                                    
                                    # If JavaScript is missing or empty, collect text content for later extraction
                                    if not js:
                                        print("WARNING: JavaScript missing from tool use, will try to extract from text content")
                            elif content.type == 'text':
                                text_content += content.text + "\n"
                            elif content.type == 'thinking' and EXTENDED_THINKING_MODE:
                                thinking_content = content.thinking
                                print(f"Received thinking content: {len(thinking_content)} chars")
                        
                        # Save thinking content if available (for logging/debugging purposes)
                        if thinking_content and EXTENDED_THINKING_MODE:
                            # This is optional - you can save the thinking content to a file for analysis
                            try:
                                thinking_dir = Path("thinking_logs")
                                thinking_dir.mkdir(exist_ok=True)
                                thinking_file = thinking_dir / f"thinking_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                                with open(thinking_file, "w") as f:
                                    f.write(thinking_content)
                                print(f"Saved thinking content to {thinking_file}")
                            except Exception as e:
                                print(f"Could not save thinking content: {e}")
                        
                        # If we found tool use but are missing JavaScript, try to extract from text content
                        if tool_use_found and not js and text_content:
                            print("Attempting to extract JavaScript from text content")
                            import re
                            js_match = re.search(r'```(?:javascript|js)\s*(.*?)\s*```', text_content, re.DOTALL)
                            if js_match:
                                js = js_match.group(1).strip()
                                print(f"Extracted JavaScript from text content - {len(js)} chars")
                        
                        # If we have valid HTML, CSS and JS from tool use, return the components
                        if tool_use_found and html and (css or True) and js:  # CSS is optional
                            # Record token usage
                            completion_tokens = response.usage.output_tokens
                            total_tokens = prompt_tokens + completion_tokens
                            
                            # Calculate generation time
                            end_time = datetime.datetime.now()
                            generation_time_ms = (end_time - start_time).total_seconds() * 1000
                            
                            # Save token usage to database
                            token_count.record_token_usage(
                                model=model,
                                prompt=prompt if prompt else None,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                total_tokens=total_tokens,
                                user_id=user_id,
                                session_id=session_id,
                                generation_time_ms=generation_time_ms
                            )
                            
                            return html, css, js
                        
                        # If we have tool use but missing components, fall through to text-based extraction
                        if tool_use_found and text_content:
                            print("Tool use found but components incomplete. Falling back to text extraction.")
                            code = text_content
                        else:
                            # Fallback to traditional extraction if no tool use or missing components
                            code = response.content[0].text.strip() if hasattr(response.content[0], 'text') else ""
                    else:
                        # No content found in response
                        code = response.content[0].text.strip() if hasattr(response.content[0], 'text') else ""
                    
                    print(f"Falling back to regex extraction. Response content length: {len(code)} chars")
                    
                    # Extract components using regex as fallback
                    html, css, js = extract_components(code)
                    
                    # Record token usage
                    completion_tokens = response.usage.output_tokens
                    total_tokens = prompt_tokens + completion_tokens
                    
                    # Save token usage to database
                    token_count.record_token_usage(
                        model=model,
                        prompt=prompt if prompt else None,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        user_id=user_id,
                        session_id=session_id
                    )
                    
                    # If JavaScript is missing or empty, try to obtain it from elsewhere in the response
                    if not js:
                        print("WARNING: JavaScript missing from Claude response, attempting additional extraction")
                        # Try to extract JavaScript using more focused regex
                        import re
                        js_match = re.search(r'```(?:javascript|js)\s*(.*?)\s*```', code, re.DOTALL)
                        if js_match:
                            js = js_match.group(1).strip()
                            print(f"Extracted JavaScript with targeted regex - {len(js)} chars")
                    
                    # Verify we have content
                    if not (html or css or js):
                        print("WARNING: No content extracted from Claude tool use. Using original content.")
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
        elif model.startswith("gemini"):
            # Use Google Gemini
            from google import genai
            from google.genai import types
            
            try:
                # Configure the client
                client = genai.Client(api_key=gemini_key)
                
                # Define the function declaration for extract_code_components
                extract_code_components_declaration = {
                    "name": "extract_code_components",
                    "description": "Extract HTML, CSS, and JavaScript components from the generated code. All three components MUST be included for a complete interactive HTML5 experience.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "html": {
                                "type": "string",
                                "description": "HTML content without the body tags"
                            },
                            "css": {
                                "type": "string",
                                "description": "CSS content without the style tags"
                            },
                            "javascript": {
                                "type": "string",
                                "description": "JavaScript content without the script tags. This is REQUIRED for interactive content."
                            }
                        },
                        "required": ["html", "css", "javascript"]
                    }
                }
                
                # Configure tools and generation config
                tools = types.Tool(function_declarations=[extract_code_components_declaration])
                config = types.GenerateContentConfig(
                    tools=[tools],
                    temperature=0.4,
                    max_output_tokens=8192
                )
                
                # Build content with system prompt and user message
                contents = []
                
                # Add system message
                contents.append(
                    types.Content(
                        role="user",
                        parts=[types.Part(text=system_prompt + user_prompt)]
                    )
                )
                
                # Note: Gemini API doesn't currently support image data in the same way as Claude/OpenAI
                # We should add image support when available
                
                # Make the API call
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config
                )
                
                if response:
                    print(f"Received response from Gemini. Type: {type(response)}")
                    
                    # Check for function call in the response
                    if response.candidates and response.candidates[0].content.parts:
                        for part in response.candidates[0].content.parts:
                            if hasattr(part, 'function_call') and part.function_call:
                                function_call = part.function_call
                                
                                if function_call.name == 'extract_code_components':
                                    # Extract components from function call args
                                    args = function_call.args
                                    html = args.get('html', '')
                                    css = args.get('css', '')
                                    js = args.get('javascript', '')
                                    
                                    print(f"Successfully extracted components using function call - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
                                    
                                    # Record token usage (if available from Gemini API)
                                    # Note: Gemini may structure this differently, adapt as needed
                                    prompt_tokens = getattr(response, 'usage', {}).get('prompt_tokens', 0)
                                    completion_tokens = getattr(response, 'usage', {}).get('completion_tokens', 0) 
                                    total_tokens = prompt_tokens + completion_tokens
                                    
                                    # Calculate generation time
                                    end_time = datetime.datetime.now()
                                    generation_time_ms = (end_time - start_time).total_seconds() * 1000
                                    
                                    # Save token usage to database
                                    token_count.record_token_usage(
                                        model=model,
                                        prompt=prompt if prompt else None,
                                        prompt_tokens=prompt_tokens,
                                        completion_tokens=completion_tokens,
                                        total_tokens=total_tokens,
                                        user_id=user_id,
                                        session_id=session_id,
                                        generation_time_ms=generation_time_ms
                                    )
                                    
                                    return html, css, js
                    
                    # Fallback to text extraction if no function call
                    text_content = ""
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                            for part in candidate.content.parts:
                                if hasattr(part, 'text'):
                                    text_content += part.text + "\n"
                    
                    print(f"No function call found or extraction failed. Response content length: {len(text_content)} chars")
                    
                    # Extract components using regex as fallback
                    html, css, js = extract_components(text_content)
                    
                    # If JavaScript is missing or empty, try to obtain it from elsewhere in the response
                    if not js:
                        print("WARNING: JavaScript missing from Gemini response, attempting additional extraction")
                        # Try to extract JavaScript using more focused regex
                        import re
                        js_match = re.search(r'```(?:javascript|js)\s*(.*?)\s*```', text_content, re.DOTALL)
                        if js_match:
                            js = js_match.group(1).strip()
                            print(f"Extracted JavaScript with targeted regex - {len(js)} chars")
                    
                    # Verify we have content
                    if not (html or css or js):
                        print("WARNING: No content extracted from Gemini response. Using original content.")
                        # Return the original content if we couldn't extract anything
                        if is_iterative and current_html and current_css and current_js:
                            return current_html, current_css, current_js
                    
                    # Record token usage (if available)
                    prompt_tokens = getattr(response, 'usage', {}).get('prompt_tokens', 0)
                    completion_tokens = getattr(response, 'usage', {}).get('completion_tokens', 0)
                    total_tokens = prompt_tokens + completion_tokens
                    
                    # Calculate generation time
                    end_time = datetime.datetime.now()
                    generation_time_ms = (end_time - start_time).total_seconds() * 1000
                    
                    # Save token usage to database
                    token_count.record_token_usage(
                        model=model,
                        prompt=prompt if prompt else None,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        user_id=user_id,
                        session_id=session_id,
                        generation_time_ms=generation_time_ms
                    )
                    
                    return html, css, js
                else:
                    print("Gemini returned empty response")
                    raise ValueError("Gemini returned an empty response")
            except Exception as e:
                raise ValueError(f"Gemini API error: {str(e)}")
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
                
                # Define tools for OpenAI
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "extract_code_components",
                            "description": "Extract HTML, CSS, and JavaScript components from the generated code. All three components MUST be included for a complete interactive HTML5 experience.",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "html": {
                                        "type": "string",
                                        "description": "HTML content without the body tags"
                                    },
                                    "css": {
                                        "type": "string",
                                        "description": "CSS content without the style tags"
                                    },
                                    "javascript": {
                                        "type": "string",
                                        "description": "JavaScript content without the script tags. This is REQUIRED for interactive content."
                                    }
                                },
                                "required": ["html", "css", "javascript"]
                            }
                        }
                    }
                ]
                
                # Make the API call with function tools
                response = client.chat.completions.create(
                    model=model,
                    max_tokens=16000,
                    messages=messages,
                    tools=tools,
                    tool_choice={"type": "function", "function": {"name": "extract_code_components"}}
                )
                
                if response:
                    print(f"Received response from OpenAI. Type: {type(response)}")
                    
                    # Check if we have tool calls in the response
                    if response.choices[0].message.tool_calls:
                        print("Found tool calls in the response")
                        tool_call = response.choices[0].message.tool_calls[0]
                        
                        if tool_call.function.name == 'extract_code_components':
                            # Parse the function arguments (JSON)
                            import json
                            tool_args = json.loads(tool_call.function.arguments)
                            
                            # Extract components from the tool call
                            html = tool_args.get('html', '')
                            css = tool_args.get('css', '')
                            js = tool_args.get('javascript', '')
                            
                            print(f"Successfully extracted components using tool - HTML: {len(html)} chars, CSS: {len(css)} chars, JS: {len(js)} chars")
                            
                            # Record token usage
                            prompt_tokens = response.usage.prompt_tokens
                            completion_tokens = response.usage.completion_tokens
                            total_tokens = response.usage.total_tokens
                            
                            # Calculate generation time
                            end_time = datetime.datetime.now()
                            generation_time_ms = (end_time - start_time).total_seconds() * 1000
                            
                            # Save token usage to database
                            token_count.record_token_usage(
                                model=model,
                                prompt=prompt if prompt else None,
                                prompt_tokens=prompt_tokens,
                                completion_tokens=completion_tokens,
                                total_tokens=total_tokens,
                                user_id=user_id,
                                session_id=session_id,
                                generation_time_ms=generation_time_ms
                            )
                            
                            # If JavaScript is missing or empty, try to extract from regular content
                            if not js and response.choices[0].message.content:
                                print("WARNING: JavaScript missing from tool use, trying to extract from message content")
                                import re
                                js_match = re.search(r'```(?:javascript|js)\s*(.*?)\s*```', response.choices[0].message.content, re.DOTALL)
                                if js_match:
                                    js = js_match.group(1).strip()
                                    print(f"Extracted JavaScript from message content - {len(js)} chars")
                            
                            return html, css, js
                    
                    # Fallback to traditional extraction if no tool calls
                    code = response.choices[0].message.content.strip()
                    print(f"No tool calls found or extraction failed. Response content length: {len(code)} chars")
                    
                    # Record token usage
                    prompt_tokens = response.usage.prompt_tokens
                    completion_tokens = response.usage.completion_tokens
                    total_tokens = response.usage.total_tokens
                    
                    # Calculate generation time
                    end_time = datetime.datetime.now()
                    generation_time_ms = (end_time - start_time).total_seconds() * 1000
                    
                    # Save token usage to database
                    token_count.record_token_usage(
                        model=model,
                        prompt=prompt if prompt else None,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        total_tokens=total_tokens,
                        user_id=user_id,
                        session_id=session_id,
                        generation_time_ms=generation_time_ms
                    )
                    
                    # Extract components
                    html, css, js = extract_components(code)
                    
                    # If JavaScript is missing or empty, try to obtain it from elsewhere in the response
                    if not js:
                        print("WARNING: JavaScript missing from OpenAI response, attempting additional extraction")
                        # Try to extract JavaScript using more focused regex
                        import re
                        js_match = re.search(r'```(?:javascript|js)\s*(.*?)\s*```', code, re.DOTALL)
                        if js_match:
                            js = js_match.group(1).strip()
                            print(f"Extracted JavaScript with targeted regex - {len(js)} chars")
                    
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