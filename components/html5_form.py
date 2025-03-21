from fasthtml.common import *
import os
import base64
from io import BytesIO
from PIL import Image

def create_file_uploader(index=0):
    """Create a file uploader that supports both direct file upload and base64 data"""
    return Div(
        # Hidden input for storing base64 data
        Input(type="hidden", id=f"image-data-{index}", name=f"image-data-{index}"),
        
        # Title for each uploader
        H4(f"Image {index+1}", cls="text-lg font-semibold mb-2 text-blue-300"),
        
        # The file input with improved styling
        Label(
            Input(
                type="file", 
                id=f"image-upload-{index}", 
                name=f"image-upload-{index}",
                accept="image/*",
                cls="block w-full text-sm text-gray-400 bg-gray-700 rounded cursor-pointer mb-2 p-2 border border-gray-600 hover:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            ),
            cls="block w-full mb-3"
        ),
        
        # Preview container with improved styling
        Div(
            cls="image-preview hidden w-full h-32 bg-gray-800 rounded-lg flex items-center justify-center overflow-hidden mb-3 border border-gray-600",
            id=f"preview-container-{index}"
        ),
        
        # JavaScript to handle immediate preview and store base64 data
        # Enhanced to add visual feedback when image is loaded
        Script(f"""
        document.getElementById('image-upload-{index}').addEventListener('change', function(e) {{
            const file = e.target.files[0];
            const container = document.getElementById('uploader-container-{index}');
            
            if (file) {{
                const reader = new FileReader();
                
                reader.onload = function(e) {{
                    // Show preview
                    const previewContainer = document.getElementById('preview-container-{index}');
                    previewContainer.innerHTML = `<img src="${{e.target.result}}" class="max-h-full max-w-full object-contain" />`;
                    previewContainer.classList.remove('hidden');
                    
                    // Store base64 data in the hidden input
                    const base64Data = e.target.result.split(',')[1];
                    document.getElementById('image-data-{index}').value = base64Data;
                    
                    // Add visual indication that this uploader has an image
                    container.classList.add('has-image');
                }};
                
                reader.readAsDataURL(file);
            }} else {{
                // Remove visual indication if no file is selected
                container.classList.remove('has-image');
                
                // Hide preview container
                const previewContainer = document.getElementById('preview-container-{index}');
                previewContainer.innerHTML = '';
                previewContainer.classList.add('hidden');
                
                // Clear hidden input
                document.getElementById('image-data-{index}').value = '';
            }}
        }});
        """),
        
        cls="file-uploader-container mb-6 p-4 border-2 border-gray-700 rounded-lg bg-gray-900 transition-all hover:shadow-md",
        id=f"uploader-container-{index}"
    )

def create_multiple_uploaders(count=5):
    """Create multiple simple file uploaders"""
    uploaders = [create_file_uploader(i) for i in range(count)]
    
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
            id="clear-all-images-button",
            type="button",
            cls="w-full py-2 px-4 bg-red-500 text-white rounded hover:bg-red-600"
        ),
        # JavaScript to handle clearing all images
        Script("""
        document.getElementById('clear-all-images-button').addEventListener('click', function() {
            // Clear all file inputs        
            for (let i = 0; i < 5; i++) {
                const fileInput = document.getElementById(`image-upload-${i}`);
                if (fileInput) {
                    fileInput.value = '';
                }
            }   

            // Clear all hidden base64 inputs
            for (let i = 0; i < 5; i++) {
                const base64Input = document.getElementById(`image-data-${i}`);
                if (base64Input) {
                    base64Input.value = '';
                }                   
            }

            // Hide all preview containers
            for (let i = 0; i < 5; i++) {
                const previewContainer = document.getElementById(`preview-container-${i}`);
                if (previewContainer) {
                    previewContainer.innerHTML = '';    
                    previewContainer.classList.add('hidden');
                }
            }
        });
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
    return Div(
        # Add styles for the preview, editors, etc.
        Style("""
            body {
                background-color: #121212;
                color: #e0e0e0;
            }

            .preview-frame {
                width: 100%;
                height: 400px;
                border: 1px solid #333;
                border-radius: 4px;
                background-color: #121212 !important;
                color: #ddd;
                margin-bottom: 20px;
                overflow: hidden;
            }
            
            .preview-frame iframe {
                width: 100%;
                height: 100%;
                border: none;
                background-color: #121212 !important;
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
                border-bottom: 2px solid #4299e1;
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
                background: linear-gradient(to right, #4299e1, #7f9cf5);
            }
            
        """),
        
        # Include TinyMCE script
        Script(src="https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js", referrerpolicy="origin"),
        
        H2("HTML5 Interactive Editor", cls="text-center text-xl font-bold mb-4"),
        
        # Preview area with increased height
        Div(
            H3("Preview", cls="text-lg font-semibold mb-2"),
            Div(
                Div("Your HTML5 content will appear here",
                    cls="flex items-center justify-center h-full text-gray-400"),
                id="preview-container",
                cls="preview-frame",
                hx_swap="innerHTML",
                style="background-color: #121212 !important; height: 700px;" # Increased height from default 400px to 600px
            ),
            cls="mb-6"
        ),

        
        # Code generator form
        Card(
            Form(
                # Hidden API Key
                Input(id='api_key', name='api_key',
                    value=api_key,
                    type='hidden'),
                
                # Model selector
                Div(
                    Label("Model:", cls="block mb-2"),
                    Select(
                        #Gpt 4.5 
                        Option("Claude 3.7 Sonnet", value="claude-3-7-sonnet-20250219"),
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
                
                # Add iterative toggle switch
                Div(
                    Label(
                        Div(
                            Input(
                                type="checkbox",
                                id="iterative-toggle",
                                name="iterative-toggle",
                                cls="sr-only peer",
                                checked=True,
                                value="on"  # Added value attribute to ensure proper form submission
                            ),
                            Div(
                                cls="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-blue-500 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600",
                            ),
                            cls="relative inline-flex items-center cursor-pointer"
                        ),
                        Span("Iterative Mode", cls="ml-3 text-sm font-medium text-gray-300"),
                        cls="inline-flex items-center cursor-pointer"
                    ),
                    P("When enabled, existing code will be included in your next prompt for refinement", 
                    cls="text-xs text-gray-400 mt-1 ml-14"),
                    cls="flex flex-col mb-4 iterative-container" # Added iterative-container class for styling
                ),
                
                
                
                # Rich Text Editor for prompt
                Div(
                    Label("HTML5 Prompt:", cls="block mb-2"),
                    # Basic textarea for initial render and as fallback
                    Textarea("", 
                          id='prompt', 
                          name='prompt', 
                          placeholder='Describe the HTML5 interactive content you want to generate...',
                          rows=8,
                          cls="w-full p-2 border rounded"),
                    cls="mb-4"
                ),
                
                
                
                                # File upload section - simplified to basic file inputs
                Div(
                    H3("Reference Images (Up to 5):", cls="block text-lg mb-2"),
                    P("Upload images to be used as references in your interactive content", 
                      cls="text-sm text-gray-400 mb-4"),
                    
                    create_multiple_uploaders(5),
                    
                    cls="mb-6 p-4 border border-gray-700 rounded bg-gray-900"
                ),
                # Generate button
                Button("Generate", 
                       type='submit',
                       hx_post="/api/html5/generate-code",
                       hx_target="#code-editors-container",
                       hx_indicator="#loading-indicator",
                       cls="w-full py-3 bg-gradient-to-r from-purple-600 to-purple-500 text-white rounded-lg hover:shadow-lg transition-all duration-300 font-medium"),
                
                # Loading and results container
                Div(
                    # Loading indicator
                    Div(
                        P("Generating HTML5 content... Please wait."),
                        Div(cls="loading-spinner"),
                        id="loading-indicator",
                        cls="htmx-indicator text-center"
                    ),
                    
                    # Editors container - will be populated by the generate endpoint
                    Div(id="code-editors-container", cls="mt-4"),
                    # Editor buttons container
                    Div(
                        # Run Preview button
                        Button("Run Preview",
                            id="run-preview-button",
                            hx_post="/api/html5/preview",
                            hx_target="#preview-container",
                            hx_include="#html-editor,#css-editor,#js-editor",
                            cls="action-button bg-gradient-to-r from-green-600 to-green-500 hidden"),
                        
                        # Undo button with icon
                        Button(
                            Div(
                                Svg(
                                    Path(d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z", 
                                         fill="currentColor"),
                                    viewBox="0 0 24 24", 
                                    width="20", 
                                    height="20"
                                ),
                                Span("Undo", cls="ml-2"),
                                cls="flex items-center justify-center w-full"
                            ),
                            id="undo-button",
                            hx_post="/api/html5/undo",
                            hx_target="#code-editors-container",
                            hx_swap="innerHTML",
                            disabled=True,
                            cls="action-button bg-gradient-to-r from-blue-600 to-blue-500 hidden opacity-50 cursor-not-allowed",
                            hx_trigger="click",
                            hx_include="[id='html-editor'],[id='css-editor'],[id='js-editor']",
                            hx_on_after_request="""
                                if(event.detail.successful) {
                                    // Check if there's more history available
                                    fetch('/api/html5/check-history')
                                        .then(response => response.json())
                                        .then(data => {
                                            if(data.hasHistory) {
                                                this.disabled = false;
                                                this.classList.remove('opacity-50', 'cursor-not-allowed');
                                            } else {
                                                this.disabled = true;
                                                this.classList.add('opacity-50', 'cursor-not-allowed');
                                            }
                                        });
                                }
                            """
                        ),
                        
                        # Container for buttons that will be added after generation
                        Div(id="dynamic-buttons", cls="flex-grow"),
                        
                        # Clear All button
                        Button(
                            Div(
                                Svg(
                                    Path(d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z", fill="currentColor"),
                                    viewBox="0 0 24 24", 
                                    width="20", 
                                    height="20"
                                ),
                                Span("Clear All", cls="ml-2"),
                                cls="flex items-center justify-center w-full"
                            ),
                            id="clear-button",
                            hx_post="/api/html5/clear-preview",
                            hx_target="#preview-container",
                            hx_trigger="click",
                            hx_swap="innerHTML",
                            cls="action-button bg-gradient-to-r from-gray-600 to-gray-500 hidden"),
                        
                        # Container for ZIP download link (initially empty)
                        Div(id="zip-download-container", cls="mt-6 w-full"),
                        
                        id="editor-buttons",
                        cls="mt-6 flex flex-wrap justify-between items-center gap-4"
                    ),
                  # Add this script tag right after your button container in the HTML

                    Script("""
                    // Direct ZIP button handler that activates as soon as possible
                    (function() {
                        // Function to handle the ZIP button click directly
                        function handleZipButton() {
                            const zipButton = document.getElementById('create-zip-button');
                            if (zipButton && !zipButton._handled) {
                                console.log("ZIP Button found - adding direct handler");
                                
                                // Add direct click handler
                                zipButton.addEventListener('click', function(e) {
                                    // Prevent default behavior to stop form submission
                                    e.preventDefault();
                                    e.stopPropagation();
                                    
                                    console.log("ZIP button clicked directly");
                                    
                                    // Get the download container
                                    const downloadContainer = document.getElementById('zip-download-container');
                                    if (downloadContainer) {
                                        downloadContainer.innerHTML = `
                                            <div class="bg-gray-800 p-4 rounded border border-blue-500">
                                                <h4 class="text-lg font-bold text-blue-400 mb-2">Creating ZIP Package...</h4>
                                                <div class="flex items-center space-x-3">
                                                    <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                                                    <p>Preparing your download...</p>
                                                </div>
                                            </div>
                                        `;
                                        downloadContainer.classList.remove('hidden');
                                    }
                                    
                                    // Get content from editors
                                    const htmlContent = document.getElementById('html-editor')?.value || '';
                                    const cssContent = document.getElementById('css-editor')?.value || '';
                                    const jsContent = document.getElementById('js-editor')?.value || '';
                                    
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
                                    
                                    // Make the request
                                    fetch('/api/html5/create-zip', {
                                        method: 'POST',
                                        body: formData
                                    })
                                    .then(response => response.text())
                                    .then(html => {
                                        if (downloadContainer) {
                                            downloadContainer.innerHTML = html;
                                            downloadContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
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
                                            downloadContainer.querySelector('.try-again-btn')?.addEventListener('click', function() {
                                                zipButton.click();
                                            });
                                        }
                                    });
                                    
                                    // Return false to be extra sure we're preventing default behavior
                                    return false;
                                });
                                
                                // Mark button as handled
                                zipButton._handled = true;
                                
                                // Make sure button is visible
                                zipButton.classList.remove('hidden');
                                console.log("ZIP Button is now visible and has direct handler");
                            }
                        }
                        
                        // Try to handle the button immediately
                        handleZipButton();
                        
                        // Also try after a delay in case the button isn't ready yet
                        setTimeout(handleZipButton, 1000);
                        
                        // Also after code editors are loaded
                        document.addEventListener('htmx:afterSwap', function(e) {
                            if (e.detail.target.id === 'code-editors-container') {
                                setTimeout(handleZipButton, 500);
                            }
                        });
                        
                        // Ensure button is visible after generate
                        const generateButton = document.querySelector('button[type="submit"]');
                        if (generateButton) {
                            generateButton.addEventListener('click', function() {
                                setTimeout(handleZipButton, 3000);
                            });
                        }
                    })();
                    """),
        
                    
                    cls="mt-4"
                ),
                id="html5-form",
                enctype="multipart/form-data",
                cls="space-y-4",
              
            ),
            cls="p-6"
        ),
        
      Script("""
                // Initialize TinyMCE
                document.addEventListener('DOMContentLoaded', function() {
                    initRichTextEditor();
                    
                    // Ensure iterative mode is on by default
                    const iterativeToggle = document.getElementById('iterative-toggle');
                    if (iterativeToggle) {
                        iterativeToggle.checked = true;
                        updateIterativeBadge();
                        console.log('Iterative mode initialized to ON by default');
                    }
                });

                function initRichTextEditor() {
                    // Check if TinyMCE exists
                    if (typeof tinymce !== 'undefined') {
                        if (tinymce.get('prompt')) {
                            tinymce.get('prompt').remove();
                        }
                        
                        tinymce.init({
                            selector: '#prompt',
                            height: 250,
                            skin: 'oxide-dark',
                            content_css: 'dark',
                            plugins: 'autosave link image lists table code help wordcount',
                            toolbar: 'undo redo | styles | bold italic underline | alignleft aligncenter alignright | bullist numlist | link image | code',
                            menubar: 'file edit view insert format tools help',
                            placeholder: 'Describe the HTML5 interactive content you want to generate...',
                            content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:14px; color:#e0e0e0; }'
                        });
                    } else {
                        console.warn('TinyMCE not loaded');
                        // Fallback - just show the textarea
                        document.getElementById('prompt').style.display = 'block';
                    }
                }

                document.addEventListener('DOMContentLoaded', function() {
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
                        
                        // Show them all by removing the hidden class
                        if (runButton) {
                            runButton.classList.remove('hidden');
                            console.log('Run button visible');
                        }
                        if (zipButton) {
                            zipButton.classList.remove('hidden');
                            zipButton.style.display = 'inline-flex';  // Force display as flex
                            console.log('ZIP button visible and set to display flex');
                        }
                        if (clearButton) {
                            clearButton.classList.remove('hidden');
                            console.log('Clear button visible');
                        }
                        
                        // Auto-trigger preview
                        setTimeout(function() {
                            console.log("Auto-triggering preview");
                            if (runButton) {
                                runButton.click();
                            }
                        }, 500);
                        
                        // Update iterative badge if needed
                        updateIterativeBadge();
                    }
                    
                    // Additional check for ZIP button visibility after a delay
                    setTimeout(function() {
                        const zipButton = document.getElementById('create-zip-button');
                        if (zipButton && zipButton.classList.contains('hidden')) {
                            console.log('ZIP button still hidden after delay, forcing show');
                            zipButton.classList.remove('hidden');
                            zipButton.style.display = 'inline-flex';
                        }
                    }, 1000);
                });

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
                    // Show loading indicator in the download container
                    const downloadContainer = document.getElementById('zip-download-container');
                    if (downloadContainer) {
                        downloadContainer.innerHTML = `
                            <div class="bg-gray-800 p-4 rounded border border-blue-500">
                                <h4 class="text-lg font-bold text-blue-400 mb-2">Creating ZIP Package...</h4>
                                <div class="flex items-center space-x-3">
                                    <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                                    <p>Preparing your download...</p>
                                </div>
                            </div>
                        `;
                        downloadContainer.classList.remove('hidden');
                    }
                    
                    // Get content from each editor
                    const htmlContent = document.getElementById('html-editor')?.value || '';
                    const cssContent = document.getElementById('css-editor')?.value || '';
                    const jsContent = document.getElementById('js-editor')?.value || '';
                    
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
                    
                    // Use fetch API with proper error handling
                    fetch('/api/html5/create-zip', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`Server returned ${response.status}: ${response.statusText}`);
                        }
                        return response.text();
                    })
                    .then(html => {
                        // Update the download container with the response
                        if (downloadContainer) {
                            downloadContainer.innerHTML = html;
                            
                            // Scroll to the download section
                            downloadContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                            
                            // Add focus/highlight effect
                            downloadContainer.classList.add('animate-pulse');
                            setTimeout(() => {
                                downloadContainer.classList.remove('animate-pulse');
                            }, 1500);
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

                // Function to update the iterative mode badge
                function updateIterativeBadge() {
                    const iterativeToggle = document.getElementById('iterative-toggle');
                    const promptContainer = document.querySelector('.tox-edit-area') || document.getElementById('prompt')?.parentNode;
                    const badge = document.getElementById('iterative-badge');
                    
                    if (!iterativeToggle || !promptContainer) return;
                    
                    // Remove existing badge if it exists
                    if (badge) badge.remove();
                    
                    // Create new badge if toggle is checked
                    if (iterativeToggle.checked) {
                        const newBadge = document.createElement('div');
                        newBadge.id = 'iterative-badge';
                        newBadge.innerHTML = '<span class="pulse"></span> Iterative Mode Active';
                        newBadge.className = 'px-3 py-1 bg-blue-600 text-white text-xs rounded-full absolute top-0 right-0 m-2 z-10 flex items-center gap-2';
                        newBadge.style.zIndex = '9999';
                        
                        // Add to prompt container
                        promptContainer.style.position = 'relative';
                        promptContainer.appendChild(newBadge);
                    }
                    
                    console.log("Iterative mode:", iterativeToggle.checked ? "ON" : "OFF");
                }

                // Modified DOM ready function for iterative mode
                document.addEventListener('DOMContentLoaded', function() {
                    // Initialize the iterative badge
                    updateIterativeBadge();
                    
                    // Listen for toggle changes
                    const iterativeToggle = document.getElementById('iterative-toggle');
                    if (iterativeToggle && iterativeToggle.checked) {
                        console.log("Iterative mode is ON - preparing editor content");
                        
                        // Get the code editors
                        const htmlEditor = document.getElementById('html-editor');
                        const cssEditor = document.getElementById('css-editor');
                        const jsEditor = document.getElementById('js-editor');
                        
                        // Check if editors exist and have content
                        if (htmlEditor || cssEditor || jsEditor) {
                            console.log("Code editors found - adding content to form");
                            
                            // Create hidden inputs if they don't exist
                            if (!document.getElementById('html-content-hidden')) {
                                const htmlHidden = document.createElement('input');
                                htmlHidden.type = 'hidden';
                                htmlHidden.id = 'html-content-hidden';
                                htmlHidden.name = 'html-content';
                                htmlHidden.value = htmlEditor ? htmlEditor.value : '';
                                this.appendChild(htmlHidden);
                                console.log(`Added HTML content (${htmlHidden.value.length} chars)`);
                            }
                            
                            if (!document.getElementById('css-content-hidden')) {
                                const cssHidden = document.createElement('input');
                                cssHidden.type = 'hidden';
                                cssHidden.id = 'css-content-hidden';
                                cssHidden.name = 'css-content';
                                cssHidden.value = cssEditor ? cssEditor.value : '';
                                this.appendChild(cssHidden);
                                console.log(`Added CSS content (${cssHidden.value.length} chars)`);
                            }
                            
                            if (!document.getElementById('js-content-hidden')) {
                                const jsHidden = document.createElement('input');
                                jsHidden.type = 'hidden';
                                jsHidden.id = 'js-content-hidden';
                                jsHidden.name = 'js-content';
                                jsHidden.value = jsEditor ? jsEditor.value : '';
                                this.appendChild(jsHidden);
                                console.log(`Added JS content (${jsHidden.value.length} chars)`);
                            }
                        } else {
                            console.log("Code editors not found");
                        }
                    }
                });

                // SIMPLIFIED FORM SUBMISSION FOR ITERATIVE MODE
                document.getElementById('html5-form')?.addEventListener('submit', function(e) {
                    // Skip the default HTMX handling
                    // e.preventDefault();
                    
                    const iterativeToggle = document.getElementById('iterative-toggle');
                    if (!iterativeToggle || !iterativeToggle.checked) {
                        console.log("Not in iterative mode, using original prompt");
                        return; // Continue with normal submission
                    }
                    
                    console.log("Preparing iterative mode submission");
                    
                    // Get the session content from the editors if they exist
                    const htmlEditor = document.getElementById('html-editor');
                    const cssEditor = document.getElementById('css-editor');
                    const jsEditor = document.getElementById('js-editor');
                    
                    if (!(htmlEditor && cssEditor && jsEditor)) {
                        console.log("Editors not found, skipping iterative mode");
                        return; // Continue with normal submission
                    }
                    
                    // Check if any editor has content
                    if (!(htmlEditor.value || cssEditor.value || jsEditor.value)) {
                        console.log("No code to iterate on, skipping iterative mode");
                        return; // Continue with normal submission
                    }
                    
                    // Get the editor content
                    let editor = tinymce.get('prompt');
                    let promptContent = '';
                    
                    if (editor) {
                        promptContent = editor.getContent();
                    } else {
                        const promptElement = document.getElementById('prompt');
                        if (promptElement) promptContent = promptElement.value;
                    }
                    
                    // Add banner that will appear in the prompt
                    const iterativeBanner = `
                    <div style="padding: 10px; background-color: #4a90e2; color: white; margin-bottom: 10px; border-radius: 5px;">
                        <strong>ITERATIVE MODE:</strong> You are modifying existing code. Previous code is included below.
                    </div>
                    `;
                    
                    // Append code to prompt with the banner
                    let newContent = iterativeBanner + promptContent + '\n\n';
                    newContent += '<hr>\n';
                    newContent += '<h3>Current code for iteration:</h3>\n\n';
                    
                    // Add the code blocks for HTML, CSS, and JS
                    if (htmlEditor.value) {
                        newContent += '<pre><code class="language-html">\n' + htmlEditor.value + '\n</code></pre>\n\n';
                    }
                    
                    if (cssEditor.value) {
                        newContent += '<pre><code class="language-css">\n' + cssEditor.value + '\n</code></pre>\n\n';
                    }
                    
                    if (jsEditor.value) {
                        newContent += '<pre><code class="language-javascript">\n' + jsEditor.value + '\n</code></pre>\n\n';
                    }
                    
                    newContent += '<hr>\n';
                    newContent += '<p>Please improve the above code based on my instructions. Maintain the same structure with HTML, CSS, and JavaScript sections.</p>';
                    
                    console.log("Setting iterative prompt content");
                    
                    // Set the content back to the editor
                    if (editor) {
                        editor.setContent(newContent);
                    } else if (promptElement) {
                        promptElement.value = newContent;
                    }
                    
                    // Add a debug message to the console
                    console.log("Iterative mode enabled: Sending existing code for iteration");
                });

                // Update system prompt to handle iterative mode
                function updateSystemPrompt(systemPrompt, isIterative) {
                    if (!isIterative) return systemPrompt;
                    
                    // Add instructions for iterative mode
                    return systemPrompt + `
                    
                    ITERATIVE MODE INSTRUCTIONS:
                    - You are modifying existing HTML, CSS, and JavaScript code.
                    - The user has provided the current code in the prompt.
                    - Maintain the same overall structure while making improvements.
                    - Focus on addressing the specific requests in the user's instructions.
                    - Return the complete improved code with all three components properly wrapped.
                    `;
                }

                // Clear button should reset iterative mode
                document.addEventListener('click', function(e) {
                    if (e.target && e.target.id === 'clear-button') {
                        const iterativeToggle = document.getElementById('iterative-toggle');
                        if (iterativeToggle) {
                            iterativeToggle.checked = false;
                            updateIterativeBadge();
                        }
                    }
                });

                // Fixed ZIP button click handler
                document.addEventListener('DOMContentLoaded', function() {
                    // Add direct handler to the ZIP button when it's available
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
                });

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

                // Update onclick handlers to properly pass the event
                document.addEventListener('DOMContentLoaded', function() {
                    // Find all tab buttons and update their onclick
                    const tabButtons = document.querySelectorAll('.tab');
                    tabButtons.forEach(button => {
                        const tabName = button.id.replace('-tab', '');
                        button.onclick = function(e) {
                            return switchTab(tabName, e);
                        };
                    });
                });

                // Update the JavaScript to handle undo button state
                function updateUndoButtonState() {
                    const undoButton = document.getElementById('undo-button');
                    if (undoButton) {
                        // Check if there's any history in the session
                        fetch('/api/html5/check-history')
                            .then(response => response.json())
                            .then(data => {
                                if (data.hasHistory) {
                                    undoButton.disabled = false;
                                    undoButton.classList.remove('opacity-50', 'cursor-not-allowed');
                                } else {
                                    undoButton.disabled = true;
                                    undoButton.classList.add('opacity-50', 'cursor-not-allowed');
                                }
                            });
                    }
                }

                // Update undo button state when code is generated
                document.addEventListener('htmx:afterSwap', function(event) {
                    if (event.detail.target.id === 'code-editors-container') {
                        updateUndoButtonState();
                    }
                });

                // Update undo button state on page load
                document.addEventListener('DOMContentLoaded', function() {
                    updateUndoButtonState();
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