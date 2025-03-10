from fasthtml.common import *
from .progress import create_progress_indicator  # Add this import
import os
import base64
from pathlib import Path
import datetime
import tempfile
import zipfile
import io
import json


def create_recipe_carousel(recipe_templates):
    """Create a carousel of recipe template cards"""
    return Div(
        # Carousel styles
        Style("""
            .recipe-carousel {
                position: relative;
                width: 100%;
                padding: 0 40px;
            }
            .carousel-container {
                overflow-x: auto;
                scroll-behavior: smooth;
                scrollbar-width: none; /* Firefox */
                -ms-overflow-style: none; /* IE/Edge */
                padding: 10px 0;
                display: flex;
                gap: 15px;
            }
            .carousel-container::-webkit-scrollbar {
                display: none; /* Chrome/Safari/Opera */
            }
            .recipe-card {
                flex: 0 0 280px;
                height: 180px;
                background-color: #2d3748;
                border-radius: 8px;
                border: 2px solid #4a5568;
                padding: 15px;
                transition: all 0.3s ease;
                cursor: pointer;
                display: flex;
                flex-direction: column;
            }
            .recipe-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
                border-color: #63b3ed;
            }
            .recipe-card.selected {
                border-color: #38a169;
                box-shadow: 0 0 0 2px #38a169;
            }
            .recipe-title {
                font-weight: 600;
                font-size: 1.1rem;
                margin-bottom: 8px;
                color: #e2e8f0;
            }
            .recipe-preview {
                font-size: 0.9rem;
                color: #a0aec0;
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 4;
                -webkit-box-orient: vertical;
                flex-grow: 1;
            }
            .carousel-button {
                position: absolute;
                top: 50%;
                transform: translateY(-50%);
                background-color: #2d3748;
                color: white;
                border: none;
                width: 36px;
                height: 36px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                z-index: 10;
                opacity: 0.8;
                transition: opacity 0.2s;
            }
            .carousel-button:hover {
                opacity: 1;
            }
            .prev-button {
                left: 0;
            }
            .next-button {
                right: 0;
            }
            .recipe-tag {
                display: inline-block;
                background-color: #1a202c;
                color: #a0aec0;
                font-size: 0.7rem;
                padding: 2px 8px;
                border-radius: 12px;
                margin-top: auto;
                align-self: flex-start;
            }
        """),
        
        # Carousel HTML structure
        H3("Recipe Templates", cls="text-lg font-bold mb-4"),
        Div(
            # Previous button
            Button(
                Svg(
                    Path(d="M15 19l-7-7 7-7"),
                    fill="none",
                    stroke="currentColor",
                    stroke_width="2",
                    stroke_linecap="round",
                    stroke_linejoin="round",
                    viewBox="0 0 24 24",
                    width="20",
                    height="20"
                ),
                id="prev-button",
                cls="carousel-button prev-button",
                type="button",
                onclick="document.getElementById('carousel-container').scrollBy({left: -300, behavior: 'smooth'})"
            ),
            
            # Recipe cards container
            Div(
                *[Div(
                    Div(f"Recipe {i+1}", cls="recipe-title"),
                    Div(recipe[:120] + "..." if len(recipe) > 120 else recipe, cls="recipe-preview"),
                    Div("Template", cls="recipe-tag"),
                    id=f"recipe-{i+1}",
                    cls="recipe-card",
                    # Use HTML attributes with proper JSON encoding of the recipe text
                    **{"data-recipe-key": str(i+1), 
                    "data-recipe-text": recipe,
                    "onclick": f"window.handleRecipeClick(this)"}
                ) for i, recipe in enumerate(recipe_templates.values())],
                id="carousel-container",
                cls="carousel-container"
            ),
            
            # Next button
            Button(
                Svg(
                    Path(d="M9 5l7 7-7 7"),
                    fill="none",
                    stroke="currentColor",
                    stroke_width="2",
                    stroke_linecap="round",
                    stroke_linejoin="round",
                    viewBox="0 0 24 24",
                    width="20",
                    height="20"
                ),
                id="next-button",
                cls="carousel-button next-button",
                type="button",
                onclick="document.getElementById('carousel-container').scrollBy({left: 300, behavior: 'smooth'})"
            ),
            
            cls="recipe-carousel mb-8"
        ),
        
    # JavaScript for recipe selection - Replace with a simpler approach
        NotStr("""
        <script>
            // Global handler function
            window.handleRecipeClick = function(element) {
                const recipeKey = element.getAttribute('data-recipe-key');
                const recipeText = element.getAttribute('data-recipe-text');
                
                console.log("Recipe clicked:", recipeKey);
                
                // Find and update the textarea
                const textarea = document.getElementById('selected-recipe');
                if (textarea) {
                    textarea.value = recipeText;
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
        </script>
        """),
        id="recipe-section"
    )
    
