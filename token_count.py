import os
import datetime
import json
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import atexit

# Load environment variables
load_dotenv()

# Get the database connection string
DB_URL = os.environ.get('DATABASE_URL')

# Create a connection pool if DB_URL is available
connection_pool = None
if DB_URL:
    try:
        connection_pool = pool.SimpleConnectionPool(
            1,  # Minimum number of connections
            10, # Maximum number of connections
            DB_URL
        )
        print("PostgreSQL connection pool created successfully")
    except Exception as e:
        print(f"Warning: Unable to create database connection pool: {e}")

def init_db():
    """Initialize the token usage database in PostgreSQL"""
    if connection_pool is None:
        return
    
    try:
        # Get a connection from the pool
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        
        # Create token_usage table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS token_usage (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP,
            model TEXT,
            prompt TEXT,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            user_id TEXT,
            session_id TEXT,
            generation_time_ms FLOAT
        )
        ''')
        
        conn.commit()
        
        # Return the connection to the pool
        cursor.close()
        connection_pool.putconn(conn)
        
        print("Token usage table initialized in PostgreSQL")
    except Exception as e:
        print(f"Warning: Unable to initialize database: {e}")

def record_token_usage(model, prompt, prompt_tokens, completion_tokens, total_tokens, user_id="anonymous", session_id=None, generation_time_ms=0):
    """Record token usage to the PostgreSQL database or log it"""
    # Create the record for logging or database storage
    timestamp = datetime.datetime.now()
    record = {
        "timestamp": timestamp.isoformat(),
        "model": model,
        "prompt": prompt[:100] if prompt else None,  # Use shorter version for logging
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "user_id": user_id,
        "session_id": session_id,
        "generation_time_ms": generation_time_ms
    }
    
    # Debug output
    print(f"\n-----TOKEN USAGE RECORD-----")
    print(f"User: {user_id}, Model: {model}")
    print(f"Tokens - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
    print(f"Generation Time: {generation_time_ms:.2f} ms ({generation_time_ms/1000:.2f} seconds)")
    
    # If no connection pool is available, just log
    if connection_pool is None:
        print(f"Token usage: {json.dumps(record)}")
        return
    
    try:
        # Get a connection from the pool
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        
        # Insert token usage data
        cursor.execute('''
        INSERT INTO token_usage (timestamp, model, prompt, prompt_tokens, completion_tokens, total_tokens, user_id, session_id, generation_time_ms)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (timestamp, model, prompt, prompt_tokens, completion_tokens, total_tokens, user_id, session_id, generation_time_ms))
        
        conn.commit()
        print(f"Successfully recorded token usage for user {user_id} with model {model}")
        
        # Return the connection to the pool
        cursor.close()
        connection_pool.putconn(conn)
    except Exception as e:
        print(f"Warning: Failed to record token usage: {e}")
        import traceback
        traceback.print_exc()
        # Still log it to console as fallback
        print(f"Token usage: {json.dumps(record)}")

