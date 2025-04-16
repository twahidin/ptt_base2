from fasthtml.common import *
import datetime
from pathlib import Path

def create_token_usage_display():
    """Create the main token usage display form"""
    return Div(
        Div(
            Div(id="token-summary-container", cls="mb-8",
                hx_get="/api/tokens/summary",
                hx_trigger="load",
                hx_indicator="#loading-indicator"
            ),
            # User stats section is hidden per user request
            # Div(id="token-user-stats-container", cls="mb-6",
            #     hx_get="/api/tokens/user-stats",
            #     hx_trigger="load",
            #     hx_indicator="#loading-indicator"
            # ),
            Div(
                Div(id="token-history-container",
                    hx_get="/api/tokens/history",
                    hx_trigger="load",
                    hx_indicator="#loading-indicator"
                ),
                cls="mb-8"
            ),
            Div(
                Button("Refresh Data", 
                    cls="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mr-2",
                    hx_get="/api/tokens/refresh",
                    hx_target="#token-page-container",
                    hx_indicator="#loading-indicator"
                ),
                Button("Check Database Connection", 
                    cls="bg-gray-500 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded mr-2",
                    hx_get="/api/tokens/db-check",
                    hx_target="#db-status",
                    hx_indicator="#loading-indicator"
                ),
                Button("Reset Database", 
                    cls="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded",
                    hx_get="/api/tokens/reset-database",
                    hx_target="#reset-confirmation",
                    hx_confirm="WARNING: This will permanently delete all token usage data. Are you sure you want to proceed?",
                    hx_indicator="#loading-indicator"
                ),
                cls="mt-6"
            ),
            Div(
                A("Download CSV", 
                    href="/api/tokens/download-csv",
                    cls="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded inline-block",
                    download=True
                ),
                cls="mt-4 mb-4"
            ),
            Div(id="db-status", cls="mt-6"),
            Div(id="reset-confirmation", cls="mt-6"),
            Div(
                NotStr("""
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                """),
                " Loading...",
                cls="hidden items-center text-gray-500",
                id="loading-indicator"
            ),
            cls="bg-white p-8 rounded-lg shadow-md"
        ),
        cls="container mx-auto px-4 py-8",
        id="token-page-container"
    )

def create_token_summary(summary):
    """Create a summary view of token usage"""
    # Ensure None values are converted to 0 for formatting
    total_requests = summary.get('total_requests', 0) or 0
    total_prompt_tokens = summary.get('total_prompt_tokens', 0) or 0
    total_completion_tokens = summary.get('total_completion_tokens', 0) or 0
    total_tokens = summary.get('total_tokens', 0) or 0
    models_used = summary.get("models_used", []) or []
    
    # Create HTML manually to avoid rendering issues
    html = f"""
    <h3 class="text-lg font-semibold mb-8">Summary</h3>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <div class="bg-blue-100 p-6 rounded">
            <div class="text-gray-600">Total Requests</div>
            <div class="text-2xl font-bold">{total_requests:,}</div>
        </div>
        <div class="bg-green-100 p-6 rounded">
            <div class="text-gray-600">Prompt Tokens</div>
            <div class="text-2xl font-bold">{total_prompt_tokens:,}</div>
        </div>
        <div class="bg-purple-100 p-6 rounded">
            <div class="text-gray-600">Completion Tokens</div>
            <div class="text-2xl font-bold">{total_completion_tokens:,}</div>
        </div>
        <div class="bg-amber-100 p-6 rounded">
            <div class="text-gray-600">Total Tokens</div>
            <div class="text-2xl font-bold">{total_tokens:,}</div>
        </div>
    </div>
    
    <h4 class="text-md font-semibold mb-4">Models Used</h4>
    <div class="flex flex-wrap mb-6">
    """
    
    # Add models used
    if models_used:
        for model in models_used:
            model_name = model.get("model", "") or "Unknown"
            html += f"""
            <div class="bg-gray-100 p-3 rounded-lg m-2">
                <div class="text-sm">{model_name}</div>
            </div>
            """
    else:
        html += '<div class="text-gray-500 italic">No model data available</div>'
    
    html += """
    </div>
    """
    
    return NotStr(html)

