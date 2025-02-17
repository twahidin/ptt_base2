from fasthtml.common import *
from dataclasses import dataclass
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
# In routes/stability.py
from components.forms import create_stability_form, create_stability_video_form
import requests
import time
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
            style_preset = form.get('style_preset', '')
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
            # Add style_preset to params if one was selected
            if style_preset =='No style':
                params["style_preset"] = ""
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
        create_stability_form(api_key)
        )
   
    @rt("/menuC")
    def get(req, sess):
        api_key = sess.get('stability_ai_key', '')
        return Titled("Stability AI Video Generator",
            Link(rel="stylesheet", href="/static/css/styles.css"),
            create_stability_video_form(api_key)
        )

    @rt("/api/stability/generate-video")
    async def post(req):
        try:
            form = await req.form()
            api_key = req.session.get('stability_ai_key')
            
            if not api_key:
                return Div("Please configure your Stability AI API key first", 
                        cls="error alert alert-warning")

            # Debug logging
            print("Received form data keys:", form.keys())
            print("All form data:", dict(form))
            
            # Get uploaded image
            upload_file = form.get('file')
            print("Upload file object:", upload_file)
            print("Upload file type:", type(upload_file))
            
            if not upload_file:
                return Div("No file was uploaded. Please select an image file.", 
                        cls="error alert alert-warning")
                        
            if not isinstance(upload_file, UploadFile):
                print("File is not an UploadFile instance")
                return Div("Invalid file format. Please try again.", 
                        cls="error alert alert-warning")
            
            # Get file data
            image_data = await upload_file.read()
            filename = upload_file.filename
            print(f"Successfully read file: {filename}")
            print(f"Image data length: {len(image_data)} bytes")

            # Determine content type from filename
            if filename.lower().endswith(('.jpg', '.jpeg')):
                content_type = 'image/jpeg'
            elif filename.lower().endswith('.png'):
                content_type = 'image/png'
            else:
                return Div("Please upload a JPEG or PNG image", 
                        cls="error alert alert-warning")

            # Get other form parameters
            seed = int(form.get('seed', '0'))
            cfg_scale = float(form.get('cfg_scale', '1.8'))
            motion_bucket_id = int(form.get('motion_bucket_id', '127'))

            # Initial request to start generation
            response = requests.post(
                "https://api.stability.ai/v2beta/image-to-video",
                headers={
                    "Authorization": f"Bearer {api_key}"
                },
                files={
                    "image": (filename, image_data, content_type)
                },
                data={
                    "seed": seed,
                    "cfg_scale": cfg_scale,
                    "motion_bucket_id": motion_bucket_id
                }
            )

            if not response.ok:
                error_msg = response.json().get('message', response.text)
                return Div(f"API Error: {error_msg}", 
                        cls="error alert alert-danger")

            generation_id = response.json().get('id')
            
            # Start polling for results
            max_attempts = 30  # 5 minutes maximum (10 second intervals)
            for attempt in range(max_attempts):
                time.sleep(10)  # Wait 10 seconds between polls
                
                result_response = requests.get(
                    f"https://api.stability.ai/v2beta/image-to-video/result/{generation_id}",
                    headers={
                        'Accept': 'application/json',
                        'Authorization': f"Bearer {api_key}"
                    }
                )

                if result_response.status_code == 200:
                    # Video is ready
                    video_data = result_response.json().get('video')
                    if video_data:
                        return Div(
                            Video(
                                Source(src=f"data:video/mp4;base64,{video_data}",
                                      type="video/mp4"),
                                controls=True,
                                autoplay=True,
                                loop=True,
                                cls="result-video"
                            ),
                            id="video-result",
                            cls="generated-video"
                        )
                elif result_response.status_code != 202:
                    # Error occurred
                    error_msg = result_response.json().get('message', 'Unknown error occurred')
                    return Div(f"Error retrieving video: {error_msg}",
                             cls="error alert alert-danger")

            return Div("Video generation timed out. Please try again.",
                      cls="error alert alert-warning")

        except Exception as e:
            print(f"Error in video generation: {str(e)}")
            return Div(f"An error occurred: {str(e)}", 
                    cls="error alert alert-danger")