from fasthtml.common import *
import os
import json
import datetime
import base64
from pathlib import Path
import tempfile
import yaml
from components.lea_form import create_lea_chatbot, ChatMessage, create_recipe_carousel

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI API key
if os.getenv("OPENAI_API_KEY") is None:
    os.environ["OPENAI_API_KEY"] = ""
else:
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
 
 
#extract the recipe template from the config.yaml file
with open('config.yaml', 'r') as file:
    config = yaml.safe_load(file)
    #extract the base template      
    base_template = config['templates']['base_template']
    #extract the recipe template 1  
    recipe_template_1 = config['templates']['recipe_template_1']
    #extract the recipe template 2  
    recipe_template_2 = config['templates']['recipe_template_2']
    #extract the recipe template 3  
    recipe_template_3 = config['templates']['recipe_template_3']
    #extract the recipe template 4  
    recipe_template_4 = config['templates']['recipe_template_4']
    #extract the recipe template 5  
    recipe_template_5 = config['templates']['recipe_template_5']
    #extract the recipe template 6  
    recipe_template_6 = config['templates']['recipe_template_6']
    #extract the recipe template 7  
    recipe_template_7 = config['templates']['recipe_template_7']
    #extract the recipe template 8  
    recipe_template_8 = config['templates']['recipe_template_8']
    
    
    

# Session keys
CHAT_HISTORY_KEY = "lea_chat_history"
SYSTEM_PROMPT_KEY = "system_prompt"
RECIPE_TEMPLATE_KEY = "selected_recipe"

# Default system prompt (will be replaced by base_template)

def routes(rt):
    @rt('/menuE')
    def get(req, session):
        """Render the main chatbot interface with recipe templates"""
        api_key = os.environ.get("OPENAI_API_KEY", "")
        
        # Store system prompt in session if not already set
        if SYSTEM_PROMPT_KEY not in session:
           session[SYSTEM_PROMPT_KEY] = base_template
        
        # Create recipe templates dictionary
        recipe_templates = {
            "recipe_1": recipe_template_1,
            "recipe_2": recipe_template_2,
            "recipe_3": recipe_template_3,
            "recipe_4": recipe_template_4,
            "recipe_5": recipe_template_5,
            "recipe_6": recipe_template_6,
            "recipe_7": recipe_template_7,
            "recipe_8": recipe_template_8
        }
        
        # Store recipe templates in session for later use
        session[RECIPE_TEMPLATE_KEY] = recipe_templates
        
