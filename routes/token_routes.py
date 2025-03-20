from fasthtml.common import *
import token_count
from components.token_form import (
    create_token_usage_display,
    create_token_summary,
    create_token_history_table
)

def routes(rt):
    @rt('/tokens')
    def get(req):
        """Display the token usage statistics page"""
        # Initialize the database if it doesn't exist
        token_count.init_db()
        
        return Titled("Token Usage Statistics",
            Link(rel="stylesheet", href="/static/css/styles.css"),
            create_token_usage_display()
        )
    
    @rt('/api/tokens/summary')
    def get(req):
        """API endpoint to get token usage summary"""
        # Get user ID from session if available
        user_id = req.session.get('auth', None)
        
        # Get summary statistics
        summary = token_count.get_token_usage_summary(user_id)
        
        return create_token_summary(summary)
    
    @rt('/api/tokens/history')
    def get(req):
        """API endpoint to get token usage history"""
        # Get user ID from session if available
        user_id = req.session.get('auth', None)
        
        # Get usage history
        history = token_count.get_token_usage(limit=50, user_id=user_id)
        
        return create_token_history_table(history)
    
    @rt('/api/tokens/refresh')
    def get(req):
        """Refresh the entire token usage page"""
        return create_token_usage_display() 