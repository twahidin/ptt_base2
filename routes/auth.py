from fasthtml.common import Titled, Container, Div
from components.forms import create_login_form
from ptt_bascode.authentication import check_password
from starlette.responses import RedirectResponse, JSONResponse
import redis
import os

# Redis connection for cache clearing
redis_client = None
try:
    REDIS_URL = os.environ.get('HTML5_REDIS_URL', "redis://localhost:6379/0")
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()  # Test connection
except Exception as e:
    print(f"Auth module: Error connecting to Redis: {str(e)}")
    redis_client = None

def clear_preview_cache():
    """Clear all HTML preview caches from Redis"""
    if not redis_client:
        print("Redis not available, preview cache not cleared during logout")
        return 0
    
    try:
        # Get all preview cache keys
        preview_keys = redis_client.keys("gallery_preview_html_*")
        
        if not preview_keys:
            return 0
        
        # Delete all preview cache keys
        deleted_count = 0
        for key in preview_keys:
            redis_client.delete(key)
            deleted_count += 1
        
        print(f"Logout: Cleared {deleted_count} preview caches")
        return deleted_count
    except Exception as e:
        print(f"Error clearing preview cache during logout: {str(e)}")
        return 0

def hx_redirect(url, status_code=303):
    """
    Return a JSON response with an HX-Redirect header so that HTMX
    clients will perform a full-page redirect.
    """
    response = JSONResponse({"redirect": url})
    response.headers["HX-Redirect"] = url
    response.status_code = status_code
    return response

def routes(rt):
    @rt("/login", methods=["GET"])
    async def login_get(request):
        """Handle GET requests to /login."""
        # Extract error from query parameters, if any.
        error = request.query_params.get("error")
        content = []
        if error:
            # Display the error message in a styled div.
            content.append(Div(f"Error: {error}", cls="error"))
        # Append the login form.
        content.append(create_login_form())
        return Titled("Login", Container(*content))

    @rt("/login", methods=["POST"])
    async def login_post(request):
        """Handle POST requests to /login."""
        try:
            # Retrieve form data.
            form = await request.form()
            username = form.get('username')
            password = form.get('password')
            
            print(f"Login attempt for: {username}")  # Debug print
            
            # Validate input.
            if not username or not password:
                redirect_url = '/login?error=missing_fields'
                if request.headers.get("HX-Request"):
                    return hx_redirect(redirect_url)
                return RedirectResponse(redirect_url, status_code=303)
            
            # Attempt to authenticate.
            try:
                user = check_password(username.lower(), password)
            except Exception as e:
                print(f"Auth error: {e}")  # Debug print
                redirect_url = '/login?error=auth_error'
                if request.headers.get("HX-Request"):
                    return hx_redirect(redirect_url)
                return RedirectResponse(redirect_url, status_code=303)
            
            # If authentication succeeds.
            if user:
                request.session['auth'] = username
                print(f"Login successful for: {username}")  # Debug print
                redirect_url = '/'
                if request.headers.get("HX-Request"):
                    return hx_redirect(redirect_url)
                return RedirectResponse(redirect_url, status_code=303)
            else:
                print("Login failed")  # Debug print
                redirect_url = '/login?error=invalid_credentials'
                if request.headers.get("HX-Request"):
                    return hx_redirect(redirect_url)
                return RedirectResponse(redirect_url, status_code=303)
                
        except Exception as e:
            print(f"Unexpected error: {e}")  # Debug print
            redirect_url = '/login?error=server_error'
            if request.headers.get("HX-Request"):
                return hx_redirect(redirect_url)
            return RedirectResponse(redirect_url, status_code=303)

    @rt("/logout", methods=["GET"])
    async def logout_get(request):
        """Handle GET requests to /logout."""
        if 'auth' in request.session:
            # Clear the user's session
            del request.session['auth']
            
            # Clear the preview cache when logging out
            clear_preview_cache()
            
        redirect_url = '/login'
        if request.headers.get("HX-Request"):
            return hx_redirect(redirect_url)
        return RedirectResponse(redirect_url, status_code=303)
