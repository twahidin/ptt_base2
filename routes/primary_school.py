from fasthtml.common import *
from components.gallery_upload_form import create_gallery_upload_form
from components.gallery_submissions_grid import create_gallery_submissions_grid
from routes.api import get_submissions_by_gallery_type

def routes(router):
    @router.get("/primary")
    def primary_school(req):
        return Div(
            H2("Primary School Interactives Gallery"),
            P("Select a subject category from the menu on the left to browse interactive resources for primary school students."),
            H3("Share Your Interactive", cls="text-xl font-bold text-blue-500 mt-8 mb-4"),
            P("Have you created an excellent interactive for primary school students? Share it with the community!", 
              cls="text-gray-400 mb-4"),
            create_gallery_upload_form(gallery_type="primary"),
            cls="menu-content"
        )
        
    @router.get("/primary/math")
    def primary_math(req):
        # Get submissions for primary school math
        primary_submissions = get_submissions_by_gallery_type("primary")
        # Filter further by subject (case-insensitive contains match)
        math_submissions = [s for s in primary_submissions if "math" in s.get("subject", "").lower()]
        
        return Div(
            H3("Primary School Math Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(math_submissions),
            
            cls="submenu-content-area"
        )
    
    @router.get("/primary/science")
    def primary_science(req):
        # Get submissions for primary school science
        primary_submissions = get_submissions_by_gallery_type("primary")
        # Filter further by subject (case-insensitive contains match)
        science_submissions = [s for s in primary_submissions if "science" in s.get("subject", "").lower()]
        
        return Div(
            H3("Primary School Science Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(science_submissions),
            
            cls="submenu-content-area"
        )
    
    @router.get("/primary/languages")
    def primary_languages(req):
        # Get submissions for primary school languages
        primary_submissions = get_submissions_by_gallery_type("primary")
        # Filter further by subject (case-insensitive contains match for language-related subjects)
        language_keywords = ["english", "chinese", "malay", "tamil", "language"]
        language_submissions = [
            s for s in primary_submissions 
            if any(keyword in s.get("subject", "").lower() for keyword in language_keywords)
        ]
        
        return Div(
            H3("Primary School Languages Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(language_submissions),
            
            cls="submenu-content-area"
        ) 