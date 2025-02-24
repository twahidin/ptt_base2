from fasthtml.common import *
import base64
from pathlib import Path
import tempfile
import zipfile
import io
from components.forms import create_html5_form, create_zip_file

from dotenv import load_dotenv
load_dotenv()

#try and load the environment variables
if os.getenv("OPENAI_API_KEY") is None:
    os.environ["OPENAI_API_KEY"] = ""
else:
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

if os.getenv("ANTHROPIC_API_KEY") is None:
    os.environ["ANTHROPIC_API_KEY"] = ""
else:  
    os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")

def routes(rt):
    @rt('/menuD')
    def get(req):
        api_key = os.getenv("OPENAI_API_KEY")
        return Titled("HTML5 Project",
            Link(rel="stylesheet", href="static/css/styles.css"),
            create_html5_form(api_key)
        )         

    @rt('/upload')
    async def post(req):
        form = await req.form()
        project_file = form.get('project_zip')
        if project_file:
            # Process uploaded zip file
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_path = Path(tmpdir) / "project.zip"
                zip_path.write_bytes(await project_file.read())
                # Extract and process zip contents
                # Update session with extracted contents
                return "Project uploaded successfully!"
        return "No file uploaded"

    @rt('/download')
    def get(req):
        # Get current project state and create zip
        html = req.session.get('html', '')
        css = req.session.get('css', '')
        js = req.session.get('js', '')
        sprites = req.session.get('sprites', {})
        
        zip_data = create_zip_file(html, css, js, sprites)
        
        headers = {
            'Content-Type': 'application/zip',
            'Content-Disposition': 'attachment; filename="project.zip"'
        }
        return Response(zip_data, headers=headers)

    @rt('/preview')
    def post(html: str, css: str, js: str):
        """Update the preview with new code"""
        preview_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>{css}</style>
        </head>
        <body>
            {html}
            <script>{js}</script>
        </body>
        </html>
        """
        return preview_html
