from fasthtml.common import *
from components.gallery_upload_form import create_gallery_upload_form
from components.gallery_submissions_grid import create_gallery_submissions_grid
from routes.api import get_submissions_by_gallery_type

def routes(router):
    @router.get("/jc_ci")
    def jc_ci(req):
        return Div(
            H2("JC & CI Interactives Gallery"),
            P("Select a subject category from the menu on the left to browse interactive resources for JC and CI students."),
            H3("Share Your Interactive", cls="text-xl font-bold text-blue-500 mt-8 mb-4"),
            P("Have you created an excellent interactive for JC & CI students? Share it with the community!", 
              cls="text-gray-400 mb-4"),
            create_gallery_upload_form(gallery_type="jc_ci"),
            cls="menu-content"
        )
        
    @router.get("/jc_ci/math")
    def jc_ci_math(req):
        # Get submissions for JC/CI math
        jc_ci_submissions = get_submissions_by_gallery_type("jc_ci")
        # Filter further by subject (case-insensitive contains match)
        math_keywords = ["math", "calculus", "statistics", "further mathematics"]
        math_submissions = [
            s for s in jc_ci_submissions 
            if any(keyword in s.get("subject", "").lower() for keyword in math_keywords)
        ]
        
        return Div(
            H3("JC & CI Math Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(math_submissions),
            
            cls="submenu-content-area"
        )
    
    @router.get("/jc_ci/science")
    def jc_ci_science(req):
        # Get submissions for JC/CI science
        jc_ci_submissions = get_submissions_by_gallery_type("jc_ci")
        # Filter further by subject (case-insensitive contains match)
        science_keywords = ["physics", "chemistry", "biology", "science"]
        science_submissions = [
            s for s in jc_ci_submissions 
            if any(keyword in s.get("subject", "").lower() for keyword in science_keywords)
        ]
        
        return Div(
            H3("JC & CI Science Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(science_submissions),
            
            cls="submenu-content-area"
        )
    
    @router.get("/jc_ci/humanities_arts")
    def jc_ci_humanities_arts(req):
        # Get submissions for JC/CI humanities & arts
        jc_ci_submissions = get_submissions_by_gallery_type("jc_ci")
        # Filter further by subject (case-insensitive contains match)
        humanities_keywords = ["economics", "history", "geography", "arts", "humanities"]
        humanities_submissions = [
            s for s in jc_ci_submissions 
            if any(keyword in s.get("subject", "").lower() for keyword in humanities_keywords)
        ]
        
        return Div(
            H3("JC & CI Humanities & Arts Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(humanities_submissions),
            
            cls="submenu-content-area"
        )
    
    @router.get("/jc_ci/languages")
    def jc_ci_languages(req):
        # Get submissions for JC/CI languages
        jc_ci_submissions = get_submissions_by_gallery_type("jc_ci")
        # Filter further by subject (case-insensitive contains match)
        language_keywords = ["general paper", "english", "chinese", "malay", "tamil", "literature", "language"]
        language_submissions = [
            s for s in jc_ci_submissions 
            if any(keyword in s.get("subject", "").lower() for keyword in language_keywords)
        ]
        
        return Div(
            H3("JC & CI Languages Interactives"),
            
            # Gallery submissions section
            H3("Community Submissions", style="font-size: 1.25rem; font-weight: bold; color: #4ade80; margin-top: 2rem; margin-bottom: 1rem;"),
            create_gallery_submissions_grid(language_submissions),
            
            cls="submenu-content-area"
        ) 