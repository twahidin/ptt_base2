from fasthtml.common import *
from dataclasses import dataclass
import requests
# In routes/leonardo.py
from components.forms import create_leonardo_form 


# Leonardo AI API handlers
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
    @rt("/save-leonardo-key")
    async def post(req, sess):
        form = await req.form()
        api_key = form.get('api_key')
        if api_key:
            sess['leonardo_ai_key'] = api_key
        return RedirectResponse('/menuA', status_code=303)
    
    async def handle_image_upload(form_data):
        # Handle image upload logic here
        image_file = form_data.get('image_file')
        if image_file and image_file.file:
            # Process the uploaded image
            content = await image_file.read()
            # Convert to base64 or handle as needed
            return base64.b64encode(content).decode('utf-8')
        return None
        

    @rt("/menuA")
    def get(req, sess):
        api_key = sess.get('leonardo_ai_key', '')
        return create_leonardo_form(api_key)
        
    
    
    @rt("/api/leonardo/generate")
    async def post(req):
        form = await req.form()
        api_key = req.session.get('leonardo_ai_key')
        
        if not api_key:
            return JSONResponse({"error": "API key not set"})

        # Get form parameters
        prompt = form.get('prompt')
        num_images = int(form.get('num_images', 4))
        preset_style = form.get('preset_style', 'DYNAMIC')
        height = int(form.get('height', 768))
        width = int(form.get('width', 1024))
        model_id = form.get('model_id', 'b24e16ff-06e3-43eb-8d33-4416c2d75876')
        
        # Handle image upload if present
        image_data = None
        if form.get('use_image') == 'true':
            image_data = await handle_image_upload(form)

        url = "https://cloud.leonardo.ai/api/rest/v1/generations"
        payload = {
            "alchemy": True,
            "height": height,
            "width": width,
            "modelId": model_id,
            "num_images": num_images,
            "presetStyle": preset_style,
            "prompt": prompt,
        }

        if image_data:
            payload["imagePrompts"] = [image_data]

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {api_key}"
        }
        
        try:
            # Start generation
            response = requests.post(url, json=payload, headers=headers)
            generation_id = response.json()['sdGenerationJob']['generationId']
            
            # Return generation ID for polling
            return JSONResponse({"generation_id": generation_id})
        except Exception as e:
            return JSONResponse({"error": str(e)})