def create_lea_chatbot(api_key=None, base_template="", recipe_templates=None):
    """Create a chat interface with Tailwind CSS and DaisyUI styling"""
    return Div(
        # Load Tailwind and DaisyUI
        Script(src="https://cdn.tailwindcss.com"),
        Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css"),
        
        # Add styling with dark theme
        Style("""
            body {
                background-color: #121212;
                color: #e0e0e0;
            }
            .chat-container {
                height: 65vh;
                overflow-y: auto;
                padding: 1rem;
                margin-bottom: 1rem;
                border: 1px solid #2d3748;
                border-radius: 0.5rem;
                background-color: #1a1a1a;
                color: #e0e0e0;
            }
            .card {
                background-color: #1a1a1a;
                color: #e0e0e0;
                border: 1px solid #2d3748;
            }
            .chat-form {
                display: flex;
                gap: 0.5rem;
            }
            .typing-indicator {
                display: flex;
                align-items: center;
                margin-top: 8px;
            }
            .typing-indicator span {
                height: 8px;
                width: 8px;
                margin: 0 1px;
                background-color: #9ca3af;
                border-radius: 50%;
                display: inline-block;
                animation: blink 1.4s infinite both;
            }
            .typing-indicator span:nth-child(2) {
                animation-delay: 0.2s;
            }
            .typing-indicator span:nth-child(3) {
                animation-delay: 0.4s;
            }
            @keyframes blink {
                0% { opacity: 0.1; }
                20% { opacity: 1; }
                100% { opacity: 0.1; }
            }
            input, textarea, select {
                background-color: #2d3748 !important;
                color: #e0e0e0 !important;
                border-color: #4a5568 !important;
            }
            button {
                background-color: #3182ce !important;
                color: white !important;
            }
            button:hover {
                background-color: #2c5282 !important;
            }
            .chat-start .chat-bubble {
                background-color: #fc37a0 !important;
                color: white !important;
            }
            .chat-end .chat-bubble {
                background-color: #4361ee !important;
                color: white !important;
            }
            .chat-header, .chat-footer {
                color: #a0aec0 !important;
            }
        """),
        
            create_recipe_carousel(recipe_templates) if recipe_templates else Div(),

                    # Recipe Templates Section
            Div(
                H3("Recipe Templates", cls="text-lg font-bold mb-4"),
                Div(
                    # Recipe cards will be generated here
                    id="recipe-templates",
                    cls="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"
                ),
                
                # Selected Recipe Display
                Div(
                    H4("Selected Recipe", cls="text-md font-semibold mb-2"),
                    Textarea(
                        id="selected-recipe",
                        name="selected_recipe",
                        rows=5,
                        placeholder="Select a recipe template to view here...",
                        cls="w-full p-2 mb-2"
                    ),
                    Button(
                        "Save as Prompt",
                        id="save-recipe-btn",
                        hx_post="/api/lea/save-recipe",
                        hx_include="#selected-recipe",
                        hx_swap="none",
                        cls="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                    ),
                    Div(
                        Button(
                            "View Current Prompt",
                            hx_get="/api/lea/get-current-prompt",
                            hx_target="#current-prompt-display",
                            cls="text-xs bg-blue-600 text-white py-1 px-2 rounded"
                        ),
                        Div(id="current-prompt-display", cls="mt-2 text-sm"),
                        cls="mt-2"
                    ),
                    id="recipe-display",
                    cls="mb-6"
                ),
                
                # Current Prompt Indicator
                Div(
                    P("System prompt is set to base template only", id="prompt-status", cls="text-sm text-green-500"),
                    Button(
                        "Reset to Base Template",
                        hx_post="/api/lea/reset-prompt",
                        cls="ml-2 text-xs bg-red-600 text-white py-1 px-2 rounded"
                    ),
                    cls="mb-4 flex items-center"
                ),
                
                # Script to handle recipe template selection
                NotStr("""
                <script>
                    function selectRecipe(recipeName, recipeText) {
                        document.getElementById('selected-recipe').value = recipeText;
                        document.getElementById('selected-recipe').setAttribute('data-recipe-name', recipeName);
                        
                        // Highlight selected recipe
                        document.querySelectorAll('.recipe-card').forEach(card => {
                            card.classList.remove('border-green-500');
                            card.classList.add('border-gray-700');
                        });
                        document.getElementById('recipe-' + recipeName).classList.remove('border-gray-700');
                        document.getElementById('recipe-' + recipeName).classList.add('border-green-500');
                    }
                </script>
                """),
                
                cls="mb-4"
            ),
            
            Card(
                # Add a script to ensure dark mode applies to the whole page
                Script("""
                    document.body.style.backgroundColor = '#121212';
                    document.body.style.color = '#e0e0e0';
                """),
            # Chat header
            H2("LEA AI Assistant", cls="text-xl font-bold mb-4"),
            
            # Chat container with message history
            Div(
                # Messages will be loaded here by HTMX
                id="chatlist",
                cls="chat-container",
                hx_get="/api/lea/get-messages",
                hx_trigger="load"
            ),
            
            # Loading indicator
            Div(
                P("LEA is thinking...", cls="mr-2"),
                Div(
                    Span(), Span(), Span(),
                    cls="typing-indicator"
                ),
                id="typing-indicator",
                cls="htmx-indicator flex items-center text-sm text-gray-500 my-2"
            ),
            
            # Chat input form
            Form(
                Div(
                    # Hidden API key field
                    Input(id='api_key', name='api_key', type='hidden', value=api_key),
                    
                    # Message input
                    Input(
                        id="user-message", 
                        name="message", 
                        placeholder="Type your message here...",
                        cls="flex-grow p-2 border rounded-l focus:outline-none focus:ring-2 focus:ring-blue-500",
                        hx_on="keydown[event.key=='Enter' && !event.shiftKey]: htmx.trigger('#send-button', 'click'); event.preventDefault();"
                    ),
                    
                    # Send button
                    Button(
                        "Send",
                        id="send-button",
                        type="button",
                        hx_post="/api/lea/send-message",
                        hx_include="closest form",
                        hx_target="#chatlist",
                        hx_swap="beforeend",
                        hx_indicator="#typing-indicator",
                        cls="p-2 bg-blue-500 text-white rounded-r hover:bg-blue-600"
                    ),
                    
                    # File upload button (optional)
                    Button(
                        Div(
                            Svg(
                                Path(d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"),
                                viewBox="0 0 24 24",
                                fill="none",
                                stroke="currentColor",
                                stroke_width="2",
                                stroke_linecap="round",
                                stroke_linejoin="round",
                                width="20",
                                height="20"
                            ),
                            cls="mr-1"
                        ),
                        id="upload-button",
                        type="button",
                        hx_get="/api/lea/upload-form",
                        hx_target="#upload-area",
                        cls="ml-2 p-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 flex items-center"
                    ),
                    
                    cls="chat-form"
                ),
                
                # Upload area (hidden by default, shown when upload button is clicked)
                Div(id="upload-area", cls="mt-2 hidden"),
                
                # Model selection
                Div(
                    Label("Model:", cls="mr-2"),
                    Select(
                        Option("GPT-4o", value="gpt-4o", selected="selected"),
                        Option("GPT-4o Mini", value="gpt-4o-mini"),
                        Option("GPT-3.5 Turbo", value="gpt-3.5-turbo"),
                        name="model",
                        id="model-selector",
                        cls="p-1 border rounded text-sm"
                    ),
                    cls="flex items-center mt-2 text-sm"
                ),
                
                id="chat-form",
                cls="mt-4"
            ),
            
            # Clear chat button
            Button(
                "Clear Chat",
                hx_post="/api/lea/clear-chat",
                hx_target="#chatlist",
                cls="mt-2 text-sm text-gray-500 hover:text-gray-700"
            ),
            
            cls="p-6 max-w-4xl mx-auto"
        )
    )


def ChatMessage(msg):
    """Helper function to create a chat message div with the appropriate styling"""
    is_user = msg['role'] == 'user'
    bubble_class = "chat-bubble" if is_user else "chat-bubble"
    position_class = "chat-end" if is_user else "chat-start"
    
    # Format timestamp if available
    timestamp = ""
    if 'timestamp' in msg and msg['timestamp']:
        time_obj = datetime.datetime.strptime(msg['timestamp'], "%Y-%m-%d %H:%M:%S") if isinstance(msg['timestamp'], str) else msg['timestamp']
        timestamp = time_obj.strftime("%H:%M")
    
    return Div(
        # Avatar (optional)
        Div(
            Div(
                Div(
                    Img(alt="Avatar", src=f"https://ui-avatars.com/api/?name={'You' if is_user else 'LEA'}&background={'0D8ABC' if is_user else '7A3E65'}&color=fff"),
                    cls="w-10 rounded-full"
                ),
                cls="chat-image avatar"
            ) if msg.get('show_avatar', True) else "",
            
            # Header with role name and timestamp
            Div(
                f"{'You' if is_user else 'LEA'}",
                Time(timestamp, cls="text-xs opacity-50") if timestamp else "",
                cls="chat-header"
            ),
            
            # Message content
            Div(msg['content'], cls=f"chat-bubble {bubble_class}"),
            
            # Footer (optional)
            Div(
                "Sent" if is_user else "",
                cls="chat-footer opacity-50"
            ) if msg.get('show_footer', False) else "",
            
            cls=f"chat {position_class}"
        )
    )