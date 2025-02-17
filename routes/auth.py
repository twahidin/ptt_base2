from fasthtml.common import Titled, Container, Div
from components.forms import create_login_form
from ptt_bascode.authentication import check_password
from starlette.responses import RedirectResponse, JSONResponse

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
            del request.session['auth']
        redirect_url = '/login'
        if request.headers.get("HX-Request"):
            return hx_redirect(redirect_url)
        return RedirectResponse(redirect_url, status_code=303)
