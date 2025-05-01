from fasthtml.common import *
import json

def create_gallery_submissions_grid(submissions):
    """
    Create a grid to display gallery submissions.
    
    Parameters:
    submissions (list): List of submission metadata
    """
    if not submissions:
        return Div(
            P("No submissions found. Be the first to contribute an interactive!", cls="text-gray-400"),
            cls="empty-submissions-message my-8 text-center"
        )
    
    return Div(
        # Styles for gallery grid
        Style("""
            .gallery-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 1.5rem;
                margin-top: 2rem;
                margin-bottom: 2rem;
            }
            
            .gallery-card {
                background-color: #1a202c;
                border: 1px solid #2d3748;
                border-radius: 8px;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                transition: transform 0.2s;
            }
            
            .gallery-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            }
            
            .gallery-title {
                font-size: 1.25rem;
                font-weight: 600;
                color: #4299e1;
                margin-bottom: 0.5rem;
            }
            
            .gallery-details {
                padding: 1rem;
                flex: 1;
            }
            
            .gallery-metadata {
                font-size: 0.875rem;
                color: #a0aec0;
                margin-bottom: 0.75rem;
            }
            
            .gallery-prompt {
                font-size: 0.875rem;
                color: #cbd5e0;
                margin-top: 1rem;
                margin-bottom: 1rem;
                overflow: hidden;
                display: -webkit-box;
                -webkit-line-clamp: 3;
                -webkit-box-orient: vertical;
                line-height: 1.4;
            }
            
            .gallery-images {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 1rem;
            }
            
            .gallery-image-thumbnail {
                width: 60px;
                height: 60px;
                object-fit: cover;
                border-radius: 4px;
                border: 1px solid #4a5568;
            }
            
            .gallery-actions {
                display: flex;
                justify-content: space-between;
                margin-top: 1rem;
                padding-top: 1rem;
                border-top: 1px solid #2d3748;
            }
            
            .gallery-download-btn {
                background-color: #4299e1;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                font-size: 0.875rem;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                transition: background-color 0.2s;
            }
            
            .gallery-download-btn:hover {
                background-color: #3182ce;
            }
            
            .gallery-preview-btn {
                background-color: #2d3748;
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                font-size: 0.875rem;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                transition: background-color 0.2s;
            }
            
            .gallery-preview-btn:hover {
                background-color: #4a5568;
            }
            
            /* Preview Modal Styles */
            .preview-modal {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0, 0, 0, 0.7);
                z-index: 1000;
                align-items: center;
                justify-content: center;
            }
            
            .preview-modal.show {
                display: flex;
            }
            
            .preview-modal-content {
                background-color: #1a202c;
                border-radius: 8px;
                width: 90%;
                max-width: 900px;
                height: 80%;
                position: relative;
                overflow: hidden;
            }
            
            .preview-modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.75rem 1rem;
                background-color: #2d3748;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            
            .preview-modal-title {
                color: white;
                font-weight: 600;
                margin: 0;
            }
            
            .preview-modal-close {
                background: none;
                border: none;
                color: white;
                font-size: 1.5rem;
                cursor: pointer;
                padding: 0;
                line-height: 1;
            }
            
            .preview-modal-body {
                height: calc(100% - 3rem);
                overflow: hidden;
            }
            
            .preview-iframe {
                width: 100%;
                height: 100%;
                border: none;
                background-color: white;
            }
            
            .preview-loading {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: white;
            }
            
            .preview-spinner {
                border: 4px solid rgba(255, 255, 255, 0.3);
                border-top: 4px solid #4299e1;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin-bottom: 1rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            /* Controls for the preview */
            .preview-controls {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 1rem;
                background-color: #1a202c;
                border-top: 1px solid #2d3748;
            }
            
            .preview-control-btn {
                background-color: #2d3748;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 0.25rem 0.75rem;
                font-size: 0.875rem;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .preview-control-btn:hover {
                background-color: #4a5568;
            }
        """),
        
        # Gallery grid container
        Div(
            # For each submission, create a card
            *[
                Div(
                    # Card details
                    Div(
                        H4(submission.get('title', 'Untitled'), cls="gallery-title"),
                        Div(
                            P(f"Author: {submission.get('author', 'Not specified')}", cls="mb-1"),
                            P(f"Email: {submission.get('email', 'Not provided')}", cls="mb-1"),
                            P(f"Level: {submission.get('level', 'Not specified')}", cls="mb-1"),
                            P(f"Subject: {submission.get('subject', 'Not specified')}", cls="mb-1"),
                            cls="gallery-metadata"
                        ),
                        
                        # Display prompt if available
                        (
                            Div(
                                H5("Base Prompt:", cls="text-sm font-semibold text-gray-400"),
                                P(submission.get('prompt', ''), cls="gallery-prompt"),
                                cls="mt-3"
                            )
                            if submission.get('prompt') 
                            else ""
                        ),
                        
                        # Display description if available
                        (
                            Div(
                                H5("Description:", cls="text-sm font-semibold text-gray-400"),
                                P(submission.get('description', ''), cls="gallery-prompt"),
                                cls="mt-3"
                            )
                            if submission.get('description') 
                            else ""
                        ),
                        
                        # Display reference images if available
                        (
                            Div(
                                H5("Reference Images:", cls="text-sm font-semibold text-gray-400 mb-2"),
                                Div(
                                    *[
                                        A(
                                            Img(src=img, alt="Reference Image", cls="gallery-image-thumbnail"),
                                            href=img,
                                            target="_blank",
                                            title="View full size"
                                        )
                                        for img in submission.get('referenceImages', [])[:4]  # Limit to first 4 images
                                    ],
                                    (
                                        Div(
                                            f"+{len(submission.get('referenceImages', [])) - 4} more",
                                            cls="gallery-image-thumbnail flex items-center justify-center text-sm text-gray-400"
                                        )
                                        if len(submission.get('referenceImages', [])) > 4
                                        else ""
                                    ),
                                    cls="gallery-images"
                                ),
                                cls="mt-3"
                            )
                            if submission.get('referenceImages') and len(submission.get('referenceImages', [])) > 0
                            else ""
                        ),
                        
                        # Action buttons
                        Div(
                            A(
                                "Download",
                                href=submission.get('zipUrl', '#'),
                                cls="gallery-download-btn",
                                target="_blank"
                            ),
                            A(
                                "Preview",
                                href="#",
                                cls="gallery-preview-btn",
                                data_id=str(submissions.index(submission)),
                                data_title=submission.get('title', 'Interactive Preview'),
                                onclick=f"previewInteractive(this); return false;"
                            ),
                            cls="gallery-actions"
                        ),
                        cls="gallery-details"
                    ),
                    cls="gallery-card"
                )
                for submission in submissions
            ],
            cls="gallery-grid"
        ),
        
        # Preview Modal
        Div(
            Div(
                Div(
                    H3("Interactive Preview", id="preview-modal-title", cls="preview-modal-title"),
                    Button(
                        "×",
                        cls="preview-modal-close",
                        onclick="closePreviewModal()"
                    ),
                    cls="preview-modal-header"
                ),
                Div(
                    id="preview-modal-body",
                    cls="preview-modal-body"
                ),
                Div(
                    Button("Refresh", cls="preview-control-btn", onclick="refreshPreview()"),
                    Button("Open in New Tab", cls="preview-control-btn", id="open-in-new-tab", onclick="openInNewTab()"),
                    cls="preview-controls"
                ),
                cls="preview-modal-content"
            ),
            id="preview-modal",
            cls="preview-modal"
        ),
        
        # JavaScript for preview functionality
        Script("""
            // Store current submission ID being previewed
            if (typeof window.currentPreviewId === 'undefined') {
                window.currentPreviewId = null;
            }
            
            function previewInteractive(element) {
                // Get the submission ID from the data attribute
                const submissionId = element.getAttribute("data-id");
                const submissionTitle = element.getAttribute("data-title");
                
                // Store current ID for refresh functionality
                window.currentPreviewId = submissionId;
                
                // Update modal title
                document.getElementById("preview-modal-title").textContent = submissionTitle;
                
                // Update open in new tab button
                document.getElementById("open-in-new-tab").onclick = function() {
                    window.open(`/api/gallery/preview/${submissionId}`, '_blank');
                };
                
                // Show the modal
                const modal = document.getElementById('preview-modal');
                modal.classList.add('show');
                
                // Show loading state
                const modalBody = document.getElementById('preview-modal-body');
                modalBody.innerHTML = `
                    <div class="preview-loading">
                        <div class="preview-spinner"></div>
                        <p>Loading interactive...</p>
                    </div>
                `;
                
                // Create an iframe to load the preview
                const iframe = document.createElement('iframe');
                iframe.className = 'preview-iframe';
                iframe.allowFullscreen = true;
                // Add allow-same-origin to fix postMessage errors but keep other security restrictions
                iframe.sandbox = 'allow-scripts allow-same-origin allow-popups allow-forms allow-modals';
                iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
                
                // Set the iframe src directly to the preview endpoint
                // Add cache buster to prevent caching
                iframe.src = `/api/gallery/preview/${submissionId}?cacheBust=${Date.now()}`;
                
                // Clear container and add iframe
                modalBody.innerHTML = '';
                modalBody.appendChild(iframe);
                
                // Add load event handler
                iframe.onerror = () => {
                    modalBody.innerHTML = `
                        <div class="preview-loading">
                            <p>Error loading preview. Please try again.</p>
                        </div>
                    `;
                };
            }
            
            function refreshPreview() {
                if (window.currentPreviewId) {
                    // Show loading state
                    const modalBody = document.getElementById('preview-modal-body');
                    modalBody.innerHTML = `
                        <div class="preview-loading">
                            <div class="preview-spinner"></div>
                            <p>Refreshing interactive...</p>
                        </div>
                    `;
                    
                    // Create an iframe to load the preview
                    const iframe = document.createElement('iframe');
                    iframe.className = 'preview-iframe';
                    iframe.allowFullscreen = true;
                    // Add allow-same-origin to fix postMessage errors but keep other security restrictions
                    iframe.sandbox = 'allow-scripts allow-same-origin allow-popups allow-forms allow-modals';
                    iframe.allow = "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture";
                    
                    // Add cache-busting parameter to force reload
                    const cacheBuster = `?cacheBust=${Date.now()}`;
                    
                    // Set the iframe src directly to the preview endpoint
                    iframe.src = `/api/gallery/preview/${window.currentPreviewId}${cacheBuster}`;
                    
                    // Clear container and add iframe
                    modalBody.innerHTML = '';
                    modalBody.appendChild(iframe);
                    
                    // Add load event handler
                    iframe.onerror = () => {
                        modalBody.innerHTML = `
                            <div class="preview-loading">
                                <p>Error refreshing preview. Please try again.</p>
                            </div>
                        `;
                    };
                }
            }
            
            function openInNewTab() {
                if (window.currentPreviewId) {
                    window.open(`/api/gallery/preview/${window.currentPreviewId}`, '_blank');
                }
            }
            
            function closePreviewModal() {
                const modal = document.getElementById('preview-modal');
                modal.classList.remove('show');
                
                // Clear the iframe content when closing to stop any running code/audio
                document.getElementById('preview-modal-body').innerHTML = '';
                window.currentPreviewId = null;
            }
            
            // Close modal when clicking outside the content
            document.getElementById('preview-modal').addEventListener('click', function(event) {
                if (event.target === this) {
                    closePreviewModal();
                }
            });
            
            // Close modal with Escape key
            document.addEventListener('keydown', function(event) {
                if (event.key === 'Escape' && document.getElementById('preview-modal').classList.contains('show')) {
                    closePreviewModal();
                }
            });
        """),
        
        cls="gallery-container"
    ) 