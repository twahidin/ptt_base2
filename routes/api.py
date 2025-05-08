from fasthtml.common import *
import json
import os
import io
import zipfile
import urllib.request
import tempfile
import shutil
import mimetypes
import base64
import re
import redis
import time
import http.client
from urllib.parse import urlparse
from pathlib import Path
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, HTMLResponse, FileResponse
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from datetime import datetime

# Check for blob token
BLOB_TOKEN = os.environ.get('BLOB_READ_WRITE_TOKEN')
if not BLOB_TOKEN:
    print("WARNING: BLOB_READ_WRITE_TOKEN environment variable not set. Blob storage will use mock implementation.")

# Check for Redis URL
REDIS_URL = os.environ.get('HTML5_REDIS_URL')
if not REDIS_URL:
    print("WARNING: HTML5_REDIS_URL environment variable not set. Using default localhost connection.")
    REDIS_URL = "redis://localhost:6379/0"

# Initialize Redis connection
try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()  # Test connection
    print("Connected to Redis successfully")
except Exception as e:
    print(f"Error connecting to Redis: {str(e)}. Using fallback in-memory storage.")
    redis_client = None

# Import Vercel Blob SDK if available
try:
    import vercel_blob
    # Only use vercel_blob if we have a token
    if BLOB_TOKEN:
        def blob_put(path, data, options=None):
            print(f"VERCEL: Uploading to {path} with options {options}")
            return vercel_blob.put(path, data, options)
    else:
        raise ImportError("BLOB_READ_WRITE_TOKEN not set")
except ImportError as e:
    print(f"Vercel Blob not available: {str(e)}. Using mock implementation.")
    # Mock implementation for development without Vercel Blob
    def blob_put(path, data, options=None):
        print(f"MOCK: Would upload to {path} with options {options}")
        return {
            "url": f"https://example-blob-storage.com/{path}",
            "pathname": path,
            "contentType": getattr(data, "content_type", "application/octet-stream"),
            "contentDisposition": None,
            "size": getattr(data, "size", 0)
        }

# Fallback in-memory storage for when Redis is not available
submissions_memory = []

# In-memory storage for extracted ZIP files
# Key: submission_id, Value: (temp_dir_path, files_dict)
extracted_zips = {}

# Function to validate if a URL exists without downloading the entire file
def url_exists(url):
    try:
        parsed_url = urlparse(url)
        conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=5)
        path = parsed_url.path
        if parsed_url.query:
            path += f"?{parsed_url.query}"
        
        conn.request("HEAD", path)
        response = conn.getresponse()
        conn.close()
        
        # Check if response is successful (2xx) or redirect (3xx)
        return 200 <= response.status < 400
    except Exception as e:
        print(f"Error checking URL {url}: {str(e)}")
        return False

# Function to validate a submission record's blob URLs
def validate_submission(submission):
    """
    Validates that all blob URLs in a submission record are accessible.
    
    Returns:
        bool: True if all URLs are valid, False if any are invalid
    """
    if not submission:
        return False
    
    # Check main ZIP URL
    zip_url = submission.get('zipUrl')
    if not zip_url or not url_exists(zip_url):
        print(f"Invalid ZIP URL in submission: {zip_url}")
        return False
    
    # Check reference image URLs
    reference_images = submission.get('referenceImages', [])
    for img_url in reference_images:
        if not url_exists(img_url):
            print(f"Invalid reference image URL in submission: {img_url}")
            return False
    
    return True

# Function to cleanup invalid submissions
def cleanup_invalid_submissions():
    """
    Scans all submissions in Redis and removes those with invalid blob URLs.
    
    Returns:
        tuple: (cleaned_count, total_count) - number of records cleaned up and total checked
    """
    if not redis_client:
        print("Redis not available, skipping cleanup")
        return 0, 0
    
    try:
        cleaned_count = 0
        submission_ids = redis_client.hkeys("submission")
        print(f"Checking {len(submission_ids)} submissions for validity...")
        
        for sid in submission_ids:
            try:
                submission_data = redis_client.hget("submission", sid)
                if submission_data:
                    submission = json.loads(submission_data)
                    if not validate_submission(submission):
                        # Delete invalid submission
                        redis_client.hdel("submission", sid)
                        print(f"Deleted invalid submission with ID {sid}")
                        cleaned_count += 1
            except Exception as e:
                print(f"Error processing submission {sid}: {str(e)}")
        
        print(f"Cleanup complete. Removed {cleaned_count} invalid submissions out of {len(submission_ids)}.")
        return cleaned_count, len(submission_ids)
    
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        return 0, 0

