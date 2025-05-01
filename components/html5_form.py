from fasthtml.common import *
import os
import base64
from io import BytesIO
from PIL import Image
import yaml  # Add import for yaml

def create_recipe_carousel(recipe_templates):
    """Create a carousel of recipe template cards"""
    return Div(
        # Carousel styles
        Style("""
            .recipe-carousel {
                position: relative;
                width: 100%;
                padding: 0 40px;
                margin-bottom: 20px;
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
                color: #ffff00;
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
                font-weight: bold;
                font-size: 18px;
                line-height: 1;
                padding: 0;
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
            .carousel-button-content {
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
                width: 100%;
                line-height: 1;
                position: relative;
                top: -1px; /* Fine-tune vertical alignment */
            }
            .carousel-arrow {
                margin: 0 2px;
                display: inline-block;
                position: relative;
                top: 1px; /* Fine-tune vertical position */
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
        H3("HTML5 Template Library", cls="text-lg font-bold mb-4 text-white"),
        P("To start generating an interactive, scroll through a recipe and select the one that closely matched your envision interactive. In the recipe, fill in all the necessary information within the curly brackets and add additional instructions. If there are any unused instructions or optional fields that are not needed, remove them.", cls="text-sm text-gray-400 mb-4"),
        Div(
            # Previous button
            Button(
                Div(
                    Span("←", cls="carousel-arrow"),  # Changed class for better alignment
                    cls="carousel-button-content"
                ),
                id="prev-button",
                cls="carousel-button prev-button",
                type="button",
                onclick="document.getElementById('carousel-container').scrollBy({left: -300, behavior: 'smooth'})"
            ),
            
            # Recipe cards container
            Div(
                *[Div(
                    Div(recipe_name.replace('_template', '').replace('_', ' ').title(), cls="recipe-title"),
                    Div(recipe[:120] + "..." if len(recipe) > 120 else recipe, cls="recipe-preview"),
                    Div("Template", cls="recipe-tag"),
                    id=f"recipe-{i+1}",
                    cls="recipe-card",
                    # Use HTML attributes with proper JSON encoding of the recipe text
                    **{"data-recipe-key": recipe_name, 
                    "data-recipe-text": recipe,
                    "onclick": f"window.handleRecipeClick(this)"}
                ) for i, (recipe_name, recipe) in enumerate(recipe_templates.items())],
                id="carousel-container",
                cls="carousel-container"
            ),
            
            # Next button
            Button(
                Div(
                    Span("→", cls="carousel-arrow"),  # Changed class for better alignment
                    cls="carousel-button-content"
                ),
                id="next-button",
                cls="carousel-button next-button",
                type="button",
                onclick="document.getElementById('carousel-container').scrollBy({left: 300, behavior: 'smooth'})"
            ),
            
            cls="recipe-carousel mb-4"
        ),
        
        # JavaScript for recipe selection
        NotStr("""
        <script>
            // Global handler function
            window.handleRecipeClick = function(element) {
                const recipeKey = element.getAttribute('data-recipe-key');
                const recipeText = element.getAttribute('data-recipe-text');
                
                console.log("Recipe clicked:", recipeKey);
                
                // Find and update the textarea - first try TinyMCE, then fallback to regular textarea
                const textarea = document.getElementById('prompt');
                let updated = false;
                
                // Try to update TinyMCE if it's initialized
                if (typeof tinymce !== 'undefined' && tinymce.get('prompt')) {
                    tinymce.get('prompt').setContent(recipeText);
                    updated = true;
                    console.log("Updated TinyMCE with recipe text");
                } 
                // Fallback to regular textarea
                else if (textarea) {
                    textarea.value = recipeText;
                    updated = true;
                    console.log("Updated regular textarea with recipe text");
                } else {
                    console.error("Could not find prompt textarea");
                }
                
                // Highlight the selected card
                document.querySelectorAll('.recipe-card').forEach(card => {
                    card.classList.remove('selected');
                });
                element.classList.add('selected');
                
                // Show a confirmation message
                if (updated) {
                    const confirmationEl = document.createElement('div');
                    confirmationEl.textContent = 'Template applied! You can now edit it.';
                    confirmationEl.className = 'text-sm text-green-500 mt-2 mb-2 text-center';
                    
                    // Insert the confirmation before the prompt
                    const promptContainer = textarea.closest('div');
                    
                    // Remove any existing confirmation
                    const existingConfirmation = document.getElementById('template-confirmation');
                    if (existingConfirmation) {
                        existingConfirmation.remove();
                    }
                    
                    // Add the new confirmation
                    confirmationEl.id = 'template-confirmation';
                    if (promptContainer) {
                        promptContainer.insertBefore(confirmationEl, textarea);
                        
                        // Auto-remove the confirmation after 3 seconds
                        setTimeout(() => {
                            confirmationEl.style.opacity = '0';
                            confirmationEl.style.transition = 'opacity 0.5s';
                            setTimeout(() => confirmationEl.remove(), 500);
                        }, 3000);
                    }
                }
            };
        </script>
        """),
        id="recipe-section"
    )

def create_file_uploader(index=0, tab_prefix="gen"):
    """Create a file uploader that supports both direct file upload and base64 data"""
    return Div(
        # Hidden input for storing base64 data
        Input(type="hidden", id=f"{tab_prefix}-image-data-{index}", name=f"image-data-{index}"),
        
        # Title for each uploader
        H4(f"Image {index+1}", cls="text-lg font-semibold mb-2 text-yellow-300"),
        
        # The file input with improved styling
        Label(
            Input(
                type="file", 
                id=f"{tab_prefix}-image-upload-{index}", 
                name=f"image-upload-{index}",
                accept="image/*",
                cls="block w-full text-sm text-gray-400 bg-gray-700 rounded cursor-pointer mb-2 p-2 border border-gray-600 hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            ),
            cls="block w-full mb-3"
        ),
        
        # Preview container with improved styling
        Div(
            cls="image-preview hidden w-full h-32 bg-gray-800 rounded-lg flex items-center justify-center overflow-hidden mb-3 border border-gray-600",
            id=f"{tab_prefix}-preview-container-{index}"
        ),
        
        # JavaScript to handle immediate preview and store base64 data
        # Enhanced to add visual feedback when image is loaded
        Script(f"""
        document.getElementById('{tab_prefix}-image-upload-{index}').addEventListener('change', function(e) {{
            const file = e.target.files[0];
            const container = document.getElementById('{tab_prefix}-uploader-container-{index}');
            
            if (file) {{
                const reader = new FileReader();
                
                reader.onload = function(e) {{
                    // Show preview
                    const previewContainer = document.getElementById('{tab_prefix}-preview-container-{index}');
                    previewContainer.innerHTML = `<img src="${{e.target.result}}" class="max-h-full max-w-full object-contain" />`;
                    previewContainer.classList.remove('hidden');
                    
                    // Store base64 data in the hidden input
                    const base64Data = e.target.result.split(',')[1];
                    document.getElementById('{tab_prefix}-image-data-{index}').value = base64Data;
                    
                    // Add visual indication that this uploader has an image
                    container.classList.add('has-image');
                }};
                
                reader.readAsDataURL(file);
            }} else {{
                // Remove visual indication if no file is selected
                container.classList.remove('has-image');
                
                // Hide preview container
                const previewContainer = document.getElementById('{tab_prefix}-preview-container-{index}');
                previewContainer.innerHTML = '';
                previewContainer.classList.add('hidden');
                
                // Clear hidden input
                document.getElementById('{tab_prefix}-image-data-{index}').value = '';
            }}
        }});
        """),
        
        cls="file-uploader-container mb-6 p-4 border-2 border-gray-700 rounded-lg bg-gray-900 transition-all hover:shadow-md",
        id=f"{tab_prefix}-uploader-container-{index}"
    )

def create_multiple_uploaders(count=5, tab_prefix="gen"):
    """Create multiple simple file uploaders"""
    uploaders = [create_file_uploader(i, tab_prefix) for i in range(count)]
    
    # Create the "Remove All Images" button container with enhanced styling
    clear_button_container = Div(
        Button(
            Div(
                Svg(
                    Path(d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z", fill="currentColor"),
                    viewBox="0 0 24 24", width="20", height="20"
                ),
                Span("Remove All Images", cls="ml-2"),
                cls="flex items-center justify-center"
            ),
            id=f"{tab_prefix}-clear-all-images-button",
            type="button",
            cls="w-full py-2 px-4 bg-red-500 text-white rounded hover:bg-red-600"
        ),
        # JavaScript to handle clearing all images
        Script(f"""
        document.getElementById('{tab_prefix}-clear-all-images-button').addEventListener('click', function() {{
            // Clear all file inputs        
            for (let i = 0; i < 5; i++) {{
                const fileInput = document.getElementById(`{tab_prefix}-image-upload-${{i}}`);
                if (fileInput) {{
                    fileInput.value = '';
                }}
            }}   

            // Clear all hidden base64 inputs
            for (let i = 0; i < 5; i++) {{
                const base64Input = document.getElementById(`{tab_prefix}-image-data-${{i}}`);
                if (base64Input) {{
                    base64Input.value = '';
                }}                   
            }}

            // Hide all preview containers
            for (let i = 0; i < 5; i++) {{
                const previewContainer = document.getElementById(`{tab_prefix}-preview-container-${{i}}`);
                if (previewContainer) {{
                    previewContainer.innerHTML = '';    
                    previewContainer.classList.add('hidden');
                }}
            }}
        }});
        """),
        cls="mt-4 p-2 border border-gray-700 rounded bg-gray-800"
    )   

    return Div(
        Div(
            *uploaders,
            cls="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4"
        ),  
        clear_button_container
    )   


def create_html5_form(api_key=None):
    """Create the HTML5 editor form with simplified image uploaders"""
    # Load templates from config.yaml
    try:
        with open('config.yaml', 'r') as file:
            config = yaml.safe_load(file)
            recipe_templates = {k: v for k, v in config.get('templates', {}).items()}
    except Exception as e:
        print(f"Error loading config.yaml: {e}")
        recipe_templates = {}
    
    return Div(
        # Add styles for the preview, editors, tabs, etc.
        Style("""
            body {
                background-color: #121212;
                color: #e0e0e0;
            }

            .preview-frame {
                width: 100%;
                height: 700px;
                border: 1px solid #333;
                border-radius: 4px;
                background-color: #333333 !important;
                margin-bottom: 20px;
                overflow: hidden;
            }
            
            .preview-frame iframe {
                width: 100%;
                height: 100%;
                border: none;
                background-color: #333333 !important;
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
            
            /* Iterative mode toggle styles */
            .iterative-container {
                position: relative;
                margin-bottom: 16px;
                padding: 12px;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                background-color: #1e1e1e;
            }

            .iterative-container:hover {
                border-color: #4a90e2;
            }

            .iterative-badge {
                position: absolute;
                top: -10px;
                right: 10px;
                padding: 2px 8px;
                background-color: #4a90e2;
                color: white;
                font-size: 0.75rem;
                border-radius: 10px;
                z-index: 10;
            }

            /* Pulse animation for active iterative mode */
            @keyframes pulse-border {
                0% {
                    border-color: #4a90e2;
                    box-shadow: 0 0 0 0 rgba(74, 144, 226, 0.4);
                }
                70% {
                    border-color: #4a90e2;
                    box-shadow: 0 0 0 10px rgba(74, 144, 226, 0);
                }
                100% {
                    border-color: #4a90e2;
                    box-shadow: 0 0 0 0 rgba(74, 144, 226, 0);
                }
            }

            .iterative-active {
                animation: pulse-border 2s infinite;
            }
                                     
            /* File uploader styling */
            .file-uploader-container {
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 10px;
                background-color: #1e1e1e;
                transition: all 0.3s ease;
            }
            
            .file-uploader-container:hover {
                border-color: #4a90e2;
                box-shadow: 0 0 10px rgba(74, 144, 226, 0.3);
            }
            
            .file-uploader-container.has-image {
                border-color: #4caf50;
            }
            /* Animation for the download container */
            @keyframes pulse {
                0% {
                    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.4);
                }
                70% {
                    box-shadow: 0 0 0 10px rgba(74, 222, 128, 0);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(74, 222, 128, 0);
                }
            }

            .animate-pulse {
                animation: pulse 1s 2;
            }

            /* Styling for the zip download container */
            #zip-download-container {
                transition: all 0.3s ease;
                margin-top: 1rem;
            }

            #zip-download-container:not(.hidden) {
                display: block;
                margin-top: 1rem;
            }

            .download-button {
                transition: all 0.2s ease;
            }

            .download-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }

            /* Action button styling */
            .action-button {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                padding: 0.625rem 1.25rem;
                color: white;
                font-weight: 500;
                border-radius: 0.5rem;
                border: none;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                min-width: 140px;
                position: relative;
                overflow: hidden;
            }
            
            .action-button::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(255, 255, 255, 0);
                transition: background-color 0.3s ease;
            }
            
            .action-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            
            .action-button:hover::after {
                background-color: rgba(255, 255, 255, 0.1);
            }
            
            .action-button:active {
                transform: translateY(1px);
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }
            
            .action-button:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }
            
            .action-button:disabled:hover {
                transform: none;
                box-shadow: none;
            }
            
            .action-button:disabled:hover::after {
                background-color: rgba(255, 255, 255, 0);
            }
            
            /* Custom button container styling */
            #editor-buttons-container {
                background: linear-gradient(to right, #1a1c2e, #2d3748);
                border: 2px solid #4299e1;
                border-radius: 16px;
                padding: 20px;
                margin: 20px auto;
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
                transition: all 0.5s ease;
            }
            
            #editor-buttons-container:hover {
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 10px 10px -5px rgba(0, 0, 0, 0.1);
                border-color: #63b3ed;
            }
            
            /* Custom button styling */
            .editor-action-button {
                font-size: 1.125rem;
                font-weight: 600;
                transition: all 0.3s ease;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .editor-action-button:hover {
                transform: translateY(-3px) scale(1.02);
            }
            
            .editor-action-button:active {
                transform: translateY(1px);
            }
            
            /* Button highlight effect */
            .editor-action-button::before {
                content: '';
                position: absolute;
                top: -50%;
                left: -50%;
                width: 200%;
                height: 200%;
                background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 70%);
                transform: scale(0);
                opacity: 0;
                transition: transform 0.6s, opacity 0.6s;
            }
            
            .editor-action-button:hover::before {
                transform: scale(1);
                opacity: 1;
            }

            /* Make buttons more responsive on small screens */
            @media (max-width: 640px) {
                #editor-buttons {
                    flex-direction: column;
                    align-items: stretch;
                    gap: 0.75rem;
                }
                
                .action-button {
                    width: 100%;
                    margin-right: 0;
                    margin-bottom: 0.5rem;
                }
                
                #dynamic-buttons {
                    order: -1;
                    margin-bottom: 0.5rem;
                    width: 100%;
                }
            }
            
            /* Medium screens - 2 buttons per row */
            @media (min-width: 641px) and (max-width: 1024px) {
                #editor-buttons {
                    justify-content: flex-start;
                }
                
                .action-button {
                    flex: 0 0 calc(50% - 0.5rem);
                    margin-right: 0;
                }
                
                #dynamic-buttons {
                    flex: 0 0 100%;
                    order: -1;
                    margin-bottom: 0.75rem;
                }
            }
            
            /* Tab styling */
            .tab-header {
                display: flex;
                border-bottom: 1px solid #2d3748;
                background-color: #1a202c;
                border-top-left-radius: 0.5rem;
                border-top-right-radius: 0.5rem;
                overflow: hidden;
            }
            
            .tab {
                padding: 0.75rem 1.25rem;
                background: none;
                border: none;
                color: #a0aec0;
                font-size: 0.875rem;
                font-weight: 500;
                cursor: pointer;
                border-bottom: 2px solid transparent;
                transition: all 0.2s ease;
                flex: 1;
                text-align: center;
            }
            
            .tab:hover {
                color: #fff;
                background-color: #2d3748;
            }
            
            .tab.active {
                color: #fff;
                border-bottom: 2px solid #48bb78;
                background-color: #2d3748;
                position: relative;
            }
            
            .tab.active::after {
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 2px;
                background: linear-gradient(to right, #48bb78, #68d391);
            }
            
            /* Main tabs styling */
            .main-tab-header {
                display: flex;
                background-color: #2d3748;
                border-radius: 0.5rem 0.5rem 0 0;
                overflow: hidden;
                margin-bottom: 0;
            }
            
            .main-tab {
                padding: 1rem 2rem;
                background: none;
                border: none;
                color: #a0aec0;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                border-bottom: 3px solid transparent;
                transition: all 0.3s ease;
                flex: 1;
                text-align: center;
            }
            
            .main-tab:hover {
                color: #fff;
                background-color: #4a5568;
            }
            
            .main-tab.active {
                color: #48bb78;
                border-bottom: 3px solid #48bb78;
                background-color: #1a202c;
            }
            
            .main-tab-panel {
                display: none;
                padding: 1.5rem;
                background-color: #1a202c;
                border-radius: 0 0 0.5rem 0.5rem;
                min-height: 800px; /* Set a minimum height to prevent resizing */
                width: 100%; /* Ensure consistent width */
                box-sizing: border-box; /* Include padding in width calculation */
            }
            
            .main-tab-panel.active {
                display: block;
            }

            /* Form consistency */
            #generation-form, #refinement-form, #html5-form {
                width: 100%;
                max-width: 100%;
                box-sizing: border-box;
            }
            
            /* Tab panel container */
            .tab-container {
                width: 100%;
                max-width: 100%;
                margin: 0 auto;
                box-sizing: border-box;
            }
            
            /* Force consistent form layout */
            .main-tab-panel form {
                display: flex;
                flex-direction: column;
                width: 100%;
            }
        """),
        
        H2("HTML5 Interactive Editor", cls="text-center text-xl font-bold mb-4 text-white drop-shadow-md editor-title bright-white"),
        
        # Preview area with increased height
        Div(
            H3("Preview", cls="text-lg font-semibold mb-2 text-white preview-title bright-white"),
            Div(
                Div("Your HTML5 content will appear here",
                    cls="flex items-center justify-center h-full text-gray-600 preview-text"),
                id="preview-container",
                cls="preview-frame",
                hx_swap="outerHTML",
                style="background-color: #333333 !important; height: 700px;"
            ),
            cls="mb-6 preview-section"
        ),

        
        # Main Tabs Container
        Card(
            # Main Tab Navigation
            Div(
                Button("Generation", 
                       id="generation-tab", 
                       type="button", 
                       cls="main-tab active", 
                       onclick="switchMainTab('generation', event)"),
                Button("Refinement", 
                       id="refinement-tab", 
                       type="button", 
                       cls="main-tab", 
                       onclick="switchMainTab('refinement', event)"),
                cls="main-tab-header"
            ),
            
            # Fixed width container for the tab panels
            Div(
                # Generation Tab Panel
                Div(
                    Form(
                        # Hidden API Key
                        Input(id='api_key', name='api_key',
                            value=api_key,
                            type='hidden'),
                        
                        # Model selector
                        Div(
                            Label("Model:", 
                                 cls="block mb-2 text-white", 
                                 style="color: #ffffff !important; font-weight: bold;"),
                            Select(
                                Option("Claude 3.7 Sonnet", value="claude-3-7-sonnet-20250219"),
                                Option("Gemini 2.5 Pro", value="gemini-2.5-pro-preview-03-25"),
                                Option("GPT-o3", value="o3-2025-04-16"),
                                Option("GPT-4.5", value="gpt-4.5-preview"),
                                Option("GPT-4o", value="gpt-4o"),
                                Option("GPT-4o Mini", value="gpt-4o-mini"),
                                Option("GPT-o1", value="o1"),
                                Option("GPT-o3-mini", value="o3-mini"),
                                Option("Claude 3.5 Haiku", value="claude-3-5-haiku-20241022"),
                                id="model-selector",
                                name="model",
                                cls="w-full p-2 border rounded"
                            ),
                            cls="mb-4"
                        ),
                        
                        # Add recipe carousel
                        create_recipe_carousel(recipe_templates) if recipe_templates else Div(),
                        
                        # Rich Text Editor for prompt
                        Div(
                            Label("HTML5 Prompt:", 
                                 cls="block mb-2 text-white text-xl", 
                                 style="color: #ffffff !important; font-weight: bold;"),
                            # Basic textarea for initial render and as fallback
                            Textarea("", 
                                  id='prompt', 
                                  name='prompt', 
                                  placeholder='This simulation/game/interactive graph should have the following aspects:\nTopic...\nDemonstrates...\nDisplay...\n(Primary) Bright and colourful buttons',
                                  rows=32,
                                  cls="w-full p-2 border rounded"),
                            cls="mb-4"
                        ),
                        
                        # File upload section - simplified to basic file inputs
                        Div(
                            H3("Reference Images (Up to 5):", cls="block text-lg mb-2 text-blue-500"),
                            P("Upload up to 5 reference images to help generate the interactive. Note that reference images will not appear or used as objects in the interactive. Example, you can upload what the interactive may look like at different stages of the simulation.", 
                              cls="text-sm text-gray-400 mb-4"),
                            
                            create_multiple_uploaders(5, "gen"),
                            
                            cls="mb-6 p-4 border border-gray-700 rounded bg-gray-900"
                        ),
                        
                        # Generate button
                        Button("Generate", 
                               type='submit',
                               hx_post="/api/html5/generate-code",
                               hx_target="#code-editors-container",
                               hx_indicator="#loading-indicator",
                               cls="w-full py-3 bg-gradient-to-r from-green-600 to-green-500 text-white rounded-lg hover:shadow-lg transition-all duration-300 font-medium"),
                        
                        id="html5-form",
                        enctype="multipart/form-data",
                        cls="space-y-4",
                    ),
                    id="generation-panel",
                    cls="main-tab-panel active"
                ),
                
                # Iteration Tab Panel (empty for now)
                Div(
                    Form(
                        # Hidden API Key
                        Input(id='api_key_iteration', name='api_key',
                            value=api_key,
                            type='hidden'),
                        
                        # Model selector
                        Div(
                            Label("Model:", 
                                 cls="block mb-2 text-white", 
                                 style="color: #ffffff !important; font-weight: bold;"),
                            Select(
                                Option("Claude 3.7 Sonnet", value="claude-3-7-sonnet-20250219"),
                                Option("GPT-o3", value="o3-2025-04-16"),
                                Option("Gemini 2.5 Pro", value="gemini-2.5-pro-preview-03-25"),
                                Option("GPT-4.5", value="gpt-4.5-preview"),
                                Option("GPT-4o", value="gpt-4o"),
                                Option("GPT-4o Mini", value="gpt-4o-mini"),
                                Option("GPT-o1", value="o1"),
                                Option("GPT-o3-mini", value="o3-mini"),
                                Option("Claude 3.5 Haiku", value="claude-3-5-haiku-20241022"),
                                id="model-selector-iteration",
                                name="model",
                                cls="w-full p-2 border rounded"
                            ),
                            cls="mb-4"
                        ),
                        
                        # Help section for refinement
                        Div(
                            Details(
                                Summary(
                                    Div(
                                        "How to Use Refinement (Click to Expand)",
                                        Svg(
                                            Path(d="M19 9l-7 7-7-7", stroke="currentColor", stroke_width="2", fill="none"),
                                            viewBox="0 0 24 24", 
                                            width="16", 
                                            height="16",
                                            cls="ml-2"
                                        ),
                                        cls="flex items-center"
                                    ),
                                    cls="cursor-pointer font-semibold text-blue-400 hover:text-blue-300 border-2 border-blue-400 p-2 rounded hover:bg-gray-800 flex items-center justify-between w-full"
                                ),
                                Div(
                                    H4("Effective Refinement Tips:", cls="text-blue-300 text-lg mt-2 mb-3"),
                                    Ul(
                                        Li("Focus on one change at a time for best results", cls="mb-2"),
                                        Li("Use the 'Undo' button if you don't like a result", cls="mb-2"),
                                        Li("Create a ZIP download after each satisfactory iteration", cls="mb-2"),
                                        Li("Be specific about what to change and what to keep the same", cls="mb-2"),
                                        Li("Use the 'Example Refinements' button in the toolbar for templates", cls="mb-2"),
                                        cls="list-disc ml-6 text-gray-300"
                                    ),
                                    H4("Example Scenarios:", cls="text-blue-300 text-lg mt-4 mb-3"),
                                    Div(
                                        Pre("Add a new variable called x in the drop down list and keep the rest of the code the same", 
                                            cls="bg-gray-900 p-2 rounded text-sm mb-2"),
                                        Pre("Change the font of the text to black in the table and keep the rest of the code the same", 
                                            cls="bg-gray-900 p-2 rounded text-sm mb-2"),
                                        Pre("Remove the object [name] from the simulation and adjust the necessary code", 
                                            cls="bg-gray-900 p-2 rounded text-sm mb-2"),
                                        Pre("Create an object [name] that can [behavior] and adjust the necessary code", 
                                            cls="bg-gray-900 p-2 rounded text-sm"),
                                        cls="mb-3"
                                    ),
                                    cls="p-3 bg-gray-800 rounded-b"
                                ),
                                cls="mb-4 border border-gray-600 rounded"
                            ),
                            cls="mb-4"
                        ),
                        
                        # Rich Text Editor for refinement prompt (half the height)
                        Div(
                            # Refinement History expandable tab
                            Details(
                                Summary(
                                    Div(
                                        "Refinement History (Click to Expand)",
                                        Svg(
                                            Path(d="M19 9l-7 7-7-7", stroke="currentColor", stroke_width="2", fill="none"),
                                            viewBox="0 0 24 24", 
                                            width="16", 
                                            height="16",
                                            cls="ml-2"
                                        ),
                                        cls="flex items-center"
                                    ),
                                    cls="cursor-pointer font-semibold text-blue-400 hover:text-blue-300 border-2 border-blue-400 p-2 rounded hover:bg-gray-800 flex items-center justify-between w-full"
                                ),
                                Div(
                                    id="refinement-history-content",
                                    cls="p-3 bg-gray-800 rounded-b text-gray-300 mt-2",
                                    hx_get="/api/html5/get-refinement-history",
                                    hx_trigger="load, revealed"
                                ),
                                cls="mb-4 border border-gray-600 rounded"
                            ),
                            
                            # Clear button positioned between history and textarea
                            Button(
                                Div(
                                    Svg(
                                        Path(d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z", fill="currentColor"),
                                        viewBox="0 0 24 24", 
                                        width="18", 
                                        height="18"
                                    ),
                                    Span("Clear Instructions", cls="ml-2"),
                                    cls="flex items-center justify-center"
                                ),
                                type="button",
                                cls="w-full py-2 px-3 bg-red-700 text-white rounded-md mb-3 hover:bg-red-800 transition-all duration-200",
                                onclick="document.getElementById('refinement_prompt').value = ''"
                            ),
                            
                            # Example refinement buttons for guidance
                            Div(
                                P("Example of Refinement Instructions:", cls="text-blue-400 text-sm font-medium mb-2"),
                                Div(
                                    Button("Add Variable", 
                                          type="button",
                                          cls="px-2 py-1 bg-gray-700 text-blue-300 text-xs rounded mr-2 mb-1 hover:bg-gray-600",
                                          onclick="insertRefinementExample('Add a new variable called x in the drop down list and keep the rest of the code the same')"),
                                    Button("Change Style", 
                                          type="button",
                                          cls="px-2 py-1 bg-gray-700 text-blue-300 text-xs rounded mr-2 mb-1 hover:bg-gray-600",
                                          onclick="insertRefinementExample('Change the font of the text to black in the table and keep the rest of the code the same')"),
                                    Button("Remove Element", 
                                          type="button",
                                          cls="px-2 py-1 bg-gray-700 text-blue-300 text-xs rounded mr-2 mb-1 hover:bg-gray-600",
                                          onclick="insertRefinementExample('Remove the object [object name] from the simulation and adjust the necessary code while keeping the rest of the code intact')"),
                                    Button("Create Object", 
                                          type="button",
                                          cls="px-2 py-1 bg-gray-700 text-blue-300 text-xs rounded mr-2 mb-1 hover:bg-gray-600",
                                          onclick="insertRefinementExample('Create an object [object name] so that the object can [describe behavior] and adjust the necessary code while keeping the rest of the code intact')"),
                                    cls="flex flex-wrap"
                                ),
                                cls="mb-3 p-2 border border-gray-700 rounded bg-gray-800"
                            ),
                            
                            # Advisory text about clearing previous instructions
                            P("⚠️ Please clear previous instructions before adding new ones to avoid duplicating refinements.", 
                              cls="text-yellow-400 text-sm mb-3 font-medium"),
                            
                            # Basic textarea for initial render and as fallback
                            Textarea("", 
                                  id='refinement_prompt', 
                                  name='prompt', 
                                  placeholder='Describe how you want to refine the current HTML5 content...',
                                  rows=32,
                                  cls="w-full p-3 border-2 rounded border-blue-500 bg-gray-800 focus:border-blue-400 focus:ring-2 focus:ring-blue-400 focus:outline-none text-white font-medium"),
                            cls="mb-4"
                        ),
                        
                        # Add script for fallback buttons 
                        Script("""
                        function insertRefinementExample(text) {
                            // Simple textarea handling without TinyMCE
                            const textarea = document.getElementById('refinement_prompt');
                            if (textarea) {
                                // Get cursor position or end of text
                                const start = textarea.selectionStart || 0;
                                const end = textarea.selectionEnd || 0;
                                const currentValue = textarea.value || '';
                                
                                // Insert text at cursor position
                                textarea.value = currentValue.substring(0, start) + text + currentValue.substring(end);
                                
                                // Set cursor position after inserted text
                                textarea.selectionStart = textarea.selectionEnd = start + text.length;
                                
                                // Focus the textarea
                                textarea.focus();
                            }
                        }
                        """),
                        
                        # Refinement button
                        Button("Refine", 
                               type='submit',
                               hx_post="/api/html5/refine-code",
                               hx_target="#code-editors-container",
                               hx_indicator="#loading-indicator",
                               cls="w-full py-3 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded-lg hover:shadow-lg transition-all duration-300 font-medium"),
                        
                        id="refinement-form",
                        enctype="multipart/form-data",
                        cls="space-y-4",
                    ),
                    id="refinement-panel",
                    cls="main-tab-panel"
                ),
                cls="tab-container"
            ),
            
            # Loading and results container
            Div(
                # Loading indicator
                Div(
                    P("Generating HTML5 content... Please wait.", cls="text-green-500"),
                    Div(cls="loading-spinner"),
                    id="loading-indicator",
                    cls="htmx-indicator text-center"
                ),
                
                # Editors container - will be populated by the generate endpoint
                Div(id="code-editors-container", cls="mt-4"),
                # Editor buttons container
                Div(
                    # Button Group Container
                    Div(
                        # Run Preview button
                        Button(
                            Div(
                                Svg(
                                    Path(d="M8 5v14l11-7z", fill="currentColor"),
                                    viewBox="0 0 24 24", 
                                    width="18", 
                                    height="18"
                                ),
                                Span("Run Preview", cls="ml-2"),
                                cls="flex items-center justify-center"
                            ),
                            id="run-preview-button",
                            hx_post="/api/html5/preview",
                            hx_target="#preview-container",
                            hx_include="#html-editor,#css-editor,#js-editor",
                            cls="action-button bg-gradient-to-r from-purple-600 to-purple-500 px-5 py-2 rounded-md hidden"
                        ),
                        
                        # Create ZIP button
                        Button(
                            Div(
                                Svg(
                                    Path(d="M20 6h-3V4c0-1.1-.9-2-2-2H9c-1.1 0-2 .9-2 2v2H4c-1.1 0-2 .9-2 2v11c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-5-2v2H9V4h6zM4 8h16v3H4V8zm0 11v-6h16v6H4z", fill="currentColor"),
                                    viewBox="0 0 24 24", 
                                    width="18", 
                                    height="18"
                                ),
                                Span("Create ZIP", cls="ml-2 text-gray-200"),
                                cls="flex items-center justify-center"
                            ),
                            id="create-zip-button",
                            cls="action-button bg-gradient-to-r from-purple-600 to-purple-500 px-5 py-2 rounded-md hidden",
                            onclick="createZipPackage(); return false;"
                        ),
                        
                        # Clear All button
                        Button(
                            Div(
                                Svg(
                                    Path(d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z", fill="currentColor"),
                                    viewBox="0 0 24 24", 
                                    width="18", 
                                    height="18"
                                ),
                                Span("Clear All", cls="ml-2"),
                                cls="flex items-center justify-center"
                            ),
                            id="clear-button",
                            hx_post="/api/html5/clear-preview",
                            hx_target="#preview-container",
                            hx_trigger="click",
                            hx_swap="innerHTML",
                            cls="action-button bg-gradient-to-r from-purple-600 to-purple-500 px-5 py-2 rounded-md hidden",
                        ),
                        
                        # Previous Interactive button
                        Button(
                            Div(
                                Svg(
                                    Path(d="M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z", fill="currentColor"),
                                    viewBox="0 0 24 24", 
                                    width="18", 
                                    height="18"
                                ),
                                Span("Previous Interactive", cls="ml-2"),
                                cls="flex items-center justify-center"
                            ),
                            id="previous-interactive-button",
                            hx_post="/api/html5/load-previous",
                            hx_target="#code-editors-container",
                            hx_trigger="click",
                            cls="action-button bg-gradient-to-r from-purple-600 to-purple-500 px-5 py-2 rounded-md hidden",
                        ),
                        id="editor-buttons-container",
                        cls="flex justify-between items-center gap-8 p-3 rounded-lg mx-auto my-4 bg-gray-800 border-0"
                    ),
                    
                    # Container for ZIP download link (initially empty)
                    Div(id="zip-download-container", cls="mt-6 w-full"),
                    
                    # ZIP Upload Section - moved below the buttons
                    Div(
                        H3("Import Content from ZIP", 
                           cls="block text-lg mb-2 text-gray-500", 
                           style="color: #4a5568 !important;"),
                        P("Upload a ZIP file containing HTML, CSS, and JavaScript files to import", 
                          cls="text-sm text-gray-500 mb-3",
                          style="color: #4a5568 !important;"),
                        
                        Form(
                            Div(
                                Label("Select ZIP File:", 
                                      cls="block mb-2 text-sm text-gray-500",
                                      style="color: #4a5568 !important;"),
                                Input(
                                    type="file", 
                                    name="zipfile", 
                                    accept=".zip",
                                    cls="w-full p-2 border rounded bg-gray-800 text-white"
                                ),
                                cls="mb-3"
                            ),
                            Button(
                                Div(
                                    Svg(
                                        Path(d="M5 8h14M12 4v8m-4 4h8m-10 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z", stroke="currentColor", stroke_width="2", fill="none"),
                                        viewBox="0 0 24 24", 
                                        width="20", 
                                        height="20",
                                        cls="mr-2"
                                    ),
                                    "Upload ZIP & Import Content",
                                    cls="flex items-center justify-center w-full"
                                ),
                                type="submit",
                                hx_post="/api/html5/upload-zip",
                                hx_target="#code-editors-container",
                                hx_indicator="#loading-indicator",
                                hx_encoding="multipart/form-data",
                                cls="w-full py-2 bg-gradient-to-r from-blue-600 to-blue-500 text-white rounded hover:shadow-lg transition-all duration-300"
                            ),
                            P(
                                "Tip: Upload a ZIP file that was previously downloaded from this tool for best results.",
                                cls="text-xs text-gray-500 mt-2",
                                style="color: #4a5568 !important;"
                            ),
                            enctype="multipart/form-data",
                            id="zip-upload-form",
                            method="post",
                            action="/api/html5/upload-zip",
                            cls="p-3 border border-gray-700 rounded bg-gray-800"
                        ),
                        
                        # Add JavaScript for handling ZIP file upload validation
                        Script("""
                            // Add validation for ZIP file upload
                            document.addEventListener('DOMContentLoaded', function() {
                                const zipFileInput = document.querySelector('input[name="zipfile"]');
                                const zipUploadForm = document.getElementById('zip-upload-form');
                                
                                if (zipFileInput && zipUploadForm) {
                                    // Add file change event listener for validation
                                    zipFileInput.addEventListener('change', function(e) {
                                        const file = e.target.files[0];
                                        const feedbackDiv = document.getElementById('zip-upload-feedback');
                                        
                                        // Remove any existing feedback
                                        if (feedbackDiv) {
                                            feedbackDiv.remove();
                                        }
                                        
                                        // Create new feedback element
                                        const newFeedback = document.createElement('div');
                                        newFeedback.id = 'zip-upload-feedback';
                                        
                                        if (file) {
                                            // Validate file extension
                                            if (!file.name.toLowerCase().endsWith('.zip')) {
                                                newFeedback.className = 'text-red-400 text-sm mt-2';
                                                newFeedback.textContent = 'Please select a ZIP file (.zip)';
                                                zipFileInput.value = ''; // Clear the input
                                            } else {
                                                newFeedback.className = 'text-green-400 text-sm mt-2';
                                                newFeedback.textContent = 'ZIP file selected: ' + file.name;
                                            }
                                        }
                                        
                                        // Add feedback after file input
                                        zipFileInput.parentNode.appendChild(newFeedback);
                                    });
                                    
                                    // Form submission handling for better feedback
                                    zipUploadForm.addEventListener('submit', function(e) {
                                        // Prevent default behavior so we can handle it manually
                                        e.preventDefault();
                                        
                                        const file = zipFileInput.files[0];
                                        
                                        // Validate file is selected
                                        if (!file) {
                                            // Show error feedback
                                            const feedbackDiv = document.getElementById('zip-upload-feedback');
                                            if (feedbackDiv) {
                                                feedbackDiv.remove();
                                            }
                                            
                                            const newFeedback = document.createElement('div');
                                            newFeedback.id = 'zip-upload-feedback';
                                            newFeedback.className = 'text-red-400 text-sm mt-2';
                                            newFeedback.textContent = 'Please select a ZIP file first';
                                            zipFileInput.parentNode.appendChild(newFeedback);
                                            
                                            return false;
                                        }
                                        
                                        // Validate it's a ZIP file
                                        if (!file.name.toLowerCase().endsWith('.zip')) {
                                            // Show error feedback
                                            const feedbackDiv = document.getElementById('zip-upload-feedback');
                                            if (feedbackDiv) {
                                                feedbackDiv.remove();
                                            }
                                            
                                            const newFeedback = document.createElement('div');
                                            newFeedback.id = 'zip-upload-feedback';
                                            newFeedback.className = 'text-red-400 text-sm mt-2';
                                            newFeedback.textContent = 'Please select a valid ZIP file (.zip)';
                                            zipFileInput.parentNode.appendChild(newFeedback);
                                            
                                            return false;
                                        }
                                        
                                        // Show loading state
                                        document.getElementById('loading-indicator').style.display = 'block';
                                        
                                        // Create form data manually
                                        const formData = new FormData();
                                        formData.append('zipfile', file);
                                        
                                        // Use fetch API for more control
                                        fetch('/api/html5/upload-zip', {
                                            method: 'POST',
                                            body: formData,
                                            // Let the browser set the correct Content-Type with boundary
                                        })
                                        .then(response => response.text())
                                        .then(html => {
                                            // Update editor container
                                            const editorContainer = document.getElementById('code-editors-container');
                                            if (editorContainer) {
                                                editorContainer.innerHTML = html;
                                                
                                                // Trigger htmx:afterSwap event for compatibility
                                                const event = new CustomEvent('htmx:afterSwap', {
                                                    detail: { target: editorContainer }
                                                });
                                                document.dispatchEvent(event);
                                            }
                                            
                                            // Hide loading indicator
                                            document.getElementById('loading-indicator').style.display = 'none';
                                        })
                                        .catch(error => {
                                            console.error('Error uploading ZIP:', error);
                                            
                                            // Show error message
                                            const editorContainer = document.getElementById('code-editors-container');
                                            if (editorContainer) {
                                                editorContainer.innerHTML = `
                                                    <div class="bg-red-800 text-white p-2 mb-4 rounded">
                                                        Error uploading ZIP file: ${error.message || 'Unknown error'}
                                                    </div>
                                                `;
                                            }
                                            
                                            // Hide loading indicator
                                            document.getElementById('loading-indicator').style.display = 'none';
                                        });
                                    });
                                }
                            });
                        """),
                        
                        cls="mt-6 p-4 border border-gray-700 rounded bg-gray-800 max-w-2xl mx-auto"
                    ),
                    
                    id="editor-buttons",
                    cls="mt-6 border-0 outline-none shadow-none"
                ),
                
                # Add a style to remove all borders
                Style("""
                #editor-buttons, #editor-buttons-container, #editor-buttons * {
                  border: none !important;
                  outline: none !important;
                  box-shadow: none !important;
                }
                """),
                
                cls="mt-4"
            ),
            
            cls="p-6"
        ),
        
        Script("""
                // Simple DOM ready function without TinyMCE
                document.addEventListener('DOMContentLoaded', function() {
                    // Make sure textareas are visible
                    const promptTextarea = document.getElementById('prompt');
                    if (promptTextarea) {
                        promptTextarea.style.display = 'block';
                    }
                    
                    const refinementTextarea = document.getElementById('refinement_prompt');
                    if (refinementTextarea) {
                        refinementTextarea.style.display = 'block';
                    }

                    const form = document.getElementById('html5-form');
                    
                    // Add submit event listener
                    form.addEventListener('submit', function(e) {
                        e.preventDefault();
                        
                        // Show loading indicator
                        document.getElementById('loading-indicator').style.display = 'block';
                        
                        // Create FormData object for proper file handling
                        const formData = new FormData(form);
                        
                        // Use fetch API for the request
                        fetch('/api/html5/generate-code', {
                            method: 'POST',
                            body: formData,
                            // Don't set Content-Type header - the browser will set the correct boundary
                        })
                        .then(response => response.text())
                        .then(html => {
                            // Update the code editors container
                            document.getElementById('code-editors-container').innerHTML = html;
                            
                            // Hide loading indicator
                            document.getElementById('loading-indicator').style.display = 'none';
                            
                            // Trigger HTMX afterSwap event for compatibility
                            const event = new CustomEvent('htmx:afterSwap', {
                                detail: { target: document.getElementById('code-editors-container') }
                            });
                            document.dispatchEvent(event);
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            document.getElementById('loading-indicator').style.display = 'none';
                            document.getElementById('code-editors-container').innerHTML = 
                                '<div class="error alert alert-danger">Error: ' + error.message + '</div>';
                        });
                    });
                });

                // CONSOLIDATED EVENT HANDLERS
                // Single htmx:afterSwap event handler for all concerns
                document.addEventListener('htmx:afterSwap', function(event) {
                    console.log('htmx:afterSwap event fired for target ID:', event.detail.target.id);
                    
                    // Handle code editors loaded - show all buttons
                    if (event.detail.target.id === 'code-editors-container') {
                        console.log('Code editors loaded, showing buttons');
                        
                        // Get all buttons
                        const runButton = document.getElementById('run-preview-button');
                        const zipButton = document.getElementById('create-zip-button');
                        const clearButton = document.getElementById('clear-button');
                        const previousButton = document.getElementById('previous-interactive-button');
                        
                        // Show them all by removing the hidden class
                        if (runButton) {
                            runButton.classList.remove('hidden');
                            console.log('Run button visible');
                        }
                        if (zipButton) {
                            zipButton.classList.remove('hidden');
                            console.log('ZIP button visible');
                        }
                        if (clearButton) {
                            clearButton.classList.remove('hidden');
                            console.log('Clear button visible');
                        }
                        if (previousButton) {
                            previousButton.classList.remove('hidden');
                            console.log('Previous Interactive button visible');
                        }
                        
                        // Auto-trigger preview
                        setTimeout(function() {
                            console.log("Auto-triggering preview");
                            if (runButton) {
                                runButton.click();
                            }
                        }, 500);
                    }
                });
                
                // Main tab switching function
                function switchMainTab(tabName, event) {
                    // Prevent default behavior
                    if (event) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                    
                    // Get all tabs and panels
                    const tabs = document.querySelectorAll('.main-tab');
                    const panels = document.querySelectorAll('.main-tab-panel');
                    
                    // Get the current width before switching
                    const currentPanel = document.querySelector('.main-tab-panel.active');
                    const currentWidth = currentPanel ? currentPanel.offsetWidth : 0;
                    
                    // Deactivate all tabs and panels
                    tabs.forEach(tab => tab.classList.remove('active'));
                    panels.forEach(panel => {
                        panel.classList.remove('active');
                        panel.style.display = 'none';
                    });
                    
                    // Activate selected tab and panel
                    document.getElementById(`${tabName}-tab`)?.classList.add('active');
                    const selectedPanel = document.getElementById(`${tabName}-panel`);
                    if (selectedPanel) {
                        selectedPanel.classList.add('active');
                        selectedPanel.style.display = 'block';
                        
                        // Set explicit width if we had a previous panel
                        if (currentWidth > 0) {
                            selectedPanel.style.minWidth = `${currentWidth}px`;
                        }
                    }
                    
                    console.log(`Switched to main tab: ${tabName}`);
                    return false;
                }
                
                // Function to update refinement form with current code
                function updateRefinementFormWithCurrentCode() {
                    // No need to update hidden fields as they've been removed
                    console.log('Refinement form updated - using server-side storage');
                }
                
                // Debugging code to troubleshoot the ZIP button
                document.addEventListener('DOMContentLoaded', function() {
                    console.log("DOM fully loaded");
                    
                    // Add a manual check for code editors on page load
                    setTimeout(function() {
                        const codeEditors = document.getElementById('code-editors-container');
                        if (codeEditors && codeEditors.innerHTML.trim() !== '') {
                            console.log("Code editors found on page load, checking buttons");
                            const zipButton = document.getElementById('create-zip-button');
                            if (zipButton) {
                                console.log("ZIP button exists:", zipButton.classList.contains('hidden') ? "hidden" : "visible");
                                // Force show the button
                                zipButton.classList.remove('hidden');
                            } else {
                                console.log("ZIP button not found in DOM");
                            }
                        }
                    }, 1000);
                    
                    // Add a click event listener to the Generate button
                    const generateButton = document.querySelector('button[hx_post="/api/html5/generate-code"]');
                    if (generateButton) {
                        console.log("Found Generate button");
                        generateButton.addEventListener('click', function() {
                            console.log("Generate button clicked");
                            
                            // Check buttons after a delay to allow HTMX to process
                            setTimeout(function() {
                                const zipButton = document.getElementById('create-zip-button');
                                if (zipButton) {
                                    console.log("ZIP button after generate:", zipButton.classList.contains('hidden') ? "hidden" : "visible");
                                    // Force show the button in case it's still hidden
                                    zipButton.classList.remove('hidden');
                                }
                            }, 5000); // Check after 5 seconds
                        });
                    }
                });

                // Function to create ZIP package via fetch API
                function createZipPackage() {
                    console.log("createZipPackage function called");
                    
                    // Show loading indicator in the download container
                    const downloadContainer = document.getElementById('zip-download-container');
                    if (downloadContainer) {
                        downloadContainer.innerHTML = `
                            <div class="bg-gray-800 p-4 rounded border border-blue-500">
                                <h4 class="text-lg font-bold text-gray-400 mb-2">Creating ZIP Package...</h4>
                                <div class="flex items-center space-x-3">
                                    <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                                    <p class="text-gray-400">Preparing your download...</p>
                                </div>
                            </div>
                        `;
                        downloadContainer.classList.remove('hidden');
                    }
                    
                    // Get content from each editor
                    const htmlContent = document.getElementById('html-editor')?.value || '';
                    const cssContent = document.getElementById('css-editor')?.value || '';
                    const jsContent = document.getElementById('js-editor')?.value || '';
                    
                    console.log(`Editor content sizes - HTML: ${htmlContent.length}, CSS: ${cssContent.length}, JS: ${jsContent.length}`);
                    
                    // Check for empty content
                    if (!htmlContent && !cssContent && !jsContent) {
                        if (downloadContainer) {
                            downloadContainer.innerHTML = `
                                <div class="bg-gray-800 p-4 rounded border border-amber-500">
                                    <h4 class="text-lg font-bold text-amber-400 mb-2">No Content Found</h4>
                                    <p>Please add some HTML, CSS, or JavaScript content first.</p>
                                </div>
                            `;
                        }
                        return;
                    }
                    
                    // Create form data
                    const formData = new FormData();
                    formData.append('html-editor', htmlContent);
                    formData.append('css-editor', cssContent);
                    formData.append('js-editor', jsContent);
                    
                    console.log("Sending form data to create-zip endpoint");
                    
                    // Use fetch API with proper error handling
                    fetch('/api/html5/create-zip', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) {
                            console.error(`Server returned ${response.status}: ${response.statusText}`);
                            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                        }
                        console.log("Got successful response from server");
                        return response.text();
                    })
                    .then(html => {
                        console.log("Received HTML response from server, updating container");
                        // Update the download container with the response
                        if (downloadContainer) {
                            downloadContainer.innerHTML = html;
                            
                            // Scroll to the download section
                            downloadContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                            
                            // Find and trigger the download link automatically 
                            setTimeout(() => {
                                const downloadLink = downloadContainer.querySelector('a[download]');
                                if (downloadLink) {
                                    console.log("Triggering download automatically");
                                    downloadLink.click();
                                } else {
                                    console.warn("Download link not found in the response");
                                }
                                
                                // Add focus/highlight effect
                                downloadContainer.classList.add('animate-pulse');
                                setTimeout(() => {
                                    downloadContainer.classList.remove('animate-pulse');
                                }, 1500);
                            }, 500);
                        } else {
                            console.error("Download container not found");
                        }
                    })
                    .catch(error => {
                        console.error('Error creating ZIP:', error);
                        if (downloadContainer) {
                            downloadContainer.innerHTML = `
                                <div class="bg-gray-800 p-4 rounded border border-red-500">
                                    <h4 class="text-lg font-bold text-red-500 mb-2">Error Creating ZIP</h4>
                                    <p class="mb-2">Error: ${error.message}</p>
                                    <button class="px-3 py-1 bg-blue-600 text-white rounded text-sm try-again-btn">
                                        Try Again
                                    </button>
                                </div>
                            `;
                            // Add event listener to the try again button
                            const tryAgainBtn = downloadContainer.querySelector('.try-again-btn');
                            if (tryAgainBtn) {
                                tryAgainBtn.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    createZipPackage();
                                    return false;
                                });
                            }
                        }
                    });
                }
                
                // Fixed ZIP button click handler
                setTimeout(function() {
                    const zipButton = document.getElementById('create-zip-button');
                    if (zipButton) {
                        console.log("Adding direct click handler to ZIP button");
                        zipButton.addEventListener('click', function(e) {
                            // Always prevent default to stop form submission
                            e.preventDefault();
                            e.stopPropagation();
                            
                            console.log("ZIP button clicked via direct handler");
                            // Always use our direct handler
                            createZipPackage();
                            
                            // Return false to be extra sure
                            return false;
                        });
                    }
                }, 2000); // Wait 2 seconds for the button to be available
                
                // Clear the preview and associated code
                function clearPreview() {
                    // Clear HTML5 Prompt textarea
                    var promptTextarea = document.getElementById('prompt');
                    if (promptTextarea) {
                        promptTextarea.value = '';
                    }
                    
                    // Refresh any iterative badges (but don't change the toggle state)
                    if (typeof updateIterativeBadge === 'function') {
                        updateIterativeBadge();
                    }
                }
                
                // Improved switchTab function that properly handles events
                window.switchTab = function(tabName, event) {
                    // If event is provided, prevent default behavior
                    if (event) {
                        event.preventDefault();
                        event.stopPropagation();
                    }
                    
                    // Define all tab names
                    const tabs = ['html', 'css', 'js'];
                    
                    // Get all tab and panel elements in one go
                    const elements = tabs.map(tab => ({
                        tab: document.getElementById(`${tab}-tab`),
                        panel: document.getElementById(`${tab}-panel`)
                    }));
                    
                    // Activate/deactivate as needed
                    elements.forEach(el => {
                        if (el.tab && el.panel) {
                            const isActive = el.tab.id === `${tabName}-tab`;
                            
                            // Update tab state
                            el.tab.classList.toggle('active', isActive);
                            
                            // Update panel state - ensure display is explicitly set
                            el.panel.classList.toggle('active', isActive);
                            el.panel.style.display = isActive ? 'block' : 'none';
                        }
                    });
                    
                    console.log(`Tab switched to: ${tabName}`);
                    
                    // Return false to ensure the event doesn't bubble up
                    return false;
                };
                
                // Add event listener for the refinement form submission
                document.addEventListener('DOMContentLoaded', function() {
                    const refinementForm = document.getElementById('refinement-form');
                    
                    if (refinementForm) {
                        refinementForm.addEventListener('submit', function(e) {
                            e.preventDefault();
                            
                            // Show loading indicator
                            document.getElementById('loading-indicator').style.display = 'block';
                            
                            // Create FormData object for proper file handling
                            const formData = new FormData(refinementForm);
                            
                            // Save the form data for debugging
                            console.log("Submitting refinement form");
                            
                            // Use fetch API for the request
                            fetch('/api/html5/refine-code', {
                                method: 'POST',
                                body: formData,
                            })
                            .then(response => response.text())
                            .then(html => {
                                // Update the code editors container
                                document.getElementById('code-editors-container').innerHTML = html;
                                
                                // Hide loading indicator
                                document.getElementById('loading-indicator').style.display = 'none';
                                
                                // Clear the refinement prompt - direct textarea access only
                                const textarea = document.getElementById('refinement_prompt');
                                if (textarea) {
                                    textarea.value = '';
                                    console.log("Cleared refinement prompt textarea");
                                }
                                
                                // Trigger HTMX afterSwap event for compatibility
                                const event = new CustomEvent('htmx:afterSwap', {
                                    detail: { target: document.getElementById('code-editors-container') }
                                });
                                document.dispatchEvent(event);
                                
                                // Refresh the refinement history after submission
                                const historyContent = document.getElementById('refinement-history-content');
                                if (historyContent) {
                                    // Use fetch to get the updated history
                                    fetch('/api/html5/get-refinement-history')
                                        .then(response => response.text())
                                        .then(history => {
                                            historyContent.innerHTML = history;
                                        });
                                }
                                
                                // Switch back to the editors view after refinement
                                switchMainTab('generation', null);
                            })
                            .catch(error => {
                                console.error('Error:', error);
                                document.getElementById('loading-indicator').style.display = 'none';
                                document.getElementById('code-editors-container').innerHTML = 
                                    '<div class="error alert alert-danger">Error: ' + error.message + '</div>';
                            });
                        });
                    }
                    
                    // Handle ZIP file upload to clear refinement history
                    const zipUploadForm = document.getElementById('zip-upload-form');
                    if (zipUploadForm) {
                        zipUploadForm.addEventListener('submit', function() {
                            // This will be triggered when a ZIP is uploaded
                            console.log("ZIP upload detected, clearing refinement history");
                            
                            // Make a simple GET request to clear the history
                            fetch('/api/html5/clear-preview', { method: 'POST' })
                                .then(() => console.log("Refinement history cleared after ZIP upload"));
                        });
                    }
                    
                    // Handle Generate button to clear refinement history
                    const generateForm = document.getElementById('html5-form');
                    if (generateForm) {
                        generateForm.addEventListener('submit', function() {
                            // This will be triggered when a new generation is started
                            console.log("New generation detected, clearing refinement history");
                            
                            // Make a simple GET request to clear the history
                            fetch('/api/html5/clear-preview', { method: 'POST' })
                                .then(() => console.log("Refinement history cleared after new generation"));
                        });
                    }
                });
        """)
    )
    
def create_code_editors(html="", css="", js=""):
    """Create a simplified tab-based code editor interface"""
    return Div(
        # Tab Navigation - ADD type="button" to prevent form submission
        Div(
            Button("HTML", 
                id="html-tab", 
                type="button",  # This is crucial to prevent form submission!
                cls="tab active", 
                onclick="switchTab('html')"),
            Button("CSS", 
                id="css-tab", 
                type="button",  # This is crucial to prevent form submission!
                cls="tab", 
                onclick="switchTab('css')"),
            Button("JavaScript", 
                id="js-tab", 
                type="button",  # This is crucial to prevent form submission!
                cls="tab", 
                onclick="switchTab('js')"),
            cls="tab-header"
        ),
        
        # Tab Content Panels (no changes needed here)
        # HTML Editor
        Div(
            Textarea(html, 
                id="html-editor", 
                name="html-editor", 
                cls="code-editor",
                placeholder="Write your HTML here..."),
            id="html-panel",
            cls="tab-panel active"
        ),
        
        # CSS Editor
        Div(
            Textarea(css, 
                id="css-editor", 
                name="css-editor", 
                cls="code-editor",
                placeholder="Write your CSS here..."),
            id="css-panel",
            cls="tab-panel"
        ),
        
        # JavaScript Editor
        Div(
            Textarea(js, 
                id="js-editor", 
                name="js-editor",
                cls="code-editor",
                placeholder="Write your JavaScript here..."),
            id="js-panel",
            cls="tab-panel"
        ),
        
        # Add simple CSS styles inline (no changes needed)
        Style("""
            /* Panel styling */
            .tab-panel {
                display: none;
                padding: 16px;
                background-color: #1a202c;
                border-bottom-left-radius: 0.5rem;
                border-bottom-right-radius: 0.5rem;
                border: 1px solid #2d3748;
                border-top: none;
            }
            
            .tab-panel.active {
                display: block;
            }
            
            /* Editor styling */
            .code-editor {
                width: 100%;
                min-height: 300px;
                background-color: #2d3748;
                color: #e2e8f0;
                font-family: 'Fira Code', 'Consolas', monospace;
                padding: 1rem;
                border: 1px solid #4a5568;
                border-radius: 0.375rem;
                resize: vertical;
                line-height: 1.5;
                font-size: 0.875rem;
                transition: border-color 0.2s ease;
            }
            
            .code-editor:focus {
                outline: none;
                border-color: #4299e1;
                box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.2);
            }
        """),
        
        # Enhanced JavaScript with improved event handling
        Script("""
            function switchTab(tabName) {
                // Prevent any default behaviors
                event.preventDefault();
                event.stopPropagation();
                
                // Hide all panels and deactivate all tabs
                const panels = document.querySelectorAll('.tab-panel');
                const tabs = document.querySelectorAll('.tab');
                
                panels.forEach(panel => {
                    panel.classList.remove('active');
                    panel.style.display = 'none';
                });
                
                tabs.forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Activate the selected tab and panel
                const selectedTab = document.getElementById(tabName + '-tab');
                const selectedPanel = document.getElementById(tabName + '-panel');
                
                if (selectedTab) selectedTab.classList.add('active');
                if (selectedPanel) {
                    selectedPanel.classList.add('active');
                    selectedPanel.style.display = 'block';
                }
                
                // Return false to ensure no form submission occurs
                return false;
            }
        """),
        
        id="code-editors-container",
        cls="code-editor-wrapper"
    )