# Import the carousel component
        from components.lea_form import create_recipe_carousel
        
        return Titled("LEA Chatbot",
            Link(rel="stylesheet", href="static/css/styles.css"),
            Style("""
                body {
                    background-color: #121212 !important;
                    color: #e0e0e0 !important;
                    margin: 0;
                    padding: 0;
                }
                main {
                    background-color: #121212 !important;
                }
                h1 {
                    color: #e0e0e0 !important;
                }
                .recipe-card {
                    transition: all 0.3s ease;
                    cursor: pointer;
                    background-color: #2d3748;
                    border-width: 2px;
                }
                .recipe-card:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
            """),
            create_lea_chatbot(api_key, base_template, recipe_templates),

                    # Use a single consolidated script
            NotStr("""
            <script>
                // Make this function available immediately
                window.handleRecipeClick = function(element) {
                    const recipeKey = element.getAttribute('data-recipe-key');
                    const recipeText = element.getAttribute('data-recipe-text');
                    
                    console.log("Recipe clicked:", recipeKey);
                    
                    // Find and update the textarea
                    const textarea = document.getElementById('selected-recipe');
                    if (textarea) {
                        textarea.value = recipeText;
                        textarea.setAttribute('data-recipe-name', 'recipe_' + recipeKey);
                        console.log("Updated textarea with recipe text");
                    } else {
                        console.error("Could not find selected-recipe textarea");
                    }
                    
                    // Highlight the selected card
                    document.querySelectorAll('.recipe-card').forEach(card => {
                        card.classList.remove('selected');
                    });
                    element.classList.add('selected');
                    
                    // Update status message
                    const statusEl = document.getElementById('prompt-status');
                    if (statusEl) {
                        statusEl.textContent = 'Recipe selected but not saved as prompt yet';
                        statusEl.className = 'text-sm text-yellow-500';
                    }
                };
                
                // Initialize the UI once the DOM is loaded
                document.addEventListener('DOMContentLoaded', function() {
                    console.log("DOM loaded, initializing UI");
                    
                    // Initialize carousel navigation
                    const prevButton = document.getElementById('prev-button');
                    const nextButton = document.getElementById('next-button');
                    const container = document.getElementById('carousel-container');
                    
                    if (prevButton && container) {
                        prevButton.addEventListener('click', function() {
                            container.scrollBy({left: -300, behavior: 'smooth'});
                        });
                    }
                    
                    if (nextButton && container) {
                        nextButton.addEventListener('click', function() {
                            container.scrollBy({left: 300, behavior: 'smooth'});
                        });
                    }
                    
                    // Initialize UI state based on session data
                    const statusEl = document.getElementById('prompt-status');
                    if (statusEl) {
                        const hasRecipe = statusEl.textContent.includes('set to base template only') === false;
                        
                        if (hasRecipe) {
                            statusEl.textContent = 'System prompt includes a recipe template';
                            statusEl.className = 'text-sm text-green-500';
                        }
                    }
                });
            </script>
            """)
        )
    
    @rt('/api/lea/get-messages')
    def get(session):
        """Get existing chat messages from session"""
        messages = session.get(CHAT_HISTORY_KEY, [])
        
        # If no messages exist, add a welcome message
        if not messages:
            welcome_message = {
                "role": "assistant",
                "content": "Hello! I'm LEA, your AI assistant. How can I help you today?",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "show_avatar": True
            }
            messages = [welcome_message]
            session[CHAT_HISTORY_KEY] = messages
        
        # Return rendered message components
        return Div(*[ChatMessage(msg) for msg in messages])
    
    @rt('/api/lea/clear-chat')
    def post(session):
        """Clear chat history"""
        if CHAT_HISTORY_KEY in session:
            del session[CHAT_HISTORY_KEY]
        
        # Return welcome message
        welcome_message = {
            "role": "assistant",
            "content": "Chat cleared. How can I help you today?",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "show_avatar": True
        }
        session[CHAT_HISTORY_KEY] = [welcome_message]
        
        return ChatMessage(welcome_message)
    
    @rt('/api/lea/send-message')
    async def post(req, session):
        """Process user message and get AI response"""
        form = await req.form()
        user_message = form.get("message", "").strip()
        model = form.get("model", "gpt-4o")
        api_key = form.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
        
        # Validate inputs
        if not user_message:
            return Div("Please enter a message", cls="error-message")
        
        if not api_key:
            return Div(
                "OpenAI API key is required. Please set it in the environment variables or provide it in the form.",
                cls="error-message"
            )
        
        # Get chat history or initialize if empty
        messages = session.get(CHAT_HISTORY_KEY, [])
        
        # Add user message
        user_msg = {
            "role": "user",
            "content": user_message,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "show_avatar": True
        }
        messages.append(user_msg)
        session[CHAT_HISTORY_KEY] = messages
        
        # Prepare API request format
        api_messages = [{"role": "system", "content": session[SYSTEM_PROMPT_KEY]}]
        #assistant_messages = [{"role": "assistant", "content": session["recipe_template"]}]
        for msg in messages:
            if msg["role"] in ["user", "assistant"]:
                api_messages.append({"role": msg["role"], "content": msg["content"]})
        
        try:
            # Call OpenAI API using the specified model
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=0.7,
                max_tokens=1000,
            )
            
            # Extract response content
            assistant_response = response.choices[0].message.content.strip()
            
            # Add assistant message to history
            assistant_msg = {
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "show_avatar": True
            }
            messages.append(assistant_msg)
            session[CHAT_HISTORY_KEY] = messages
            
            # Return just the latest message pair to append to the chat
            return Div(
                ChatMessage(user_msg),
                ChatMessage(assistant_msg),
                # Add auto-scroll script to scroll to bottom
                NotStr("""
                <script>
                    document.querySelector('#chatlist').scrollTop = document.querySelector('#chatlist').scrollHeight;
                    document.querySelector('#user-message').value = '';
                </script>
                """)
            )
            
        except Exception as e:
            # Handle API errors
            error_msg = {
                "role": "assistant",
                "content": f"Error: {str(e)}. Please try again or check your API key.",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "show_avatar": True
            }
            messages.append(error_msg)
            session[CHAT_HISTORY_KEY] = messages
            
            return Div(
                ChatMessage(user_msg),
                ChatMessage(error_msg),
                NotStr("""
                <script>
                    document.querySelector('#chatlist').scrollTop = document.querySelector('#chatlist').scrollHeight;
                </script>
                """)
            )
    
    @rt('/api/lea/upload-form')
    def get():
        """Show the image upload form"""
        return Div(
            Form(
                Input(
                    type="file",
                    name="image",
                    accept="image/*",
                    cls="p-2 border w-full rounded"
                ),
                Button(
                    "Upload and Analyze",
                    type="button",
                    hx_post="/api/lea/upload-image",
                    hx_encoding="multipart/form-data",
                    hx_include="closest form",
                    hx_target="#chatlist",
                    hx_swap="beforeend",
                    hx_indicator="#typing-indicator",
                    cls="mt-2 p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                ),
                Button(
                    "Cancel",
                    type="button",
                    hx_on="click: document.querySelector('#upload-area').classList.add('hidden')",
                    cls="mt-2 ml-2 p-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                ),
                enctype="multipart/form-data",
                cls="p-4 border rounded"
            ),
            NotStr("""
            <script>
                document.querySelector('#upload-area').classList.remove('hidden');
            </script>
            """)
        )
    
    @rt('/api/lea/upload-image')
    async def post(req, session):
        """Process uploaded image and get AI analysis"""
        form = await req.form()
        api_key = form.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
        model = form.get("model", "gpt-4o")
        
        # Check for API key
        if not api_key:
            return Div(
                "OpenAI API key is required for image analysis.",
                cls="error-message"
            )
        
        # Get uploaded file
        uploaded_file = form.get("image")
        if not uploaded_file:
            return Div("No image uploaded", cls="error-message")
        
        try:
            # Read image content
            content = await uploaded_file.read()
            filename = uploaded_file.filename
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.' + filename.split('.')[-1]) as temp_file:
                temp_path = temp_file.name
                temp_file.write(content)
            
            # Get chat history
            messages = session.get(CHAT_HISTORY_KEY, [])
            
            # Add user message about the image
            user_msg = {
                "role": "user",
                "content": f"I've uploaded an image: {filename}. Please analyze it.",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "show_avatar": True
            }
            messages.append(user_msg)
            
            # Add image preview to chat
            img_preview_msg = {
                "role": "user",
                "content": f'<img src="data:image/{filename.split(".")[-1]};base64,{base64.b64encode(content).decode()}" alt="Uploaded image" style="max-width: 100%; max-height: 300px;">',
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "show_avatar": False
            }
            messages.append(img_preview_msg)
            session[CHAT_HISTORY_KEY] = messages
            
            # Call OpenAI API with vision capabilities
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            # Prepare base64 encoded image
            with open(temp_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Use vision model
            response = client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o which has vision capabilities
                messages=[
                    {"role": "system", "content": "You are an AI assistant that can analyze images. Provide insights about the uploaded image."},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Please analyze this image and describe what you see."},
                        {"type": "image_url", "image_url": {"url": f"data:image/{filename.split('.')[-1]};base64,{base64_image}"}}
                    ]}
                ],
                max_tokens=1000
            )
            
            # Extract response
            assistant_response = response.choices[0].message.content
            
            # Add assistant message to history
            assistant_msg = {
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "show_avatar": True
            }
            messages.append(assistant_msg)
            session[CHAT_HISTORY_KEY] = messages
            
            # Clean up the temporary file
            os.unlink(temp_path)
            
            # Return the latest message sequence to append to the chat
            return Div(
                ChatMessage(user_msg),
                ChatMessage(img_preview_msg),
                ChatMessage(assistant_msg),
                NotStr("""
                <script>
                    document.querySelector('#chatlist').scrollTop = document.querySelector('#chatlist').scrollHeight;
                    document.querySelector('#upload-area').classList.add('hidden');
                </script>
                """)
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error processing image: {error_details}")
            
            # Add error message to chat
            error_msg = {
                "role": "assistant",
                "content": f"Error processing the image: {str(e)}. Please try again with a different image or format.",
                "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "show_avatar": True
            }
            
            if CHAT_HISTORY_KEY in session:
                messages = session[CHAT_HISTORY_KEY]
                messages.append(error_msg)
                session[CHAT_HISTORY_KEY] = messages
            
            return Div(
                ChatMessage(error_msg),
                NotStr("""
                <script>
                    document.querySelector('#chatlist').scrollTop = document.querySelector('#chatlist').scrollHeight;
                    document.querySelector('#upload-area').classList.add('hidden');
                </script>
                """)
            )
            
    # Add these routes to the routes function in lea_chatbot.py

    @rt('/api/lea/save-recipe')
    async def post(req, session):
        """Save the selected recipe template to the system prompt"""
        form = await req.form()
        selected_recipe = form.get("selected_recipe", "").strip()
        
        if not selected_recipe:
            return Div(
                P("No recipe content provided", cls="text-red-500"),
                hx_swap_oob="true",
                id="prompt-status"
            )
        
        # Always start with the base template
        new_system_prompt = f"{base_template}\n\n{selected_recipe}"
        
        # Store in session
        session[SYSTEM_PROMPT_KEY] = new_system_prompt
        session[RECIPE_TEMPLATE_KEY] = selected_recipe
        
        # Return confirmation
        return Div(
            P(f"System prompt updated with selected recipe template", cls="text-green-500"),
            hx_swap_oob="true",
            id="prompt-status"
        )
    
    @rt('/api/lea/reset-prompt')
    def post(session):
        """Reset the system prompt to just the base template"""
        session[SYSTEM_PROMPT_KEY] = base_template
        
        return Div(
            P("System prompt reset to base template only", cls="text-green-500"),
            hx_swap_oob="true",
            id="prompt-status"
        )
    
    @rt('/api/lea/get-current-prompt')
    def get(session):
        """Get the current system prompt"""
        current_prompt = session.get(SYSTEM_PROMPT_KEY, base_template)
        
        return Div(
            Pre(current_prompt, cls="p-2 bg-gray-800 rounded text-sm max-h-40 overflow-y-auto"),
            Button(
                "Reset to Base Template",
                hx_post="/api/lea/reset-prompt",
                cls="mt-2 text-xs bg-red-600 text-white py-1 px-2 rounded"
            ),
            hx_swap_oob="true",
            id="current-prompt-display"
        )
# def routes(rt):
#     @rt('/menuE')
#     def get(req):
#         """Render the main chatbot interface"""
#         api_key = os.environ.get("OPENAI_API_KEY", "")
#         return Titled("LEA Chatbot",
#             Link(rel="stylesheet", href="static/css/styles.css"),
#             create_lea_chatbot(api_key)
#         )
    
#     @rt('/api/lea/get-messages')
#     def get(session):
#         """Get existing chat messages from session"""
#         messages = session.get(CHAT_HISTORY_KEY, [])
        
#         # If no messages exist, add a welcome message
#         if not messages:
#             welcome_message = {
#                 "role": "assistant",
#                 "content": "Hello! I'm LEA, your AI assistant. How can I help you today?",
#                 "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 "show_avatar": True
#             }
#             messages = [welcome_message]
#             session[CHAT_HISTORY_KEY] = messages
        
#         # Return rendered message components
#         return Div(*[ChatMessage(msg) for msg in messages])
    
#     @rt('/api/lea/clear-chat')
#     def post(session):
#         """Clear chat history"""
#         if CHAT_HISTORY_KEY in session:
#             del session[CHAT_HISTORY_KEY]
        
#         # Return welcome message
#         welcome_message = {
#             "role": "assistant",
#             "content": "Chat cleared. How can I help you today?",
#             "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "show_avatar": True
#         }
#         session[CHAT_HISTORY_KEY] = [welcome_message]
        
#         return ChatMessage(welcome_message)
    
#     @rt('/api/lea/send-message')
#     async def post(req, session):
#         """Process user message and get AI response"""
#         form = await req.form()
#         user_message = form.get("message", "").strip()
#         model = form.get("model", "gpt-4o")
#         api_key = form.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
        
#         # Validate inputs
#         if not user_message:
#             return Div("Please enter a message", cls="error-message")
        
#         if not api_key:
#             return Div(
#                 "OpenAI API key is required. Please set it in the environment variables or provide it in the form.",
#                 cls="error-message"
#             )
        
#         # Get chat history or initialize if empty
#         messages = session.get(CHAT_HISTORY_KEY, [])
        
#         # Add user message
#         user_msg = {
#             "role": "user",
#             "content": user_message,
#             "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "show_avatar": True
#         }
#         messages.append(user_msg)
#         session[CHAT_HISTORY_KEY] = messages
        
#         # Prepare API request format
#         api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
#         for msg in messages:
#             if msg["role"] in ["user", "assistant"]:
#                 api_messages.append({"role": msg["role"], "content": msg["content"]})
        
#         try:
#             # Call OpenAI API using the specified model
#             from openai import OpenAI
#             client = OpenAI(api_key=api_key)
            
#             response = client.chat.completions.create(
#                 model=model,
#                 messages=api_messages,
#                 temperature=0.7,
#                 max_tokens=1000,
#             )
            
#             # Extract response content
#             assistant_response = response.choices[0].message.content.strip()
            
#             # Add assistant message to history
#             assistant_msg = {
#                 "role": "assistant",
#                 "content": assistant_response,
#                 "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 "show_avatar": True
#             }
#             messages.append(assistant_msg)
#             session[CHAT_HISTORY_KEY] = messages
            
#             # Return just the latest message pair to append to the chat
#             return Div(
#                 ChatMessage(user_msg),
#                 ChatMessage(assistant_msg),
#                 # Add auto-scroll script to scroll to bottom
#                 NotStr("""
#                 <script>
#                     document.querySelector('#chatlist').scrollTop = document.querySelector('#chatlist').scrollHeight;
#                     document.querySelector('#user-message').value = '';
#                 </script>
#                 """)
#             )
            
#         except Exception as e:
#             # Handle API errors
#             error_msg = {
#                 "role": "assistant",
#                 "content": f"Error: {str(e)}. Please try again or check your API key.",
#                 "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 "show_avatar": True
#             }
#             messages.append(error_msg)
#             session[CHAT_HISTORY_KEY] = messages
            
#             return Div(
#                 ChatMessage(user_msg),
#                 ChatMessage(error_msg),
#                 NotStr("""
#                 <script>
#                     document.querySelector('#chatlist').scrollTop = document.querySelector('#chatlist').scrollHeight;
#                 </script>
#                 """)
#             )
    
#     @rt('/api/lea/upload-form')
#     def get():
#         """Show the image upload form"""
#         return Div(
#             Form(
#                 Input(
#                     type="file",
#                     name="image",
#                     accept="image/*",
#                     cls="p-2 border w-full rounded"
#                 ),
#                 Button(
#                     "Upload and Analyze",
#                     type="button",
#                     hx_post="/api/lea/upload-image",
#                     hx_encoding="multipart/form-data",
#                     hx_include="closest form",
#                     hx_target="#chatlist",
#                     hx_swap="beforeend",
#                     hx_indicator="#typing-indicator",
#                     cls="mt-2 p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
#                 ),
#                 Button(
#                     "Cancel",
#                     type="button",
#                     hx_on="click: document.querySelector('#upload-area').classList.add('hidden')",
#                     cls="mt-2 ml-2 p-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
#                 ),
#                 enctype="multipart/form-data",
#                 cls="p-4 border rounded"
#             ),
#             NotStr("""
#             <script>
#                 document.querySelector('#upload-area').classList.remove('hidden');
#             </script>
#             """)
#         )
    
#     @rt('/api/lea/upload-image')
#     async def post(req, session):
#         """Process uploaded image and get AI analysis"""
#         form = await req.form()
#         api_key = form.get("api_key") or os.environ.get("OPENAI_API_KEY", "")
#         model = form.get("model", "gpt-4o")
        
#         # Check for API key
#         if not api_key:
#             return Div(
#                 "OpenAI API key is required for image analysis.",
#                 cls="error-message"
#             )
        
#         # Get uploaded file
#         uploaded_file = form.get("image")
#         if not uploaded_file:
#             return Div("No image uploaded", cls="error-message")
        
#         try:
#             # Read image content
#             content = await uploaded_file.read()
#             filename = uploaded_file.filename
            
#             # Create a temporary file
#             with tempfile.NamedTemporaryFile(delete=False, suffix='.' + filename.split('.')[-1]) as temp_file:
#                 temp_path = temp_file.name
#                 temp_file.write(content)
            
#             # Get chat history
#             messages = session.get(CHAT_HISTORY_KEY, [])
            
#             # Add user message about the image
#             user_msg = {
#                 "role": "user",
#                 "content": f"I've uploaded an image: {filename}. Please analyze it.",
#                 "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 "show_avatar": True
#             }
#             messages.append(user_msg)
            
#             # Add image preview to chat
#             img_preview_msg = {
#                 "role": "user",
#                 "content": f'<img src="data:image/{filename.split(".")[-1]};base64,{base64.b64encode(content).decode()}" alt="Uploaded image" style="max-width: 100%; max-height: 300px;">',
#                 "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 "show_avatar": False
#             }
#             messages.append(img_preview_msg)
#             session[CHAT_HISTORY_KEY] = messages
            
#             # Call OpenAI API with vision capabilities
#             from openai import OpenAI
#             client = OpenAI(api_key=api_key)
            
#             # Prepare base64 encoded image
#             with open(temp_path, "rb") as image_file:
#                 base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
#             # Use vision model
#             response = client.chat.completions.create(
#                 model="gpt-4o",  # Using GPT-4o which has vision capabilities
#                 messages=[
#                     {"role": "system", "content": "You are an AI assistant that can analyze images. Provide insights about the uploaded image."},
#                     {"role": "user", "content": [
#                         {"type": "text", "text": "Please analyze this image and describe what you see."},
#                         {"type": "image_url", "image_url": {"url": f"data:image/{filename.split('.')[-1]};base64,{base64_image}"}}
#                     ]}
#                 ],
#                 max_tokens=1000
#             )
            
#             # Extract response
#             assistant_response = response.choices[0].message.content
            
#             # Add assistant message to history
#             assistant_msg = {
#                 "role": "assistant",
#                 "content": assistant_response,
#                 "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 "show_avatar": True
#             }
#             messages.append(assistant_msg)
#             session[CHAT_HISTORY_KEY] = messages
            
#             # Clean up the temporary file
#             os.unlink(temp_path)
            
#             # Return the latest message sequence to append to the chat
#             return Div(
#                 ChatMessage(user_msg),
#                 ChatMessage(img_preview_msg),
#                 ChatMessage(assistant_msg),
#                 NotStr("""
#                 <script>
#                     document.querySelector('#chatlist').scrollTop = document.querySelector('#chatlist').scrollHeight;
#                     document.querySelector('#upload-area').classList.add('hidden');
#                 </script>
#                 """)
#             )
            
#         except Exception as e:
#             import traceback
#             error_details = traceback.format_exc()
#             print(f"Error processing image: {error_details}")
            
#             # Add error message to chat
#             error_msg = {
#                 "role": "assistant",
#                 "content": f"Error processing the image: {str(e)}. Please try again with a different image or format.",
#                 "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#                 "show_avatar": True
#             }
            
#             if CHAT_HISTORY_KEY in session:
#                 messages = session[CHAT_HISTORY_KEY]
#                 messages.append(error_msg)
#                 session[CHAT_HISTORY_KEY] = messages
            
#             return Div(
#                 ChatMessage(error_msg),
#                 NotStr("""
#                 <script>
#                     document.querySelector('#chatlist').scrollTop = document.querySelector('#chatlist').scrollHeight;
#                     document.querySelector('#upload-area').classList.add('hidden');
#                 </script>
#                 """)
#             )