from fasthtml.common import *
from dataclasses import dataclass
from components.forms import create_leonardo_form
import time
import json
import requests
import base64
from dotenv import load_dotenv
load_dotenv()

# Load environment variables
if os.getenv("LEONARDO_API_KEY") is None:
    os.environ["LEONARDO_API_KEY"] = ""
else:
    os.environ["LEONARDO_API_KEY"] = os.getenv("LEONARDO_API_KEY")

@dataclass
class LeonardoAIConfig:
    api_key: str
    prompt: str
    num_images: int = 4
    preset_style: str = "DYNAMIC"
    height: int = 768
    width: int = 1024
    model_id: str = "b24e16ff-06e3-43eb-8d33-4416c2d75876"

def routes(rt):
    @rt("/menuA")
    def get(req):
        api_key = os.environ["LEONARDO_API_KEY"]
        return Titled("Leonardo AI Generator",
            Link(rel="stylesheet", href="public/static/css/styles.css"),
            create_leonardo_form(api_key)
        )

    @rt("/input-type-change")
    async def post(req):
        form = await req.form()
        input_type = form.get('input_type')
        
        if input_type == 'text':
            return Div(
                Label("Text Prompt:"),
                Textarea("", 
                        id='prompt', 
                        name='prompt', 
                        placeholder='Enter your prompt',
                        rows=3),
                id="text-input",
                cls="prompt-input"
            )
        else:  # image upload
            return Div(
                Label("Upload Image:"),
                Input(
                    type="file",
                    name="image_file",
                    accept="image/*",
                    id="image-input",
                    cls="file-input block w-full mb-4",
                    hx_trigger="change",
                    hx_post="/preview-image",
                    hx_target="#image-preview",
                    hx_encoding="multipart/form-data"
                ),
                Div(id="image-preview", cls="mt-4"),
                id="image-upload"
            )

    @rt("/preview-image")
    async def post(req):
        form = await req.form()
        file = form.get('image_file')
        if file and hasattr(file, 'file'):
            content = await file.read()
            base64_image = base64.b64encode(content).decode('utf-8')
            return Img(
                src=f"data:image/jpeg;base64,{base64_image}",
                alt="Preview",
                cls="max-w-sm h-auto rounded"
            )
        return ""

    @rt("/clear-results")
    def post():
        return ""  # Returns empty content to clear the results div

    @rt("/api/leonardo/generate")
    async def post(req):
        form = await req.form()
        try:
            # Validate inputs
            api_key = form.get('api_key', '').strip()
            if not api_key:
                return Div("Please configure your Leonardo AI API key first", 
                        cls="error alert alert-warning")
            
            # Get form parameters
            num_images = int(form.get('num_images', 4))
            preset_style = form.get('preset_style', 'DYNAMIC')
            height = int(form.get('height', 768))
            width = int(form.get('width', 1024))
            model_id = form.get('model_id', 'b24e16ff-06e3-43eb-8d33-4416c2d75876')
            
            # Initialize image data
            image_id = None
            prompt = form.get('prompt', '').strip()
            
            # Handle image upload if present
            if 'image_file' in form:
                image_file = form['image_file']
                if image_file and hasattr(image_file, 'file'):
                    # Get file extension
                    filename = image_file.filename
                    extension = filename.split('.')[-1].lower()
                    
                    # Get presigned URL for upload
                    init_url = "https://cloud.leonardo.ai/api/rest/v1/init-image"
                    init_payload = {"extension": extension}
                    headers = {
                        "accept": "application/json",
                        "content-type": "application/json",
                        "authorization": f"Bearer {api_key}"
                    }
                    
                    init_response = requests.post(init_url, json=init_payload, headers=headers)
                    if not init_response.ok:
                        return Div("Failed to initialize image upload", 
                                cls="error alert alert-danger")
                    
                    # Parse upload details
                    upload_data = init_response.json()
                    upload_url = upload_data['uploadInitImage']['url']
                    fields = json.loads(upload_data['uploadInitImage']['fields'])
                    image_id = upload_data['uploadInitImage']['id']
                    
                    # Upload the image
                    files = {'file': await image_file.read()}
                    upload_response = requests.post(upload_url, data=fields, files=files)
                    if not upload_response.ok:
                        return Div("Failed to upload image", 
                                cls="error alert alert-danger")

            # Prepare generation payload
            url = "https://cloud.leonardo.ai/api/rest/v1/generations"
            payload = {
                "height": height,
                "width": width,
                "modelId": model_id,
                "num_images": num_images,
                "presetStyle": preset_style,
                "prompt": prompt,
            }

            if image_id:
                payload["imagePrompts"] = [image_id]

            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Bearer {api_key}"
            }
        
            # Start generation
            response = requests.post(url, json=payload, headers=headers)
            if not response.ok:
                error_msg = response.json().get('message', response.text)
                return Div(f"API Error: {error_msg}", 
                        cls="error alert alert-danger")

            # Get generation ID and wait for results
            generation_data = response.json()
            if 'sdGenerationJob' not in generation_data:
                return Div("Unexpected API response format", 
                        cls="error alert alert-danger")
                
            generation_id = generation_data['sdGenerationJob']['generationId']
            
            # Poll for results
            result_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generation_id}"
            max_attempts = 30
            
            for _ in range(max_attempts):
                time.sleep(2)  # Wait between polls
                result_response = requests.get(result_url, headers=headers)
                
                if result_response.ok:
                    generation_data = result_response.json()
                    if 'generations_by_pk' in generation_data:
                        image_urls = [img['url'] for img in generation_data['generations_by_pk']['generated_images']]
                        if image_urls:
                            # Return container with all generated images
                            return Div(
                                *[Img(src=url, alt="Generated image", cls="result-image") 
                                for url in image_urls],
                                id="leonardo-results",
                                cls="generated-images"
                            )
                
                elif result_response.status_code != 202:
                    return Div("Error retrieving generation results", 
                            cls="error alert alert-danger")

            return Div("Generation timed out. Please try again.", 
                    cls="error alert alert-warning")

        except Exception as e:
            print(f"Error in generation: {str(e)}")
            return Div(f"An error occurred: {str(e)}", 
                    cls="error alert alert-danger")
    
    # @rt("/api/leonardo/generate")
    # async def post(req):
    #     form = await req.form()
    #     try:
    #         api_key = form.get('api_key', '').strip()
    #         print("API Key:", api_key)
    #         if not api_key:
    #             return Div("Please configure your Leonardo AI API key first", 
    #                     cls="error alert alert-warning")
    #         prompt = form.get('prompt', '').strip()
    #         if not prompt:
    #             return Div("Please provide a prompt", 
    #                     cls="error alert alert-warning")
    #         num_images = int(form.get('num_images', 4))
    #         preset_style = form.get('preset_style', 'DYNAMIC')
    #         height = int(form.get('height', 768))
    #         width = int(form.get('width', 1024))
    #         model_id = form.get('model_id', 'b24e16ff-06e3-43eb-8d33-4416c2d75876')
            
    #         # Handle image upload if present
    #         image_data = None
    #         if form.get('use_image') == 'true':
    #             image_data = await handle_image_upload(form)

    #         url = "https://cloud.leonardo.ai/api/rest/v1/generations"
    #         payload = {
    #             "alchemy": True,
    #             "height": height,
    #             "width": width,
    #             "modelId": model_id,
    #             "num_images": num_images,
    #             "presetStyle": preset_style,
    #             "prompt": prompt,
    #         }

    #         if image_data:
    #             payload["imagePrompts"] = [image_data]

    #         headers = {
    #             "accept": "application/json",
    #             "content-type": "application/json",
    #             "authorization": f"Bearer {api_key}"
    #         }
        
    
    #         # Start generation
    #         response = requests.post(url, json=payload, headers=headers)
    #         generation_id = response.json()['sdGenerationJob']['generationId']
            
    #         # Return generation ID for polling
    #         return JSONResponse({"generation_id": generation_id})
    #     except Exception as e:
    #         return JSONResponse({"error": str(e)})
