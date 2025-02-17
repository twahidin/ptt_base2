from fasthtml.common import *

def create_progress_indicator():
    """Create a progress indicator component for Stability AI image generation"""
    return Div(
        # Progress Bar Container
        Div(
            # Progress Bar
            Div(
                Div(
                    cls="htmx-indicator bg-blue-500 h-4 rounded-full transition-all duration-500 w-full"
                ),
                cls="w-full max-w-md bg-gray-200 rounded-full h-4 mb-2"
            ),
            # Progress Text
            Div(
                "Generating your image...",
                cls="text-center text-sm text-gray-600 htmx-indicator"
            ),
            cls="progress-container flex flex-col items-center justify-center w-full p-4",
            style="display: none;"
        ),
        # Results Container
        Div(
            id="stability-results",
            cls="image-results mt-4"
        ),
        cls="results-container"
    )