def get_token_usage(limit=100, user_id=None):
    """Get recent token usage data from PostgreSQL"""
    if connection_pool is None:
        return []
    
    try:
        # Get a connection from the pool
        conn = connection_pool.getconn()
        
        # Use RealDictCursor to get results as dictionaries
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        query = "SELECT * FROM token_usage ORDER BY timestamp DESC LIMIT %s"
        params = (limit,)
        
        if user_id:
            query = "SELECT * FROM token_usage WHERE user_id = %s ORDER BY timestamp DESC LIMIT %s"
            params = (user_id, limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert rows to list of dicts
        usage_data = [dict(row) for row in rows]
        
        # Return the connection to the pool
        cursor.close()
        connection_pool.putconn(conn)
        
        return usage_data
    except Exception as e:
        print(f"Warning: Failed to get token usage: {e}")
        return []

def get_token_usage_summary(user_id=None):
    """Get summary statistics of token usage from PostgreSQL"""
    empty_summary = {
        "total_requests": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0, 
        "total_tokens": 0,
        "models_used": []
    }
    
    if connection_pool is None:
        print("Database unavailable for token summary. Using empty summary.")
        return empty_summary
    
    try:
        # Get a connection from the pool
        conn = connection_pool.getconn()
        
        # Use RealDictCursor to get results as dictionaries
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        where_clause = ""
        params = ()
        
        if user_id:
            where_clause = "WHERE user_id = %s"
            params = (user_id,)
            print(f"Getting token summary for specific user: {user_id}")
        else:
            print("Getting token summary for all users")
        
        cursor.execute(f'''
        SELECT 
            COUNT(*) as total_requests,
            COALESCE(SUM(prompt_tokens), 0) as total_prompt_tokens,
            COALESCE(SUM(completion_tokens), 0) as total_completion_tokens,
            COALESCE(SUM(total_tokens), 0) as total_tokens
        FROM token_usage
        {where_clause}
        ''', params)
        
        summary = dict(cursor.fetchone())
        print(f"Retrieved summary data: {json.dumps(summary)}")
        
        # Handle None values from PostgreSQL
        for key in summary:
            if summary[key] is None:
                summary[key] = 0
        
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
        print(f"Retrieved {len(models)} model usage records")
        
        # Return the connection to the pool
        cursor.close()
        connection_pool.putconn(conn)
        
        return summary
    except Exception as e:
        print(f"Warning: Failed to get token usage summary: {e}")
        import traceback
        traceback.print_exc()
        return empty_summary

def get_token_usage_by_user():
    """Get token usage statistics grouped by user from PostgreSQL"""
    if connection_pool is None:
        return []
    
    try:
        # Get a connection from the pool
        conn = connection_pool.getconn()
        
        # Use RealDictCursor to get results as dictionaries
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute('''
        SELECT 
            user_id,
            COUNT(*) as total_requests,
            COALESCE(SUM(prompt_tokens), 0) as total_prompt_tokens,
            COALESCE(SUM(completion_tokens), 0) as total_completion_tokens,
            COALESCE(SUM(total_tokens), 0) as total_tokens
        FROM token_usage
        GROUP BY user_id
        ORDER BY total_tokens DESC
        ''')
        
        usage_by_user = [dict(row) for row in cursor.fetchall()]
        
        # Return the connection to the pool
        cursor.close()
        connection_pool.putconn(conn)
        
        return usage_by_user
    except Exception as e:
        print(f"Warning: Failed to get token usage by user: {e}")
        return []

def get_token_record(record_id):
    """Get a specific token usage record by ID"""
    if connection_pool is None:
        return None
    
    try:
        # Get a connection from the pool
        conn = connection_pool.getconn()
        
        # Use RealDictCursor to get results as dictionaries
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT * FROM token_usage WHERE id = %s", (record_id,))
        record = cursor.fetchone()
        
        # Return the connection to the pool
        cursor.close()
        connection_pool.putconn(conn)
        
        return dict(record) if record else None
    except Exception as e:
        print(f"Warning: Failed to get token record: {e}")
        return None

def reset_token_database():
    """Reset the token database (CAUTION: Deletes all records)"""
    if connection_pool is None:
        return {"success": False, "message": "Database connection unavailable"}
    
    try:
        # Get a connection from the pool
        conn = connection_pool.getconn()
        cursor = conn.cursor()
        
        # Truncate the token_usage table
        cursor.execute("TRUNCATE TABLE token_usage")
        conn.commit()
        
        # Return the connection to the pool
        cursor.close()
        connection_pool.putconn(conn)
        
        return {
            "success": True,
            "message": "Token usage database has been reset successfully."
        }
    except Exception as e:
        print(f"Warning: Failed to reset token database: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "message": f"Failed to reset token database: {str(e)}"
        }

# Register a function to close all connections when the application shuts down
def close_all_connections():
    if connection_pool:
        print("Closing all database connections")
        connection_pool.closeall()

# Register the cleanup function
atexit.register(close_all_connections)