from fasthtml.common import *
from dataclasses import dataclass
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
# In routes/stability.py
from components.forms import create_stability_form
import requests
from IPython.display import Image, display

@dataclass
class StabilityAIConfig:
    api_key: str
    prompt: str
    negative_prompt: str = ""
    aspect_ratio: str = "3:2"
    seed: int = 0
    output_format: str = "jpeg"
    control_strength: float = 0.7

def routes(rt):
    @rt("/save-stability-key")
    async def post(req, sess):
        form = await req.form()
        api_key = form.get('api_key')
        if api_key:
            sess['stability_ai_key'] = api_key
        return RedirectResponse('/menuB', status_code=303)

    @rt("/api/stability/generate")
    async def post(req):
        form = await req.form()
        api_key = req.session.get('stability_ai_key')
        
        if not api_key:
            return Div("Please configure your Stability AI API key first", 
                    cls="error alert alert-warning")

        try:
            # Get form parameters
            # Validate required fields
            prompt = form.get('prompt', '').strip()
            if not prompt:
                return Div("Please provide a prompt", 
                        cls="error alert alert-warning")
            negative_prompt = form.get('negative_prompt', '')
            aspect_ratio = form.get('aspect_ratio', '3:2')
            seed = int(form.get('seed', '0'))
            output_format = form.get('output_format', 'jpeg')
            control_strength = float(form.get('control_strength', '0.7'))
            
            # Handle image upload if present
            image_data = None
            control_type = form.get('control_type', 'none')
            if control_type in ['sketch', 'structure']:
                image_file = form.get('image_file')
                if image_file and image_file.file:
                    image_data = await image_file.read()
            
            # Set up API endpoint based on control type
            if control_type == 'none':
                host = "https://api.stability.ai/v2beta/stable-image/generate/ultra"
            else:
                host = f"https://api.stability.ai/v2beta/stable-image/control/{control_type}"
            
            # Prepare request parameters
            params = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "aspect_ratio": aspect_ratio,
                "seed": str(seed),
                "output_format": output_format
            }
            
            if control_type != 'none':
                params["control_strength"] = str(control_strength)
            
            headers = {
                "Accept": "image/*",
                "Authorization": f"Bearer {api_key}"
            }

            # Prepare multipart form data
            fields = params.copy()
            if image_data:
                fields["image"] = ("image.jpg", image_data, "image/jpeg")
            
            encoder = MultipartEncoder(fields=fields)
            headers["Content-Type"] = encoder.content_type

            # Make the request
            response = requests.post(host, headers=headers, data=encoder)
            
            if not response.ok:
                error_msg = response.json().get('message', response.text)
                return Div(f"API Error: {error_msg}", 
                        cls="error alert alert-danger")

            return Div(
                Img(
                    src=f"data:image/jpeg;base64,{base64.b64encode(response.content).decode()}", 
                    alt="Generated image",
                    cls="result-image"
                ),
                id="stability-results",
                cls="generated-image"
            )

        except Exception as e:
            return Div(f"An error occurred: {str(e)}", 
                    cls="error alert alert-danger")
        


    @rt("/menuB")
    def get(req, sess):
        api_key = sess.get('stability_ai_key', '')
        return Titled("Stability AI Generator",
        # Add CSS and JS to headers
        Link(rel="stylesheet", href="/static/css/styles.css"),
        Script(src="/static/js/stability.js"),
        create_stability_form(api_key)
        )
   