# Function to save submission to Redis
def save_submission(submission):
    if redis_client:
        try:
            # Get current submissions count for ID assignment
            submission_count = redis_client.get("submissions_count")
            if submission_count is None:
                submission_count = 0
            else:
                submission_count = int(submission_count)
            
            # Assign ID to submission
            submission_id = submission_count
            
            # Save the submission
            redis_client.hset("submission", submission_id, json.dumps(submission))
            
            # Increment submissions count
            redis_client.set("submissions_count", submission_count + 1)
            
            return submission_id
        except Exception as e:
            print(f"Error saving to Redis: {str(e)}. Falling back to memory storage.")
            submissions_memory.append(submission)
            return len(submissions_memory) - 1
    else:
        # Fallback to memory storage
        submissions_memory.append(submission)
        return len(submissions_memory) - 1

# Function to get a submission by ID
def get_submission(submission_id):
    if redis_client:
        try:
            submission_data = redis_client.hget("submission", submission_id)
            if submission_data:
                return json.loads(submission_data)
            return None
        except Exception as e:
            print(f"Error getting submission from Redis: {str(e)}. Falling back to memory storage.")
            if 0 <= submission_id < len(submissions_memory):
                return submissions_memory[submission_id]
            return None
    else:
        # Fallback to memory storage
        if 0 <= submission_id < len(submissions_memory):
            return submissions_memory[submission_id]
        return None

# Function to get all submissions
def get_all_submissions():
    if redis_client:
        try:
            all_submissions = []
            submission_ids = redis_client.hkeys("submission")
            for sid in submission_ids:
                submission_data = redis_client.hget("submission", sid)
                if submission_data:
                    submission = json.loads(submission_data)
                    # Add ID to the submission data
                    submission['id'] = sid.decode('utf-8') if isinstance(sid, bytes) else sid
                    all_submissions.append(submission)
            return all_submissions
        except Exception as e:
            print(f"Error getting all submissions from Redis: {str(e)}. Falling back to memory storage.")
            return submissions_memory
    else:
        # Fallback to memory storage
        return submissions_memory

# Function to get submissions by gallery type
def get_submissions_by_gallery_type(gallery_type):
    all_submissions = get_all_submissions()
    return [s for s in all_submissions if s.get('galleryType') == gallery_type]