def create_token_history_table(history):
    """Create a table showing token usage history"""
    if not history:
        return Div("No token usage history found", cls="text-gray-500 italic")
    
    # Build HTML manually using NotStr to prevent escaping/string representation
    table_html = """
    <h3 class="text-lg font-semibold mb-6">Token Usage History</h3>
    <div class="overflow-x-auto">
        <table class="w-full border-collapse">
            <thead class="bg-gray-100">
                <tr>
                    <th class="px-4 py-3 text-left">Time</th>
                    <th class="px-4 py-3 text-left">Username</th>
                    <th class="px-4 py-3 text-left">Model</th>
                    <th class="px-4 py-3 text-right">Input</th>
                    <th class="px-4 py-3 text-right">Output</th>
                    <th class="px-4 py-3 text-right">Total</th>
                    <th class="px-4 py-3 text-right">Gen. Time</th>
                    <th class="px-4 py-3 text-left">Prompt</th>
                </tr>
            </thead>
            <tbody>
    """
    
    # Add rows for each history item
    for item in history:
        # Format values safely
        timestamp = format_timestamp(item.get("timestamp", ""))
        username = item.get("user_id", "") or "Anonymous"
        model = item.get("model", "") or "Unknown"
        prompt_tokens = f"{item.get('prompt_tokens', 0) or 0:,}"
        completion_tokens = f"{item.get('completion_tokens', 0) or 0:,}"
        total_tokens = f"{item.get('total_tokens', 0) or 0:,}"
        gen_time = format_generation_time(item.get("generation_time_ms", 0))
        prompt_text = item.get('prompt', '') or ''
        
        # Truncate prompt if too long for display
        if len(prompt_text) > 100:
            prompt_text = prompt_text[:97] + "..."
        
        table_html += f"""
                <tr class="border-b hover:bg-gray-50">
                    <td class="px-4 py-3 text-sm">{timestamp}</td>
                    <td class="px-4 py-3 text-sm">{username}</td>
                    <td class="px-4 py-3 text-sm">{model}</td>
                    <td class="px-4 py-3 text-right">{prompt_tokens}</td>
                    <td class="px-4 py-3 text-right">{completion_tokens}</td>
                    <td class="px-4 py-3 text-right font-bold">{total_tokens}</td>
                    <td class="px-4 py-3 text-right">{gen_time}</td>
                    <td class="px-4 py-3 text-sm max-w-xs overflow-hidden">{prompt_text}</td>
                </tr>
        """
    
    # Close the table
    table_html += """
            </tbody>
        </table>
    </div>
    """
    
    # Return with NotStr to prevent escaping
    return NotStr(table_html)

def format_generation_time(ms):
    """Format generation time for display"""
    if not ms:
        return "N/A"
    
    if ms < 1000:
        return f"{ms:.0f} ms"
    else:
        return f"{ms/1000:.2f} sec"

def create_user_token_stats(user_stats):
    """Create a table showing token usage by user"""
    if not user_stats:
        return Div("No user statistics available", cls="text-gray-500 italic")
    
    return Div(
        H3("Usage by User", cls="text-lg font-semibold mb-6"),
        Table(
            Thead(
                Tr(
                    Th("Username", cls="px-4 py-2"),
                    Th("Requests", cls="px-4 py-2 text-right"),
                    Th("Prompt Tokens", cls="px-4 py-2 text-right"),
                    Th("Completion Tokens", cls="px-4 py-2 text-right"),
                    Th("Total Tokens", cls="px-4 py-2 text-right")
                ),
                cls="bg-gray-100"
            ),
            Tbody(
                [Tr(
                    Td(user.get("user_id", "") or "Anonymous", cls="px-4 py-2"),
                    Td(f"{user.get('total_requests', 0) or 0:,}", cls="px-4 py-2 text-right"),
                    Td(f"{user.get('total_prompt_tokens', 0) or 0:,}", cls="px-4 py-2 text-right"),
                    Td(f"{user.get('total_completion_tokens', 0) or 0:,}", cls="px-4 py-2 text-right"),
                    Td(f"{user.get('total_tokens', 0) or 0:,}", cls="px-4 py-2 text-right font-bold"),
                    cls="border-b hover:bg-gray-50"
                ) for user in user_stats]
            ),
            cls="w-full border-collapse"
        ),
        cls="overflow-x-auto mb-6"
    )

def format_timestamp(timestamp):
    """Format a timestamp for display."""
    try:
        # If timestamp is already a datetime object
        if hasattr(timestamp, 'strftime'):
            return timestamp.strftime('%Y-%m-%d %H:%M')
        
        # If timestamp is a string
        if isinstance(timestamp, str):
            # Handle ISO format strings
            if 'Z' in timestamp:
                timestamp = timestamp.replace('Z', '+00:00')
            dt = datetime.datetime.fromisoformat(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M')
        
        # Return as is if we can't handle it
        return str(timestamp)
    except (ValueError, AttributeError, TypeError) as e:
        # Fallback for any parsing errors
        return str(timestamp) 