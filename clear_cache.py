#!/usr/bin/env python

import os
import redis
import sys

# Check for Redis URL (same as in api.py)
REDIS_URL = os.environ.get('HTML5_REDIS_URL')
if not REDIS_URL:
    print("WARNING: HTML5_REDIS_URL environment variable not set. Using default localhost connection.")
    REDIS_URL = "redis://localhost:6379/0"

# Initialize Redis connection
try:
    redis_client = redis.from_url(REDIS_URL)
    redis_client.ping()  # Test connection
    print("Connected to Redis successfully")
except Exception as e:
    print(f"Error connecting to Redis: {str(e)}")
    sys.exit(1)

def clear_preview_cache():
    """Clear all HTML preview caches from Redis"""
    # Get all preview cache keys
    preview_keys = redis_client.keys("gallery_preview_html_*")
    
    if not preview_keys:
        print("No preview caches found.")
        return 0
    
    # Delete all preview cache keys
    deleted_count = 0
    for key in preview_keys:
        print(f"Deleting cache: {key}")
        redis_client.delete(key)
        deleted_count += 1
    
    print(f"Deleted {deleted_count} preview caches.")
    return deleted_count

if __name__ == "__main__":
    clear_preview_cache() 