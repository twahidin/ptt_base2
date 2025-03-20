from fasthtml.common import *
import datetime
from pathlib import Path

def create_token_usage_display():
    """Create the main token usage display form"""
    return Div(
        H2("Token Usage Statistics", cls="text-xl font-bold mb-4"),
        Div(
            Div(id="token-summary-container", cls="mb-6",
                hx_get="/api/tokens/summary",
                hx_trigger="load",
                hx_indicator="#loading-indicator"
            ),
            Div(
                H3("Usage History", cls="text-lg font-semibold mb-2"),
                Div(id="token-history-container",
                    hx_get="/api/tokens/history",
                    hx_trigger="load",
                    hx_indicator="#loading-indicator"
                ),
                cls="mb-6"
            ),
            Div(
                Button("Refresh Data", 
                    cls="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded",
                    hx_get="/api/tokens/refresh",
                    hx_target="#token-page-container",
                    hx_indicator="#loading-indicator"
                ),
                cls="mt-4"
            ),
            Div(
                Img(src="/static/img/loading.gif", cls="w-8 h-8"),
                " Loading...",
                cls="hidden items-center text-gray-500",
                id="loading-indicator"
            ),
            cls="bg-white p-6 rounded-lg shadow-md"
        ),
        cls="container mx-auto px-4 py-8",
        id="token-page-container"
    )

def create_token_summary(summary):
    """Create a summary view of token usage"""
    return Div(
        H3("Summary", cls="text-lg font-semibold mb-3"),
        Div(
            Div(
                Div("Total Requests", cls="text-gray-600"),
                Div(f"{summary['total_requests']:,}", cls="text-2xl font-bold"),
                cls="bg-blue-100 p-4 rounded"
            ),
            Div(
                Div("Prompt Tokens", cls="text-gray-600"),
                Div(f"{summary['total_prompt_tokens']:,}", cls="text-2xl font-bold"),
                cls="bg-green-100 p-4 rounded"
            ),
            Div(
                Div("Completion Tokens", cls="text-gray-600"),
                Div(f"{summary['total_completion_tokens']:,}", cls="text-2xl font-bold"),
                cls="bg-purple-100 p-4 rounded"
            ),
            Div(
                Div("Total Tokens", cls="text-gray-600"),
                Div(f"{summary['total_tokens']:,}", cls="text-2xl font-bold"),
                cls="bg-amber-100 p-4 rounded"
            ),
            cls="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6"
        ),
        
        # Models used section
        H4("Models Used", cls="text-md font-semibold mb-2"),
        Div(
            [Div(
                Div(model["model"] or "Unknown", cls="text-sm"),
                Div(f"{model['count']} requests", cls="text-xs text-gray-600"),
                cls="bg-gray-100 p-2 rounded-lg"
            ) for model in summary["models_used"]],
            cls="flex flex-wrap gap-2 mb-4"
        ) if summary["models_used"] else Div("No model data available", cls="text-gray-500 italic"),
        
        cls="token-summary"
    )

def create_token_history_table(history):
    """Create a table showing token usage history"""
    if not history:
        return Div("No token usage history found", cls="text-gray-500 italic")
    
    return Div(
        Table(
            Thead(
                Tr(
                    Th("Timestamp", cls="px-4 py-2"),
                    Th("Model", cls="px-4 py-2"),
                    Th("Prompt", cls="px-4 py-2"),
                    Th("Prompt Tokens", cls="px-4 py-2 text-right"),
                    Th("Completion Tokens", cls="px-4 py-2 text-right"),
                    Th("Total", cls="px-4 py-2 text-right")
                ),
                cls="bg-gray-100"
            ),
            Tbody(
                [Tr(
                    Td(format_timestamp(item["timestamp"]), cls="px-4 py-2 text-sm"),
                    Td(item["model"] or "Unknown", cls="px-4 py-2 text-sm"),
                    Td(item["prompt"] or "", cls="px-4 py-2 text-sm truncate max-w-xs"),
                    Td(f"{item['prompt_tokens']:,}", cls="px-4 py-2 text-right"),
                    Td(f"{item['completion_tokens']:,}", cls="px-4 py-2 text-right"),
                    Td(f"{item['total_tokens']:,}", cls="px-4 py-2 text-right font-bold"),
                    cls="border-b hover:bg-gray-50"
                ) for item in history]
            ),
            cls="min-w-full"
        ),
        cls="overflow-x-auto"
    )

def format_timestamp(timestamp_str):
    """Format ISO timestamp string to readable format"""
    try:
        dt = datetime.datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str 