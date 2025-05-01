from fasthtml.common import *
from components.gallery_upload_form import create_gallery_upload_form
from components.gallery_submissions_grid import create_gallery_submissions_grid
from routes.api import get_submissions_by_gallery_type

def routes(router):
    @router.get("/secondary")
    def secondary_school(req):
        return Div(
            H2("Secondary School Interactives Gallery"),
            P("Select a subject category from the menu on the left to browse interactive resources for secondary school students."),
            H3("Share Your Interactive", cls="text-xl font-bold text-blue-500 mt-8 mb-4"),
            P("Have you created an excellent interactive for secondary school students? Share it with the community!", 
              cls="text-gray-400 mb-4"),
            create_gallery_upload_form(gallery_type="secondary"),
            cls="menu-content"
        )
        
    @router.get("/secondary/math")
    def secondary_math(req):
        # Get submissions for secondary school math
        secondary_submissions = get_submissions_by_gallery_type("secondary")
        # Filter further by subject (case-insensitive contains match)
        math_keywords = ["math", "algebra", "geometry", "trigonometry", "statistics"]
        math_submissions = [
            s for s in secondary_submissions 
            if any(keyword in s.get("subject", "").lower() for keyword in math_keywords)
        ]
        
        return Div(
            H3("Secondary School Math Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(math_submissions),
            
            cls="submenu-content-area"
        )
    
    @router.get("/secondary/science")
    def secondary_science(req):
        # Get submissions for secondary school science
        secondary_submissions = get_submissions_by_gallery_type("secondary")
        # Filter further by subject (case-insensitive contains match)
        science_keywords = ["science", "physics", "chemistry", "biology"]
        science_submissions = [
            s for s in secondary_submissions 
            if any(keyword in s.get("subject", "").lower() for keyword in science_keywords)
        ]
        
        return Div(
            H3("Secondary School Science Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(science_submissions),
            
            cls="submenu-content-area"
        )
    
    @router.get("/secondary/humanities")
    def secondary_humanities(req):
        # Get submissions for secondary school humanities
        secondary_submissions = get_submissions_by_gallery_type("secondary")
        # Filter further by subject (case-insensitive contains match)
        humanities_keywords = ["history", "geography", "social studies", "humanities"]
        humanities_submissions = [
            s for s in secondary_submissions 
            if any(keyword in s.get("subject", "").lower() for keyword in humanities_keywords)
        ]
        
        return Div(
            H3("Secondary School Humanities Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(humanities_submissions),
            
            cls="submenu-content-area"
        )
        
    @router.get("/secondary/craft_tech")
    def secondary_craft_tech(req):
        # Get submissions for secondary school craft & tech
        secondary_submissions = get_submissions_by_gallery_type("secondary")
        # Filter further by subject (case-insensitive contains match)
        tech_keywords = ["design", "technology", "computing", "food", "consumer"]
        tech_submissions = [
            s for s in secondary_submissions 
            if any(keyword in s.get("subject", "").lower() for keyword in tech_keywords)
        ]
        
        return Div(
            H3("Secondary School Craft & Technology Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(tech_submissions),
            
            cls="submenu-content-area"
        )
    
    @router.get("/secondary/languages")
    def secondary_languages(req):
        # Get submissions for secondary school languages
        secondary_submissions = get_submissions_by_gallery_type("secondary")
        # Filter further by subject (case-insensitive contains match)
        language_keywords = ["english", "chinese", "malay", "tamil", "language", "literature"]
        language_submissions = [
            s for s in secondary_submissions 
            if any(keyword in s.get("subject", "").lower() for keyword in language_keywords)
        ]
        
        return Div(
            H3("Secondary School Languages Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(language_submissions),
            
            cls="submenu-content-area"
        ) 