# Function to extract ZIP and return modified HTML
def extract_zip_and_process_html(zip_data, submission_id=None):
    """
    Extracts a ZIP file, processes the HTML content, and optionally stores file references
    for later retrieval.
    
    Args:
        zip_data (bytes): The ZIP file content as bytes
        submission_id (str, optional): An ID to associate with the extracted files for later retrieval
    
    Returns:
        tuple: (processed_html_content, temp_dir_path, files_dict)
            - processed_html_content: The HTML content with paths modified to point to assets
            - temp_dir_path: Path to the temporary directory where files were extracted
            - files_dict: Dictionary mapping relative paths to absolute file paths
    """
    try:
        # Create a temporary directory to extract files
        temp_dir = tempfile.mkdtemp(prefix="gallery_preview_")
        
        # Create a zip file object from the zip data
        zip_buffer = io.BytesIO(zip_data)
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            # Extract all files to the temporary directory
            zip_ref.extractall(temp_dir)
            
            # Create a dictionary to store file paths
            files_dict = {}
            
            # Find index.html file
            index_html_path = None
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    # Get the absolute path of the file
                    abs_path = os.path.join(root, file)
                    
                    # Calculate relative path for dictionary key
                    rel_path = os.path.relpath(abs_path, temp_dir)
                    files_dict[rel_path] = abs_path
                    files_dict[rel_path.replace(os.path.sep, '/')] = abs_path
                    
                    # Also store just the filename for easier lookup
                    files_dict[file] = abs_path
                    
                    # Find index.html file
                    if file.lower() == 'index.html':
                        index_html_path = abs_path
            
            # If index.html not found, look for any HTML file
            if not index_html_path:
                html_files = [path for path in files_dict.values() if path.lower().endswith('.html')]
                if html_files:
                    index_html_path = html_files[0]
                else:
                    raise ValueError("No HTML files found in the ZIP archive")
            
            # Read the HTML content
            with open(index_html_path, 'r', encoding='utf-8', errors='replace') as f:
                html_content = f.read()
            
            # Process the HTML to correct asset paths
            if submission_id:
                # If we have a submission ID, use it to create a base path for assets
                base_path = f"/api/gallery/asset/{submission_id}/"
                
                # Rewrite links to CSS files
                html_content = re.sub(
                    r'<link\s+[^>]*href=[\'"](.*?)[\'"]',
                    lambda m: f'<link href="{base_path + m.group(1)}"' if not m.group(1).startswith(('http://', 'https://', '/')) else m.group(0),
                    html_content
                )
                
                # Rewrite links to JavaScript files
                html_content = re.sub(
                    r'<script\s+[^>]*src=[\'"](.*?)[\'"]',
                    lambda m: f'<script src="{base_path + m.group(1)}"' if not m.group(1).startswith(('http://', 'https://', '/')) else m.group(0),
                    html_content
                )
                
                # Rewrite image sources
                html_content = re.sub(
                    r'<img\s+[^>]*src=[\'"](.*?)[\'"]',
                    lambda m: f'<img src="{base_path + m.group(1)}"' if not m.group(1).startswith(('http://', 'https://', '/')) else m.group(0),
                    html_content
                )
                
                # Add base tag to head if not present
                if "<base" not in html_content and "<head" in html_content:
                    head_end = html_content.find("</head>")
                    if head_end > 0:
                        html_content = html_content[:head_end] + f'<base href="{base_path}">' + html_content[head_end:]
                
                # Store the extracted files for later retrieval
                if submission_id:
                    extracted_zips[submission_id] = (temp_dir, files_dict)
                    
                    # Store a cleanup flag in Redis to delete this temp data when no longer needed
                    # The timeout is set to 30 minutes (1800 seconds)
                    if redis_client:
                        try:
                            redis_client.setex(f"gallery_preview_{submission_id}", 1800, "1")
                        except Exception as e:
                            print(f"Error setting Redis cleanup key: {str(e)}")
            else:
                # For direct preview without submission_id, use relative paths
                # We still need to fix paths that might be broken during extraction
                
                # Create a data URI for inline resources (small files)
                for file_rel_path, file_abs_path in files_dict.items():
                    if os.path.getsize(file_abs_path) < 1024 * 1024:  # Less than 1MB
                        # Only process CSS and JS files for inline inclusion
                        if file_rel_path.endswith('.css'):
                            with open(file_abs_path, 'r', encoding='utf-8', errors='replace') as f:
                                css_content = f.read()
                            # Find CSS references in HTML and replace with inline content
                            pattern = f'<link[^>]*href=[\'"]({re.escape(file_rel_path)})[\'"][^>]*>'
                            replacement = f'<style>{css_content}</style>'
                            html_content = re.sub(pattern, replacement, html_content)
                        
                        elif file_rel_path.endswith('.js'):
                            with open(file_abs_path, 'r', encoding='utf-8', errors='replace') as f:
                                js_content = f.read()
                            # Find JS references in HTML and replace with inline content
                            pattern = f'<script[^>]*src=[\'"]({re.escape(file_rel_path)})[\'"][^>]*></script>'
                            replacement = f'<script>{js_content}</script>'
                            html_content = re.sub(pattern, replacement, html_content)
                
                # For images, we convert small images to data URIs
                for rel_path, abs_path in files_dict.items():
                    if os.path.getsize(abs_path) < 100 * 1024:  # Less than 100KB
                        if any(rel_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.svg']):
                            with open(abs_path, 'rb') as f:
                                img_data = f.read()
                            
                            # Get the MIME type
                            mime_type, _ = mimetypes.guess_type(rel_path)
                            if not mime_type:
                                mime_type = "image/png"  # Default
                            
                            # Create data URI
                            data_uri = f"data:{mime_type};base64,{base64.b64encode(img_data).decode('utf-8')}"
                            
                            # Replace in HTML
                            html_content = re.sub(
                                f'src=[\'"]({re.escape(rel_path)})[\'"]',
                                f'src="{data_uri}"',
                                html_content
                            )
                
                # Store in Redis for temporary access (if using Redis)
                if redis_client and not submission_id:
                    # Generate a temporary ID for this preview
                    temp_id = f"temp_preview_{int(time.time())}_{os.urandom(4).hex()}"
                    
                    # Store the HTML content in Redis with 30-minute expiration
                    try:
                        redis_client.setex(f"preview_html_{temp_id}", 1800, html_content)
                        
                        # Store the temp directory for cleanup
                        redis_client.setex(f"preview_tempdir_{temp_id}", 1800, temp_dir)
                    except Exception as e:
                        print(f"Error storing preview in Redis: {str(e)}")
            
            return html_content, temp_dir, files_dict
    
    except Exception as e:
        print(f"Error extracting ZIP: {str(e)}")
        # Clean up temp directory if it exists
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Error cleaning up temp directory: {str(cleanup_error)}")
        
        # Re-raise the exception
        raise

# Function to cleanup temporary files
def cleanup_temporary_files():
    """
    Cleans up temporary directories for expired previews.
    This should be called periodically to free up disk space.
    """
    if not redis_client:
        print("Redis not available, skipping temporary file cleanup")
        return 0
    
    cleanup_count = 0
    try:
        # Get all keys for temporary previews that are about to expire
        temp_keys = redis_client.keys("preview_tempdir_*")
        
        for key in temp_keys:
            # Check if the key is still valid (not expired)
            if not redis_client.exists(key):
                continue
                
            # Get the temp directory path
            temp_dir = redis_client.get(key).decode('utf-8')
            
            # Check if the directory exists
            if os.path.exists(temp_dir):
                try:
                    # Remove the temporary directory
                    shutil.rmtree(temp_dir)
                    print(f"Cleaned up temporary directory: {temp_dir}")
                    cleanup_count += 1
                except Exception as e:
                    print(f"Error cleaning up directory {temp_dir}: {str(e)}")
            
            # Remove the key from Redis
            redis_client.delete(key)
            
        # Also clean up any extracted_zips that might be in memory but no longer needed
        keys_to_delete = []
        for submission_id, (temp_dir, _) in extracted_zips.items():
            # Check if the associated Redis key exists
            if not redis_client.exists(f"gallery_preview_{submission_id}"):
                try:
                    # Remove the temporary directory
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                        print(f"Cleaned up extracted ZIP directory: {temp_dir}")
                    keys_to_delete.append(submission_id)
                    cleanup_count += 1
                except Exception as e:
                    print(f"Error cleaning up ZIP directory {temp_dir}: {str(e)}")
        
        # Remove the cleaned up entries from the in-memory dictionary
        for key in keys_to_delete:
            extracted_zips.pop(key, None)
            
        return cleanup_count
            
    except Exception as e:
        print(f"Error during temporary file cleanup: {str(e)}")
        return 0

def routes(router):
    @router.post("/api/blob/upload")
    async def upload_to_blob(req: Request):
        try:
            # Get filename from query parameter
            filename = req.query_params.get("filename", f"unknown-{len(get_all_submissions())}.bin")
            
            # Read the file content from the request body
            file_data = await req.body()
            
            # Upload to Vercel Blob (not awaited as vercel_blob.put is synchronous)
            print(f"Uploading {filename} to blob storage...")
            blob_result = blob_put(
                filename, 
                file_data, 
                {"access": "public", "addRandomSuffix": True}
            )
            print(f"Upload complete: {blob_result.get('url', 'No URL returned')}")
            
            # Return the blob information
            return JSONResponse(blob_result)
        
        except Exception as e:
            print(f"Error uploading to blob: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @router.post("/api/gallery/save-metadata")
    async def save_gallery_metadata(req: Request):
        try:
            # Parse JSON from request body
            metadata = json.loads(await req.body())
            
            # Save to Redis or in-memory fallback
            submission_id = save_submission(metadata)
            
            # Log the submission for debugging
            print(f"New gallery submission: {metadata['title']} ({metadata['level']} - {metadata['subject']})")
            print(f"ZIP URL: {metadata['zipUrl']}")
            print(f"Reference Images: {len(metadata['referenceImages'])}")
            if metadata.get('description'):
                print(f"Description: {metadata['description'][:100]}{'...' if len(metadata['description']) > 100 else ''}")
            
            # Run cleanup of temporary files
            cleanup_count = cleanup_temporary_files()
            if cleanup_count > 0:
                print(f"Cleaned up {cleanup_count} temporary files after submission")
            
            # Return success response
            return JSONResponse({
                "success": True,
                "message": "Metadata saved successfully",
                "submissionId": submission_id
            })
        
        except Exception as e:
            print(f"Error saving metadata: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @router.get("/api/gallery/submissions/{gallery_type}")
    async def get_gallery_submissions(req: Request):
        try:
            # Run cleanup to remove invalid submissions every time gallery is accessed
            start_time = time.time()
            cleaned, total = cleanup_invalid_submissions()
            cleanup_time = time.time() - start_time
            print(f"Cleanup took {cleanup_time:.2f} seconds. Removed {cleaned}/{total} invalid submissions.")
            
            # Get submissions for the requested gallery type
            gallery_type = req.path_params.get("gallery_type")
            filtered_submissions = get_submissions_by_gallery_type(gallery_type)
            
            return JSONResponse({
                "submissions": filtered_submissions,
                "data_integrity": {
                    "total_checked": total,
                    "cleaned_count": cleaned,
                    "cleanup_time_seconds": round(cleanup_time, 2)
                }
            })
        except Exception as e:
            print(f"Error getting submissions: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @router.get("/api/gallery/preview/{submission_id}")
    async def preview_interactive(req: Request):
        try:
            submission_id = req.path_params.get("submission_id")
            
            # If the ID is a numeric string, convert to int as that's how older submissions are stored
            if submission_id.isdigit():
                submission_id = int(submission_id)
            
            # Get submission from Redis or memory
            submission = get_submission(submission_id)
            
            # Ensure submission exists
            if not submission:
                return JSONResponse(
                    {"error": "Submission not found"},
                    status_code=404
                )
            
            # Validate the submission's URLs
            if not validate_submission(submission):
                # If using Redis, remove the invalid submission
                if redis_client:
                    try:
                        redis_client.hdel("submission", submission_id)
                        print(f"Removed invalid submission with ID {submission_id} during preview")
                    except Exception as e:
                        print(f"Error removing invalid submission: {str(e)}")
                
                return JSONResponse(
                    {"error": "Submission resources are no longer available"},
                    status_code=404
                )
            
            zip_url = submission.get('zipUrl')
            
            # Check if the zip has already been processed and cached in Redis
            cache_key = f"gallery_preview_html_{submission_id}"
            if redis_client:
                try:
                    cached_html = redis_client.get(cache_key)
                    if cached_html:
                        print(f"Using cached HTML for submission {submission_id}")
                        # Create response with security headers
                        response = HTMLResponse(cached_html)
                        # Add security headers to allow proper iframe communication
                        response.headers["Content-Security-Policy"] = "frame-ancestors 'self'; default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:;"
                        response.headers["X-Frame-Options"] = "SAMEORIGIN"
                        return response
                except Exception as e:
                    print(f"Error retrieving from Redis cache: {str(e)}")
            
            # Download the ZIP file if not already extracted
            print(f"Downloading ZIP from {zip_url}")
            response = urllib.request.urlopen(zip_url)
            zip_data = response.read()
                
            # Extract the ZIP and process HTML - use the same processing as preview_content_from_zip
            html_content, temp_dir, files_dict = extract_zip_and_process_html(zip_data)
            
            # Store HTML in Redis cache for future requests (with 30 minute TTL)
            if redis_client:
                try:
                    redis_client.setex(cache_key, 1800, html_content)
                    
                    # Also store temp directory path for cleanup
                    redis_client.setex(f"gallery_preview_tempdir_{submission_id}", 1800, temp_dir)
                    
                    print(f"Cached HTML for submission {submission_id} in Redis (30 min TTL)")
                except Exception as e:
                    print(f"Error caching in Redis: {str(e)}")
            
            # Return the processed HTML content with security headers
            response = HTMLResponse(html_content)
            # Add security headers to allow proper iframe communication
            response.headers["Content-Security-Policy"] = "frame-ancestors 'self'; default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:;"
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            return response
            
        except Exception as e:
            print(f"Error previewing interactive: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @router.get("/api/gallery/asset/{submission_id}/{asset_path:path}")
    async def get_asset(req: Request):
        try:
            submission_id = req.path_params.get("submission_id")
            
            # If the ID is a numeric string, convert to int as that's how older submissions are stored
            if submission_id.isdigit():
                submission_id = int(submission_id)
                
            asset_path = req.path_params.get("asset_path")
            
            print(f"Asset request: {asset_path} for submission {submission_id}")
            
            # Check if the ZIP has been extracted
            if submission_id not in extracted_zips:
                return JSONResponse(
                    {"error": "Submission not found or not extracted"},
                    status_code=404
                )
            
            temp_dir, files_dict = extracted_zips[submission_id]
            
            # Debug: Print all keys in files_dict for troubleshooting
            print(f"All files in dictionary: {list(files_dict.keys())}")
            
            # Try all possible path variations to find the file
            possible_paths = [
                asset_path,
                asset_path.replace('/', os.path.sep),
                asset_path.replace(os.path.sep, '/'),
                os.path.basename(asset_path)
            ]
            
            # Debug each path attempt
            for path in possible_paths:
                print(f"Trying path: {path}")
                
                # Try direct match
                if path in files_dict:
                    asset_file_path = files_dict[path]
                    print(f"Direct match found: {path} -> {asset_file_path}")
                    
                    # Determine content type
                    content_type, _ = mimetypes.guess_type(asset_file_path)
                    if not content_type:
                        content_type = "application/octet-stream"
                    
                    print(f"Serving asset: {asset_file_path} as {content_type}")
                    return FileResponse(
                        asset_file_path,
                        media_type=content_type
                    )
                
                # Try case-insensitive match
                lower_path = path.lower()
                for dict_path, file_path in files_dict.items():
                    if dict_path.lower() == lower_path:
                        print(f"Case-insensitive match found: {dict_path} -> {file_path}")
                        content_type, _ = mimetypes.guess_type(file_path)
                        if not content_type:
                            content_type = "application/octet-stream"
                        return FileResponse(
                            file_path,
                            media_type=content_type
                        )
            
            # If the above fails, try a more direct approach - look in the temp directory
            file_path_in_temp = os.path.join(temp_dir, asset_path.replace('/', os.path.sep))
            if os.path.isfile(file_path_in_temp):
                print(f"Found file directly in temp dir: {file_path_in_temp}")
                content_type, _ = mimetypes.guess_type(file_path_in_temp)
                if not content_type:
                    content_type = "application/octet-stream"
                return FileResponse(
                    file_path_in_temp,
                    media_type=content_type
                )
            
            # Try to find just by basename in temp_dir (recursive search)
            filename = os.path.basename(asset_path)
            for root, _, files in os.walk(temp_dir):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    print(f"Found file by basename search: {file_path}")
                    content_type, _ = mimetypes.guess_type(file_path)
                    if not content_type:
                        content_type = "application/octet-stream"
                    return FileResponse(
                        file_path,
                        media_type=content_type
                    )
            
            # Asset not found
            print(f"Asset not found: {asset_path}")
            print(f"Temp directory: {temp_dir}")
            return JSONResponse(
                {"error": f"Asset {asset_path} not found"},
                status_code=404
            )
            
        except Exception as e:
            print(f"Error serving asset: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @router.post("/api/html5/preview-content-from-zip")
    async def preview_content_from_zip(req: Request):
        try:
            # Get form data with the zip file
            form = await req.form()
            zip_file = form.get("zipfile")
            
            if not zip_file:
                return JSONResponse(
                    {"error": "No ZIP file provided"},
                    status_code=400
                )
            
            # Read the zip file content
            zip_data = await zip_file.read()
            
            # Extract the ZIP and process HTML
            html_content, _, _ = extract_zip_and_process_html(zip_data)
            
            # Return the processed HTML content with security headers
            response = HTMLResponse(html_content)
            # Add security headers to allow proper iframe communication
            response.headers["Content-Security-Policy"] = "frame-ancestors 'self'; default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:;"
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            return response
            
        except Exception as e:
            print(f"Error previewing ZIP content: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @router.get("/api/gallery/validate-data")
    async def validate_gallery_data(req: Request):
        """
        Endpoint to manually run validation and cleanup of Redis records.
        """
        try:
            start_time = time.time()
            cleaned, total = cleanup_invalid_submissions()
            elapsed_time = time.time() - start_time
            
            return JSONResponse({
                "success": True,
                "message": f"Validation completed in {elapsed_time:.2f} seconds",
                "data": {
                    "total_records": total,
                    "invalid_records_removed": cleaned,
                    "time_seconds": round(elapsed_time, 2)
                }
            })
            
        except Exception as e:
            print(f"Error validating data: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @router.get("/api/maintenance/cleanup-temp-files")
    async def cleanup_temp_files(req: Request):
        """
        Endpoint to manually trigger cleanup of temporary files
        """
        try:
            start_time = time.time()
            cleanup_count = cleanup_temporary_files()
            elapsed_time = time.time() - start_time
            
            return JSONResponse({
                "success": True,
                "message": f"Cleaned up {cleanup_count} temporary files in {elapsed_time:.2f} seconds"
            })
            
        except Exception as e:
            print(f"Error in cleanup endpoint: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @router.get("/api/maintenance/clear-preview-cache")
    async def clear_preview_cache(req: Request):
        """
        Endpoint to clear all preview HTML caches
        """
        try:
            if not redis_client:
                return JSONResponse({
                    "error": "Redis not available"
                }, status_code=500)
                
            # Get all preview cache keys
            preview_keys = redis_client.keys("gallery_preview_html_*")
            
            if not preview_keys:
                return JSONResponse({
                    "success": True,
                    "message": "No preview caches found"
                })
            
            # Delete all preview cache keys
            deleted_count = 0
            for key in preview_keys:
                redis_client.delete(key)
                deleted_count += 1
            
            return JSONResponse({
                "success": True,
                "message": f"Cleared {deleted_count} preview caches"
            })
            
        except Exception as e:
            print(f"Error clearing preview caches: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @router.get("/api/gallery/list-interactives")
    async def list_interactives(req: Request):
        try:
            # Check authentication
            auth = req.session.get('auth')
            if auth not in ["joe", "super_admin"]:
                return JSONResponse(
                    {"error": "Unauthorized"},
                    status_code=401
                )
                
            # Get all submissions
            all_submissions = get_all_submissions()
            
            # Return HTML table
            html = """
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Author</th>
                        <th>Level</th>
                        <th>Subject</th>
                        <th>Gallery Type</th>
                        <th>Date Submitted</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for submission in all_submissions:
                submission_id = submission.get('id')
                if not submission_id:
                    continue
                    
                title = submission.get('title', 'Untitled')
                author = submission.get('author', 'Unknown')
                level = submission.get('level', 'Unknown')
                subject = submission.get('subject', 'Unknown')
                gallery_type = submission.get('galleryType', 'Unknown')
                date_submitted = submission.get('dateSubmitted', 'Unknown')
                
                # Format date for display
                if date_submitted != 'Unknown':
                    try:
                        # Convert ISO date to more readable format
                        dt = datetime.fromisoformat(date_submitted.replace('Z', '+00:00'))
                        date_submitted = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                html += f"""
                <tr>
                    <td>{submission_id}</td>
                    <td>{title}</td>
                    <td>{author}</td>
                    <td>{level}</td>
                    <td>{subject}</td>
                    <td>{gallery_type}</td>
                    <td>{date_submitted}</td>
                    <td>
                        <button 
                            class="btn-replace"
                            onclick="showReplaceForm('{submission_id}', '{title.replace("'", "\\'")}')">
                            Replace ZIP
                        </button>
                    </td>
                </tr>
                """
            
            html += """
                </tbody>
            </table>
            """
            
            return HTMLResponse(html)
            
        except Exception as e:
            print(f"Error listing interactives: {str(e)}")
            return HTMLResponse(
                f"<p class='error'>Error loading interactives: {str(e)}</p>",
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @router.post("/api/gallery/update-zip")
    async def update_zip(req: Request):
        try:
            # Check authentication
            auth = req.session.get('auth')
            if auth not in ["joe", "super_admin"]:
                return JSONResponse(
                    {"error": "Unauthorized"},
                    status_code=401
                )
                
            # Parse request body
            data = await req.json()
            submission_id = data.get('id')
            new_zip_url = data.get('zipUrl')
            
            if not submission_id or not new_zip_url:
                return JSONResponse(
                    {"error": "Missing required fields"},
                    status_code=400
                )
            
            # Get the submission
            submission = get_submission(submission_id)
            if not submission:
                return JSONResponse(
                    {"error": f"Submission with ID {submission_id} not found"},
                    status_code=404
                )
            
            # Store the old ZIP URL for reference
            old_zip_url = submission.get('zipUrl')
            
            # Update the ZIP URL
            submission['zipUrl'] = new_zip_url
            
            # Record the replacement in submission history if not already present
            if 'replacementHistory' not in submission:
                submission['replacementHistory'] = []
                
            submission['replacementHistory'].append({
                'oldZipUrl': old_zip_url,
                'newZipUrl': new_zip_url,
                'replacedBy': auth,
                'replacedAt': datetime.now().isoformat()
            })
            
            # Update the submission in storage
            if redis_client:
                try:
                    redis_client.hset("submission", submission_id, json.dumps(submission))
                except Exception as e:
                    print(f"Error updating submission in Redis: {str(e)}")
                    return JSONResponse(
                        {"error": f"Error updating submission: {str(e)}"},
                        status_code=HTTP_500_INTERNAL_SERVER_ERROR
                    )
            else:
                # Update in memory storage
                try:
                    # Find the submission in the list by ID
                    for i, s in enumerate(submissions_memory):
                        if str(s.get('id')) == str(submission_id):
                            submissions_memory[i] = submission
                            break
                except Exception as e:
                    print(f"Error updating submission in memory: {str(e)}")
                    return JSONResponse(
                        {"error": f"Error updating submission: {str(e)}"},
                        status_code=HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            # Clear the HTML cache for this submission if it exists
            if redis_client:
                try:
                    cache_key = f"gallery_preview_html_{submission_id}"
                    if redis_client.exists(cache_key):
                        redis_client.delete(cache_key)
                        print(f"Cleared HTML cache for submission {submission_id}")
                        
                    # Also clear extracted ZIP if present
                    if submission_id in extracted_zips:
                        temp_dir, _ = extracted_zips.pop(submission_id)
                        if os.path.exists(temp_dir):
                            try:
                                shutil.rmtree(temp_dir)
                                print(f"Removed extracted ZIP for submission {submission_id}")
                            except Exception as cleanup_error:
                                print(f"Error removing extracted ZIP: {str(cleanup_error)}")
                except Exception as e:
                    print(f"Error clearing cache: {str(e)}")
            
            return JSONResponse({
                "success": True,
                "message": "ZIP file updated successfully",
                "replacedZipUrl": old_zip_url,
                "newZipUrl": new_zip_url
            })
            
        except Exception as e:
            print(f"Error updating ZIP: {str(e)}")
            return JSONResponse(
                {"error": str(e)},
                status_code=HTTP_500_INTERNAL_SERVER_ERROR
            ) 