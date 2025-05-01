from fasthtml.common import *
import json

def create_gallery_upload_form(gallery_type="primary"):
    """
    Create an upload form for gallery interactives.
    
    Parameters:
    gallery_type (str): 'primary', 'secondary', or 'jc_ci' to determine which levels to show
    """
    # Define the class levels based on gallery type
    level_options = []
    if gallery_type == "primary":
        level_options = [
            Option("Select a level", value="", disabled=True, selected=True),
            Option("Primary 1", value="Primary 1"),
            Option("Primary 2", value="Primary 2"),
            Option("Primary 3", value="Primary 3"),
            Option("Primary 4", value="Primary 4"),
            Option("Primary 5", value="Primary 5"),
            Option("Primary 6", value="Primary 6"),
        ]
    elif gallery_type == "secondary":
        level_options = [
            Option("Select a level", value="", disabled=True, selected=True),
            Option("Secondary 1", value="Secondary 1"),
            Option("Secondary 2", value="Secondary 2"),
            Option("Secondary 3", value="Secondary 3"),
            Option("Secondary 4", value="Secondary 4"),
            Option("Secondary 5", value="Secondary 5"),
        ]
    elif gallery_type == "jc_ci":
        level_options = [
            Option("Select a level", value="", disabled=True, selected=True),
            Option("Junior College 1", value="Junior College 1"),
            Option("Junior College 2", value="Junior College 2"),
        ]
    
    # Define all subjects (will be filtered by JavaScript based on level)
    all_subjects = {
        "primary": [
            "English Language",
            "Chinese",
            "Malay",
            "Tamil",
            "Mathematics",
            "Science",
            "Social Studies",
            "Physical Education (PE)",
            "Art",
            "Music",
            "Character and Citizenship Education (CCE)"
        ],
        "secondary": [
            "English Language",
            "Chinese",
            "Malay",
            "Tamil",
            "Mathematics",
            "Additional Mathematics",
            "Science",
            "Physics",
            "Chemistry",
            "Biology",
            "Social Studies",
            "Literature",
            "History",
            "Geography",
            "Physical Education (PE)",
            "Art",
            "Music",
            "Character and Citizenship Education (CCE)",
            "Design and Technology",
            "Food and Consumer Education",
            "Computing",
            "Theatre Studies and Drama"
        ],
        "jc_ci": [
            "General Paper",
            "Chinese",
            "Malay",
            "Tamil",
            "Mathematics",
            "Further Mathematics",
            "Physics",
            "Chemistry",
            "Biology",
            "Economics",
            "Accounting",
            "History",
            "Geography",
            "Art",
            "Music",
            "Theatre Studies and Drama",
            "Computing"
        ]
    }
    
    # Convert subjects to JSON for use in JavaScript
    subjects_json = json.dumps(all_subjects)
    
    return Div(
        # Styles for the upload form
        Style("""
            .upload-form-container {
                background-color: #1a202c;
                border-radius: 8px;
                border: 1px solid #2d3748;
                padding: 1.5rem;
                margin-bottom: 2rem;
            }
            
            .form-title {
                color: #48bb78;
                margin-bottom: 1rem;
                text-align: center;
            }
            
            .form-grid {
                display: grid;
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }
            
            @media (min-width: 768px) {
                .form-grid {
                    grid-template-columns: 1fr 1fr;
                }
            }
            
            .form-section {
                padding: 1rem;
                background-color: #2d3748;
                border-radius: 8px;
            }
            
            .section-title {
                font-size: 1.25rem;
                color: #4299e1;
                margin-bottom: 1rem;
                border-bottom: 1px solid #4a5568;
                padding-bottom: 0.5rem;
            }
            
            .form-group {
                margin-bottom: 1rem;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 0.5rem;
                color: #a0aec0;
            }
            
            .form-control {
                width: 100%;
                padding: 0.75rem;
                background-color: #1a202c;
                border: 1px solid #4a5568;
                border-radius: 4px;
                color: #e2e8f0;
                transition: border-color 0.2s;
            }
            
            .form-control:focus {
                outline: none;
                border-color: #4299e1;
                box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.2);
            }
            
            .preview-container {
                height: 400px;
                background-color: #1a202c;
                border: 1px solid #4a5568;
                border-radius: 4px;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
            }
            
            .preview-placeholder {
                color: #a0aec0;
                text-align: center;
            }
            
            .btn {
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.2s;
            }
            
            .btn-primary {
                background-color: #4299e1;
                color: white;
            }
            
            .btn-primary:hover {
                background-color: #3182ce;
            }
            
            .btn-success {
                background-color: #48bb78;
                color: white;
            }
            
            .btn-success:hover {
                background-color: #38a169;
            }
            
            .btn-block {
                display: block;
                width: 100%;
            }
            
            .uploader-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 1rem;
                margin-top: 1rem;
            }
            
            .uploader-item {
                background-color: #1a202c;
                border: 1px dashed #4a5568;
                border-radius: 4px;
                padding: 0.5rem;
                text-align: center;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .uploader-item:hover {
                border-color: #4299e1;
            }
            
            .uploader-item.has-image {
                border-style: solid;
                border-color: #48bb78;
            }
            
            .uploader-preview {
                width: 100%;
                height: 100px;
                object-fit: contain;
                margin-top: 0.5rem;
                display: none;
            }
            
            .uploader-item.has-image .uploader-preview {
                display: block;
            }
            
            /* Modal styling */
            .modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                z-index: 1000;
                align-items: center;
                justify-content: center;
            }
            
            .modal.show {
                display: flex;
            }
            
            .modal-content {
                background-color: #2d3748;
                border-radius: 8px;
                padding: 2rem;
                max-width: 500px;
                width: 90%;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .modal-title {
                font-size: 1.5rem;
                color: #4299e1;
                margin-bottom: 1rem;
                text-align: center;
            }
            
            .modal-body {
                margin-bottom: 1.5rem;
                color: #e2e8f0;
            }
            
            .modal-actions {
                display: flex;
                justify-content: space-between;
            }
            
            .btn-cancel {
                background-color: #718096;
                color: white;
            }
            
            .btn-cancel:hover {
                background-color: #4a5568;
            }
            
            /* Loading spinner */
            .spinner {
                border: 4px solid rgba(0, 0, 0, 0.1);
                width: 36px;
                height: 36px;
                border-radius: 50%;
                border-left-color: #4299e1;
                animation: spin 1s linear infinite;
                display: inline-block;
                margin-right: 0.5rem;
                vertical-align: middle;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Loading state */
            .is-loading {
                position: relative;
                pointer-events: none;
            }
            
            .is-loading::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.5);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10;
            }
            
            /* Preview iframe */
            .preview-iframe {
                width: 100%;
                height: 100%;
                border: none;
            }
            
            /* Error message styling */
            .error-message {
                color: #fc8181;
                font-size: 0.875rem;
                margin-top: 0.5rem;
            }
            
            .success-message {
                color: #48bb78;
                font-size: 0.875rem;
                margin-top: 0.5rem;
            }
        """),
        
        # Form container
        Div(
            H2("Upload Interactive to Gallery", cls="form-title"),
            
            Form(
                # Form grid layout
                Div(
                    # Left column
                    Div(
                        H3("Interactive Details", cls="section-title"),
                        
                        # Title field
                        Div(
                            Label("Title of Interactive", fr="interactive-title"),
                            Input(
                                type="text",
                                id="interactive-title",
                                name="interactive-title",
                                placeholder="Enter a descriptive title",
                                required=True,
                                cls="form-control"
                            ),
                            cls="form-group"
                        ),
                        
                        # Author field
                        Div(
                            Label("Author Name", fr="interactive-author"),
                            Input(
                                type="text",
                                id="interactive-author",
                                name="interactive-author",
                                placeholder="Enter your name",
                                required=True,
                                cls="form-control"
                            ),
                            cls="form-group"
                        ),
                        
                        # Email field (optional)
                        Div(
                            Label("Email Address (Optional)", fr="interactive-email"),
                            Input(
                                type="email",
                                id="interactive-email",
                                name="interactive-email",
                                placeholder="Enter your email address",
                                cls="form-control"
                            ),
                            cls="form-group"
                        ),
                        
                        # Level selection
                        Div(
                            Label("Education Level", fr="interactive-level"),
                            Select(
                                *level_options,
                                id="interactive-level",
                                name="interactive-level",
                                required=True,
                                cls="form-control",
                                onchange="updateSubjectOptions()"
                            ),
                            cls="form-group"
                        ),
                        
                        # Subject selection
                        Div(
                            Label("Subject", fr="interactive-subject"),
                            Select(
                                Option("Select a level first", value="", disabled=True, selected=True),
                                id="interactive-subject",
                                name="interactive-subject",
                                required=True,
                                cls="form-control"
                            ),
                            cls="form-group"
                        ),
                        
                        # Zip file upload
                        Div(
                            Label("Upload ZIP file", fr="interactive-zip"),
                            Div(
                                Input(
                                    type="file",
                                    id="interactive-zip",
                                    name="interactive-zip",
                                    accept=".zip",
                                    required=True,
                                    cls="form-control",
                                    onchange="validateZipFile(this)"
                                ),
                                Div(id="zip-validation-message", cls="text-sm text-red-500 mt-1"),
                                cls="mb-2"
                            ),
                            Button(
                                "Preview Interactive",
                                type="button",
                                id="preview-btn",
                                cls="btn btn-primary",
                                onclick="previewInteractive()"
                            ),
                            cls="form-group"
                        ),
                        
                        # Base prompt
                        Div(
                            Label("Base Prompt Used", fr="interactive-prompt"),
                            Textarea(
                                placeholder="Enter the prompt used to create this interactive...",
                                id="interactive-prompt",
                                name="interactive-prompt",
                                rows=6,
                                cls="form-control"
                            ),
                            cls="form-group"
                        ),
                        
                        cls="form-section"
                    ),
                    
                    # Right column
                    Div(
                        # Preview section
                        H3("Preview", cls="section-title"),
                        Div(
                            Div(
                                P("Interactive preview will appear here after you upload and preview a ZIP file.", cls="preview-placeholder"),
                                id="preview-container",
                                cls="preview-container"
                            ),
                            cls="form-group"
                        ),
                        
                        # Reference images section
                        H3("Reference Images (Optional)", cls="section-title"),
                        P("Upload up to 5 reference images that were used to create this interactive.", cls="text-sm text-gray-400 mb-2"),
                        
                        # Image upload grid
                        Div(
                            *[
                                Div(
                                    Label(f"Image {i+1}", fr=f"ref-image-{i}", cls="mb-1 block text-center"),
                                    Input(
                                        type="file",
                                        id=f"ref-image-{i}",
                                        name=f"ref-image-{i}",
                                        accept="image/*",
                                        cls="hidden",
                                        onchange=f"handleImageUpload({i})"
                                    ),
                                    Div(
                                        Svg(
                                            Path(d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round"),
                                            viewBox="0 0 24 24",
                                            cls="w-6 h-6 mx-auto text-gray-400"
                                        ),
                                        P("Upload", cls="text-sm text-gray-400 mt-1"),
                                        id=f"upload-label-{i}",
                                        cls="cursor-pointer"
                                    ),
                                    Img(src="", alt="Preview", id=f"image-preview-{i}", cls="uploader-preview"),
                                    Div(
                                        Button(
                                            Svg(
                                                Path(d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16", stroke="currentColor", stroke_width="2", stroke_linecap="round", stroke_linejoin="round"),
                                                viewBox="0 0 24 24",
                                                cls="w-4 h-4"
                                            ),
                                            type="button",
                                            cls="bg-red-600 text-white p-1 rounded absolute top-1 right-1 hidden",
                                            id=f"remove-image-{i}",
                                            onclick=f"removeImage({i})"
                                        ),
                                        cls="relative"
                                    ),
                                    cls="uploader-item",
                                    id=f"uploader-{i}",
                                    onclick=f"document.getElementById('ref-image-{i}').click()"
                                ) for i in range(5)
                            ],
                            cls="uploader-grid"
                        ),
                        
                        cls="form-section"
                    ),
                    
                    cls="form-grid"
                ),
                
                # Submit button
                Div(
                    Button(
                        "Submit Interactive",
                        type="button",
                        id="submit-btn",
                        cls="btn btn-success btn-block",
                        onclick="confirmSubmit()"
                    ),
                    cls="mt-6"
                ),
                
                id="gallery-upload-form",
                cls="mt-4"
            ),
            
            # Confirmation modal
            Div(
                Div(
                    H3("Confirm Submission", cls="modal-title"),
                    Div(
                        P("Are you sure you want to submit this interactive to the gallery?"),
                        P("Once submitted, it will be reviewed before being published."),
                        cls="modal-body"
                    ),
                    Div(
                        Button(
                            "Cancel",
                            type="button",
                            cls="btn btn-cancel",
                            onclick="closeModal()"
                        ),
                        Button(
                            "Submit",
                            type="button",
                            cls="btn btn-success",
                            onclick="submitForm()"
                        ),
                        cls="modal-actions"
                    ),
                    cls="modal-content"
                ),
                id="confirm-modal",
                cls="modal"
            ),
            
            # JavaScript for form handling
            Script("""
                // Store all subjects data - using window to make it globally accessible
                if (typeof window.allSubjects === 'undefined') {
                    window.allSubjects = """ + subjects_json + """;
                } else {
                    console.log("allSubjects already defined, reusing existing variable");
                }
                
                // Store uploaded reference images
                if (typeof window.refImages === 'undefined') {
                    window.refImages = {
                        0: null,
                        1: null,
                        2: null,
                        3: null,
                        4: null
                    };
                } else {
                    console.log("refImages already defined, reusing existing variable");
                }
                
                // Initialize preview ID tracker
                if (typeof window.currentPreviewId === 'undefined') {
                    window.currentPreviewId = null;
                }
                
                // Update subject options based on selected level
                function updateSubjectOptions() {
                    const levelSelect = document.getElementById('interactive-level');
                    const subjectSelect = document.getElementById('interactive-subject');
                    
                    // Clear existing options
                    subjectSelect.innerHTML = '';
                    
                    // Get the selected level
                    const selectedLevel = levelSelect.value;
                    
                    // Determine which subjects array to use
                    let subjectsArray = [];
                    if (selectedLevel.startsWith('Primary')) {
                        subjectsArray = window.allSubjects.primary;
                    } else if (selectedLevel.startsWith('Secondary')) {
                        subjectsArray = window.allSubjects.secondary;
                    } else if (selectedLevel.startsWith('Junior College')) {
                        subjectsArray = window.allSubjects.jc_ci;
                    }
                    
                    // Add default option
                    const defaultOption = document.createElement('option');
                    defaultOption.text = 'Select a subject';
                    defaultOption.value = '';
                    defaultOption.disabled = true;
                    defaultOption.selected = true;
                    subjectSelect.add(defaultOption);
                    
                    // Add subject options
                    subjectsArray.forEach(subject => {
                        const option = document.createElement('option');
                        option.text = subject;
                        option.value = subject;
                        subjectSelect.add(option);
                    });
                }
                
                // Validate ZIP file
                function validateZipFile(fileInput) {
                    const zipValidationMessage = document.getElementById('zip-validation-message');
                    
                    if (fileInput.files.length === 0) {
                        zipValidationMessage.textContent = '';
                        return false;
                    }
                    
                    const file = fileInput.files[0];
                    
                    // Check file type
                    if (!file.name.toLowerCase().endsWith('.zip')) {
                        zipValidationMessage.textContent = 'Please upload a ZIP file.';
                        return false;
                    }
                    
                    // Check file size (max 50MB)
                    const maxSize = 50 * 1024 * 1024; // 50MB in bytes
                    if (file.size > maxSize) {
                        zipValidationMessage.textContent = 'ZIP file must be less than 50MB.';
                        return false;
                    }
                    
                    zipValidationMessage.textContent = '';
                    return true;
                }
                
                // Preview the interactive
                async function previewInteractive() {
                    const zipFile = document.getElementById('interactive-zip').files[0];
                    const previewContainer = document.getElementById('preview-container');
                    const previewBtn = document.getElementById('preview-btn');
                    
                    if (!zipFile) {
                        alert('Please select a ZIP file to preview.');
                        return;
                    }
                    
                    if (!validateZipFile(document.getElementById('interactive-zip'))) {
                        return;
                    }
                    
                    // Show loading state
                    previewBtn.disabled = true;
                    previewBtn.innerHTML = '<span class="spinner"></span> Processing...';
                    previewContainer.innerHTML = '<p class="text-center">Loading preview...</p>';
                    
                    try {
                        // Create form data with the zip file
                        const formData = new FormData();
                        formData.append('zipfile', zipFile);
                        
                        // Send request to preview API
                        const response = await fetch('/api/html5/preview-content-from-zip', {
                            method: 'POST',
                            body: formData
                        });
                        
                        if (!response.ok) {
                            throw new Error('Failed to preview interactive');
                        }
                        
                        // Get the HTML content from the response
                        const htmlContent = await response.text();
                        
                        // Create a Blob from the HTML content
                        const blob = new Blob([htmlContent], { type: 'text/html' });
                        
                        // Create a URL for the Blob
                        const blobUrl = URL.createObjectURL(blob);
                        
                        // Create and append iframe to display the content
                        const iframe = document.createElement('iframe');
                        iframe.className = 'preview-iframe';
                        iframe.sandbox = 'allow-scripts';  // Keep sandbox settings for security
                        
                        // Set the src to the blob URL
                        iframe.src = blobUrl;
                        
                        // Clear and add iframe to the container
                        previewContainer.innerHTML = '';
                        previewContainer.appendChild(iframe);
                        
                        // Clean up the blob URL when iframe is loaded
                        iframe.onload = () => {
                            // Small delay to ensure content is fully loaded
                            setTimeout(() => {
                                URL.revokeObjectURL(blobUrl);
                            }, 1000);
                        };
                        
                    } catch (error) {
                        console.error('Error previewing interactive:', error);
                        previewContainer.innerHTML = `
                            <div class="text-center text-red-500">
                                <p>Error previewing interactive.</p>
                                <p class="text-sm">${error.message}</p>
                            </div>
                        `;
                    } finally {
                        // Reset button state
                        previewBtn.disabled = false;
                        previewBtn.innerHTML = 'Preview Interactive';
                    }
                }
                
                // Handle reference image upload
                async function handleImageUpload(index) {
                    const fileInput = document.getElementById(`ref-image-${index}`);
                    const uploaderItem = document.getElementById(`uploader-${index}`);
                    const imagePreview = document.getElementById(`image-preview-${index}`);
                    const removeButton = document.getElementById(`remove-image-${index}`);
                    
                    if (fileInput.files.length === 0) {
                        return;
                    }
                    
                    const file = fileInput.files[0];
                    
                    // Check if it's an image
                    if (!file.type.startsWith('image/')) {
                        alert('Please upload an image file.');
                        fileInput.value = '';
                        return;
                    }
                    
                    // Check file size (max 5MB)
                    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
                    if (file.size > maxSize) {
                        alert('Image must be less than 5MB.');
                        fileInput.value = '';
                        return;
                    }
                    
                    try {
                        // Create a preview
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            imagePreview.src = e.target.result;
                            uploaderItem.classList.add('has-image');
                            removeButton.classList.remove('hidden');
                        };
                        reader.readAsDataURL(file);
                        
                        // Create form data for upload
                        const formData = new FormData();
                        formData.append('filename', `ref-image-${Date.now()}-${file.name}`);
                        formData.append('file', file);
                        
                        // Upload to blob storage
                        const response = await fetch('/api/blob/upload?filename=' + encodeURIComponent(file.name), {
                            method: 'POST',
                            body: file
                        });
                        
                        if (!response.ok) {
                            throw new Error('Failed to upload image');
                        }
                        
                        const data = await response.json();
                        
                        // Store the image URL for submission
                        window.refImages[index] = data.url;
                        
                    } catch (error) {
                        console.error('Error uploading image:', error);
                        alert('Error uploading image. Please try again.');
                        
                        // Reset the file input and preview
                        fileInput.value = '';
                        imagePreview.src = '';
                        uploaderItem.classList.remove('has-image');
                        removeButton.classList.add('hidden');
                        window.refImages[index] = null;
                    }
                }
                
                // Remove a reference image
                function removeImage(index) {
                    const fileInput = document.getElementById(`ref-image-${index}`);
                    const uploaderItem = document.getElementById(`uploader-${index}`);
                    const imagePreview = document.getElementById(`image-preview-${index}`);
                    const removeButton = document.getElementById(`remove-image-${index}`);
                    
                    // Reset the file input
                    fileInput.value = '';
                    
                    // Reset the preview
                    imagePreview.src = '';
                    uploaderItem.classList.remove('has-image');
                    removeButton.classList.add('hidden');
                    
                    // Clear the stored reference
                    window.refImages[index] = null;
                    
                    // Stop event propagation to prevent reopening file dialog
                    event.stopPropagation();
                }
                
                // Show the confirmation modal
                function confirmSubmit() {
                    // Validate required fields
                    const title = document.getElementById('interactive-title').value;
                    const author = document.getElementById('interactive-author').value;
                    const level = document.getElementById('interactive-level').value;
                    const subject = document.getElementById('interactive-subject').value;
                    const zipFile = document.getElementById('interactive-zip').files[0];
                    
                    if (!title || !author || !level || !subject || !zipFile) {
                        alert('Please fill in all required fields and upload a ZIP file.');
                        return;
                    }
                    
                    // Show confirmation modal
                    document.getElementById('confirm-modal').classList.add('show');
                }
                
                // Close the confirmation modal
                function closeModal() {
                    document.getElementById('confirm-modal').classList.remove('show');
                }
                
                // Submit the form
                async function submitForm() {
                    const submitBtn = document.querySelector('#confirm-modal .btn-success');
                    const cancelBtn = document.querySelector('#confirm-modal .btn-cancel');
                    
                    // Disable buttons during submission
                    submitBtn.disabled = true;
                    cancelBtn.disabled = true;
                    submitBtn.innerHTML = '<span class="spinner"></span> Submitting...';
                    
                    try {
                        // Get form values
                        const title = document.getElementById('interactive-title').value;
                        const author = document.getElementById('interactive-author').value;
                        const email = document.getElementById('interactive-email').value;
                        const level = document.getElementById('interactive-level').value;
                        const subject = document.getElementById('interactive-subject').value;
                        const prompt = document.getElementById('interactive-prompt').value;
                        const zipFile = document.getElementById('interactive-zip').files[0];
                        
                        // Upload ZIP file to blob storage
                        const zipFormData = new FormData();
                        zipFormData.append('filename', `interactive-${Date.now()}-${zipFile.name}`);
                        zipFormData.append('file', zipFile);
                        
                        const zipResponse = await fetch('/api/blob/upload?filename=' + encodeURIComponent(zipFile.name), {
                            method: 'POST',
                            body: zipFile
                        });
                        
                        if (!zipResponse.ok) {
                            throw new Error('Failed to upload ZIP file');
                        }
                        
                        const zipData = await zipResponse.json();
                        
                        // Create metadata object
                        const metadata = {
                            title: title,
                            author: author,
                            email: email || null,
                            level: level,
                            subject: subject,
                            prompt: prompt || null,
                            galleryType: '""" + gallery_type + """',
                            zipUrl: zipData.url,
                            referenceImages: Object.values(window.refImages).filter(url => url !== null),
                            dateSubmitted: new Date().toISOString()
                        };
                        
                        // Save metadata
                        const metadataResponse = await fetch('/api/gallery/save-metadata', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify(metadata)
                        });
                        
                        if (!metadataResponse.ok) {
                            throw new Error('Failed to save submission metadata');
                        }
                        
                        // Show success message and reset form
                        alert('Interactive submitted successfully!');
                        document.getElementById('gallery-upload-form').reset();
                        document.getElementById('preview-container').innerHTML = '<p class="preview-placeholder">Interactive preview will appear here after you upload and preview a ZIP file.</p>';
                        
                        // Reset reference images
                        for (let i = 0; i < 5; i++) {
                            const uploaderItem = document.getElementById(`uploader-${i}`);
                            const imagePreview = document.getElementById(`image-preview-${i}`);
                            const removeButton = document.getElementById(`remove-image-${i}`);
                            
                            imagePreview.src = '';
                            uploaderItem.classList.remove('has-image');
                            removeButton.classList.add('hidden');
                            window.refImages[i] = null;
                        }
                        
                        // Close the modal
                        closeModal();
                        
                    } catch (error) {
                        console.error('Error submitting form:', error);
                        alert('Error submitting form: ' + error.message);
                    } finally {
                        // Reset button state
                        submitBtn.disabled = false;
                        cancelBtn.disabled = false;
                        submitBtn.innerHTML = 'Submit';
                    }
                }
                
                // Initialize form
                document.addEventListener('DOMContentLoaded', function() {
                    // Nothing to do on load currently
                });
            """),
            
            cls="upload-form-container"
        )
    )

