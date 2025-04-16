from fasthtml.common import *
import token_count
import datetime
from components.token_form import (
    create_token_usage_display,
    create_token_summary,
    create_token_history_table,
    create_user_token_stats
)
from starlette.responses import RedirectResponse

def routes(rt):
    @rt('/tokens')
    def get(req):
        """Display the token usage statistics page"""
        # Initialize the database if it doesn't exist
        token_count.init_db()
        
        # Check if user is authorized (must be super_admin or joe)
        auth = req.session.get('auth', None)
        if auth not in ['super_admin', 'joe']:
            return Div(
                H2("Access Denied"),
                P("You do not have permission to view token usage statistics."),
                cls="error"
            )
        
        return Titled("Token Usage Statistics",
            Link(rel="stylesheet", href="/static/css/styles.css"),
            create_token_usage_display()
        )
    
    @rt('/api/tokens/summary')
    def get(req):
        """API endpoint to get token usage summary"""
        # Check if user is authorized (must be super_admin or joe)
        auth = req.session.get('auth', None)
        if auth not in ['super_admin', 'joe']:
            return Div("Access denied", cls="error")
        
        # Get summary statistics (for all users since admin/joe has full access)
        summary = token_count.get_token_usage_summary()
        
        return create_token_summary(summary)
    
    @rt('/api/tokens/user-stats')
    def get(req):
        """API endpoint to get token usage statistics by user"""
        # Check if user is authorized (must be super_admin or joe)
        auth = req.session.get('auth', None)
        if auth not in ['super_admin', 'joe']:
            return Div("Access denied", cls="error")
        
        # Get usage stats by user
        user_stats = token_count.get_token_usage_by_user()
        
        return create_user_token_stats(user_stats)
    
    @rt('/api/tokens/history')
    def get(req):
        """API endpoint to get token usage history"""
        # Check if user is authorized (must be super_admin or joe)
        auth = req.session.get('auth', None)
        if auth not in ['super_admin', 'joe']:
            return Div("Access denied", cls="error")
        
        # Get usage history for all users (admin access)
        history = token_count.get_token_usage(limit=50)
        
        return create_token_history_table(history)
    
    @rt('/api/tokens/refresh')
    def get(req):
        """Refresh the entire token usage page"""
        # Check if user is authorized (must be super_admin or joe)
        auth = req.session.get('auth', None)
        if auth not in ['super_admin', 'joe']:
            return Div("Access denied", cls="error")
        
        return create_token_usage_display()
    
    @rt('/api/tokens/db-check')
    def get(req):
        """Check database connectivity"""
        # Check if user is authorized
        auth = req.session.get('auth', None)
        if auth not in ['super_admin', 'joe']:
            return Div("Access denied", cls="error")
        
        # Check if we have a connection pool
        if not hasattr(token_count, 'connection_pool') or token_count.connection_pool is None:
            return Div("Database connection pool not initialized", cls="error")
        
        try:
            # Get a connection
            conn = token_count.connection_pool.getconn()
            cursor = conn.cursor()
            
            # Check if we can execute a simple query
            cursor.execute("SELECT current_timestamp")
            timestamp = cursor.fetchone()[0]
            
            # Return the connection to the pool
            cursor.close()
            token_count.connection_pool.putconn(conn)
            
            # Return success
            return Div(
                H3("Database Connection Successful", cls="text-green-600"),
                P(f"Server time: {timestamp}"),
                cls="bg-green-100 p-4 rounded"
            )
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            return Div(
                H3("Database Connection Failed", cls="text-red-600"),
                P(f"Error: {str(e)}"),
                Pre(error_trace, cls="bg-gray-100 p-2 text-xs overflow-auto"),
                cls="bg-red-100 p-4 rounded"
            )
    
    @rt('/api/tokens/view-prompt/{id}')
    def get(req, id):
        """View complete prompt for a token usage record"""
        # Check if user is authorized
        auth = req.session.get('auth', None)
        if auth not in ['super_admin', 'joe']:
            return Div("Access denied", cls="error")
        
        try:
            # Get token record by ID
            record = token_count.get_token_record(id)
            
            if not record:
                return Div("Record not found", cls="bg-red-100 p-4 rounded text-red-800")
            
            # Format timestamps for display
            timestamp = None
            if record.get('timestamp'):
                try:
                    from datetime import datetime
                    if isinstance(record['timestamp'], str):
                        timestamp = datetime.fromisoformat(record['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        timestamp = record['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                except:
                    timestamp = str(record['timestamp'])
            
            return Div(
                H3("Prompt Details", cls="text-lg font-semibold mb-3"),
                Div(
                    Div(
                        H4("Metadata", cls="text-md font-semibold mb-2"),
                        Div(
                            Div(
                                Div("ID", cls="font-bold"),
                                Div(f"{record.get('id', 'N/A')}", cls="text-sm"),
                                cls="mb-2"
                            ),
                            Div(
                                Div("Time", cls="font-bold"),
                                Div(timestamp or 'N/A', cls="text-sm"),
                                cls="mb-2"
                            ),
                            Div(
                                Div("Username", cls="font-bold"),
                                Div(record.get('user_id', 'N/A'), cls="text-sm"),
                                cls="mb-2"
                            ),
                            Div(
                                Div("Model", cls="font-bold"),
                                Div(record.get('model', 'N/A'), cls="text-sm"),
                                cls="mb-2"
                            ),
                            Div(
                                Div("Generation Time", cls="font-bold"),
                                Div(f"{record.get('generation_time_ms', 0)/1000:.2f} seconds", cls="text-sm"),
                                cls="mb-2"
                            ),
                            cls="grid grid-cols-2 gap-x-4 gap-y-1 mb-4"
                        ),
                        cls="bg-blue-50 p-4 rounded-lg mb-4"
                    ),
                    Div(
                        H4("Prompt", cls="text-md font-semibold mb-2"),
                        Pre(
                            record.get('prompt', 'N/A'),
                            cls="bg-gray-100 p-4 rounded text-sm overflow-auto whitespace-pre-wrap max-h-96"
                        ),
                        cls="mb-4"
                    ),
                    Div(
                        H4("Token Usage", cls="text-md font-semibold mb-2"),
                        Table(
                            Thead(
                                Tr(
                                    Th("Prompt Tokens", cls="px-4 py-2"),
                                    Th("Completion Tokens", cls="px-4 py-2"),
                                    Th("Total Tokens", cls="px-4 py-2")
                                ),
                                cls="bg-gray-200"
                            ),
                            Tbody(
                                Tr(
                                    Td(f"{record.get('prompt_tokens', 0):,}", cls="px-4 py-2 text-center"),
                                    Td(f"{record.get('completion_tokens', 0):,}", cls="px-4 py-2 text-center"),
                                    Td(f"{record.get('total_tokens', 0):,}", cls="px-4 py-2 text-center font-bold")
                                )
                            ),
                            cls="min-w-full"
                        ),
                        cls="mb-4"
                    ),
                    Div(
                        Button(
                            "Close",
                            cls="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded",
                            onclick="document.getElementById('prompt-detail-modal').classList.add('hidden')"
                        ),
                        cls="text-right"
                    ),
                    cls="bg-white p-6 rounded-lg shadow-lg border border-gray-200"
                ),
                cls="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center",
                onclick="if(event.target === this) this.classList.add('hidden')"
            )
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            return Div(
                H3("Error Loading Prompt", cls="text-red-600"),
                P(f"Error: {str(e)}"),
                Pre(error_trace, cls="bg-gray-100 p-2 text-xs overflow-auto"),
                cls="bg-red-100 p-4 rounded"
            )
    
    @rt('/api/tokens/reset-database')
    def get(req):
        """Reset the token usage database (admin only)"""
        # Check if user is authorized (must be super_admin or joe)
        auth = req.session.get('auth', None)
        if auth not in ['super_admin', 'joe']:
            return Div("Access denied", cls="error")
        
        # Reset the database
        success = token_count.reset_token_database()
        
        if success:
            return Div(
                H3("Database Reset Successful", cls="text-green-600"),
                P("The token usage database has been reset. All previous records have been deleted."),
                A("Refresh Token Usage Page", 
                  hx_get="/api/tokens/refresh",
                  hx_target="#token-page-container",
                  hx_indicator="#loading-indicator",
                  cls="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded inline-block mt-4"),
                cls="bg-green-100 p-4 rounded"
            )
        else:
            return Div(
                H3("Database Reset Failed", cls="text-red-600"),
                P("Failed to reset the token usage database. Please check the server logs for details."),
                cls="bg-red-100 p-4 rounded"
            )
    
    @rt('/api/tokens/download-csv')
    def get(req):
        """Download token usage data as CSV"""
        # Check if user is authorized (must be super_admin or joe)
        auth = req.session.get('auth', None)
        if auth not in ['super_admin', 'joe']:
            return Div("Access denied", cls="error")
        
        try:
            # Get all token usage data
            history = token_count.get_token_usage(limit=1000)  # Increased limit for CSV export
            
            if not history:
                return Div("No data to export", cls="bg-yellow-100 p-4 rounded text-yellow-800")
            
            # Create CSV content
            import csv
            import io
            
            # Create a string IO buffer for CSV data
            output = io.StringIO()
            csv_writer = csv.writer(output)
            
            # Write header row
            csv_writer.writerow([
                'Timestamp', 'Username', 'Model', 
                'Prompt Tokens', 'Completion Tokens', 'Total Tokens',
                'Generation Time (ms)', 'Prompt'
            ])
            
            # Write data rows
            for item in history:
                # Format timestamp if it's a datetime object
                timestamp = item.get('timestamp', '')
                if hasattr(timestamp, 'isoformat'):
                    timestamp = timestamp.isoformat()
                
                csv_writer.writerow([
                    timestamp,
                    item.get('user_id', 'Anonymous'),
                    item.get('model', 'Unknown'),
                    item.get('prompt_tokens', 0),
                    item.get('completion_tokens', 0),
                    item.get('total_tokens', 0),
                    item.get('generation_time_ms', 0),
                    item.get('prompt', '')  # Include full prompt text
                ])
            
            # Get CSV content as string
            csv_content = output.getvalue()
            
            # Create a response with CSV content
            from starlette.responses import Response
            filename = f"token_usage_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={filename}"
                }
            )
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            return Div(
                H3("CSV Export Failed", cls="text-red-600"),
                P(f"Error: {str(e)}"),
                Pre(error_trace, cls="bg-gray-100 p-2 text-xs overflow-auto"),
                cls="bg-red-100 p-4 rounded"
            ) 