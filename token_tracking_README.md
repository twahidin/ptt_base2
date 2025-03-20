# Token Usage Monitoring System

This system tracks and displays token usage for OpenAI and Anthropic API calls in the HTML5 Generator.

## Features

- Records prompt tokens, completion tokens, and total tokens for each API call
- Stores data in an SQLite database
- Displays usage history and summary statistics via HTMX-powered UI
- Supports filtering by user ID

## Components

1. **token_count.py**: Core database operations for recording and retrieving token usage data
2. **components/token_form.py**: UI components for displaying token usage stats using HTMX and FASTHTML
3. **routes/token_routes.py**: API endpoints and page routes for token tracking
4. **routes/html_5.py**: Modified to record token usage for API calls

## Database Schema

The token usage is stored in an SQLite database (`data/token_usage.db`) with the following schema:

```sql
CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    model TEXT,
    prompt TEXT,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    user_id TEXT,
    session_id TEXT
)
```

## Usage

1. Access the Token Usage page through the side menu "Token Usage Monitoring"
2. View summary statistics at the top of the page
3. Browse detailed token usage history in the table below
4. Click "Refresh Data" to update the display with the latest information

## Implementation Notes

- Token counts are automatically recorded during HTML5 Generator API calls
- For OpenAI, token counts are provided directly in the API response
- For Anthropic/Claude, prompt tokens are counted before making the API call, and completion tokens are retrieved from the response

## Future Improvements

- Add export functionality (CSV, JSON)
- Implement date range filtering
- Add visualization charts for usage trends
- Extend token tracking to other AI-powered features 