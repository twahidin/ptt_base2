import sqlite3
import os
import datetime
import json
from pathlib import Path

# Check if we're running on Vercel or other read-only environment
IS_PRODUCTION = os.environ.get('VERCEL') == '1' or os.environ.get('PRODUCTION') == '1'

# Only create directories/database if we're not in production
DB_PATH = None
data_dir = None

if not IS_PRODUCTION:
    # Ensure data directory exists
    data_dir = Path("data")
    try:
        data_dir.mkdir(exist_ok=True)
        # Database path
        DB_PATH = Path("data/token_usage.db")
    except OSError:
        print("Warning: Unable to create data directory. Token tracking will be disabled.")

def init_db():
    """Initialize the token usage database"""
    if IS_PRODUCTION or DB_PATH is None:
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create token_usage table if it doesn't exist
        cursor.execute('''
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
        ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: Unable to initialize database: {e}")
    
def record_token_usage(model, prompt, prompt_tokens, completion_tokens, total_tokens, user_id="anonymous", session_id=None):
    """Record token usage to the database or log it"""
    # Create the record for logging or database storage
    record = {
        "timestamp": datetime.datetime.now().isoformat(),
        "model": model,
        "prompt": prompt[:100] if prompt else None,  # Use shorter version for logging
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "user_id": user_id,
        "session_id": session_id
    }
    
    # In production, just log the usage
    if IS_PRODUCTION or DB_PATH is None:
        print(f"Token usage: {json.dumps(record)}")
        return
    
    try:
        # Initialize database if it doesn't exist
        if not DB_PATH.exists():
            init_db()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Truncate prompt if too long
        if prompt and len(prompt) > 500:
            prompt = prompt[:497] + "..."
        
        # Insert token usage data
        cursor.execute('''
        INSERT INTO token_usage (timestamp, model, prompt, prompt_tokens, completion_tokens, total_tokens, user_id, session_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (record["timestamp"], model, prompt, prompt_tokens, completion_tokens, total_tokens, user_id, session_id))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: Failed to record token usage: {e}")
        # Still log it to console as fallback
        print(f"Token usage: {json.dumps(record)}")

def get_token_usage(limit=100, user_id=None):
    """Get recent token usage data"""
    if IS_PRODUCTION or DB_PATH is None or not DB_PATH.exists():
        return []
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM token_usage ORDER BY timestamp DESC LIMIT ?"
        params = (limit,)
        
        if user_id:
            query = "SELECT * FROM token_usage WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?"
            params = (user_id, limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        usage_data = [dict(row) for row in rows]
        
        conn.close()
        return usage_data
    except Exception as e:
        print(f"Warning: Failed to get token usage: {e}")
        return []

def get_token_usage_summary(user_id=None):
    """Get summary statistics of token usage"""
    if IS_PRODUCTION or DB_PATH is None or not DB_PATH.exists():
        return {
            "total_requests": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0, 
            "total_tokens": 0,
            "models_used": []
        }
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        where_clause = ""
        params = ()
        
        if user_id:
            where_clause = "WHERE user_id = ?"
            params = (user_id,)
        
        cursor.execute(f'''
        SELECT 
            COUNT(*) as total_requests,
            SUM(prompt_tokens) as total_prompt_tokens,
            SUM(completion_tokens) as total_completion_tokens,
            SUM(total_tokens) as total_tokens
        FROM token_usage
        {where_clause}
        ''', params)
        
        summary = dict(cursor.fetchone())
        
        # Get models used
        cursor.execute(f'''
        SELECT DISTINCT model, COUNT(*) as count
        FROM token_usage
        {where_clause}
        GROUP BY model
        ORDER BY count DESC
        ''', params)
        
        models = [{"model": row["model"], "count": row["count"]} for row in cursor.fetchall()]
        summary["models_used"] = models
        
        conn.close()
        return summary
    except Exception as e:
        print(f"Warning: Failed to get token usage summary: {e}")
        return {
            "total_requests": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0, 
            "total_tokens": 0,
            "models_used": []
        }