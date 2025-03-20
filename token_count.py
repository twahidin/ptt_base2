import sqlite3
import os
import datetime
from pathlib import Path

# Ensure data directory exists
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

# Database path
DB_PATH = Path("data/token_usage.db")

def init_db():
    """Initialize the token usage database"""
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
    
def record_token_usage(model, prompt, prompt_tokens, completion_tokens, total_tokens, user_id="anonymous", session_id=None):
    """Record token usage to the database"""
    # Initialize database if it doesn't exist
    if not DB_PATH.exists():
        init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get current timestamp
    timestamp = datetime.datetime.now().isoformat()
    
    # Truncate prompt if too long
    if prompt and len(prompt) > 500:
        prompt = prompt[:497] + "..."
    
    # Insert token usage data
    cursor.execute('''
    INSERT INTO token_usage (timestamp, model, prompt, prompt_tokens, completion_tokens, total_tokens, user_id, session_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, model, prompt, prompt_tokens, completion_tokens, total_tokens, user_id, session_id))
    
    conn.commit()
    conn.close()

def get_token_usage(limit=100, user_id=None):
    """Get recent token usage data"""
    if not DB_PATH.exists():
        init_db()
        return []
    
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

def get_token_usage_summary(user_id=None):
    """Get summary statistics of token usage"""
    if not DB_PATH.exists():
        init_db()
        return {
            "total_requests": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0, 
            "total_tokens": 0,
            "models_used": []
        }
    
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