#!/usr/bin/env python

import os
import json
import redis
import argparse
from tabulate import tabulate
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

def get_submission_count():
    """Get the total number of submissions"""
    count = redis_client.get("submissions_count")
    if count is None:
        return 0
    return int(count)

def get_submission(submission_id):
    """Get a specific submission by ID"""
    submission_data = redis_client.hget("submission", submission_id)
    if submission_data:
        return json.loads(submission_data)
    return None

def delete_submission(submission_id):
    """Delete a specific submission by ID"""
    # Check if submission exists
    if not redis_client.hexists("submission", submission_id):
        return False
    
    # Delete the submission
    result = redis_client.hdel("submission", submission_id)
    return result > 0

def delete_all_submissions():
    """Delete all submissions from Redis"""
    # Get all submission keys
    submission_ids = redis_client.hkeys("submission")
    
    if not submission_ids:
        return 0
    
    # Delete all submissions
    deleted_count = 0
    for sid in submission_ids:
        if redis_client.hdel("submission", sid) > 0:
            deleted_count += 1
    
    # Reset submissions count
    redis_client.set("submissions_count", 0)
    
    return deleted_count

def get_all_submissions():
    """Get all submissions in the Redis database"""
    all_submissions = []
    submission_ids = redis_client.hkeys("submission")
    for sid in submission_ids:
        submission_data = redis_client.hget("submission", sid)
        if submission_data:
            submission = json.loads(submission_data)
            submission['id'] = sid  # Add ID to the submission data
            all_submissions.append(submission)
    return all_submissions

def get_all_draft_keys():
    """Get all draft-related keys in Redis"""
    return redis_client.keys("html5_drafts:*") + redis_client.keys("html5_drafts_count:*")

def get_drafts_by_user():
    """Get count of drafts by user"""
    draft_keys = redis_client.keys("html5_drafts:*")
    user_drafts = {}
    
    for key in draft_keys:
        user_id = key.decode('utf-8').split(':')[1] if isinstance(key, bytes) else key.split(':')[1]
        draft_count = redis_client.hlen(key)
        user_drafts[user_id] = draft_count
    
    return user_drafts

def delete_all_drafts(user_id=None):
    """
    Delete all drafts for a specific user or all users
    
    Args:
        user_id (str, optional): User ID to delete drafts for. If None, delete all drafts.
        
    Returns:
        tuple: (deleted_count, deleted_keys) - Number of drafts deleted and keys deleted
    """
    if user_id:
        # Delete drafts for a specific user
        user_drafts_key = f"html5_drafts:{user_id}"
        user_count_key = f"html5_drafts_count:{user_id}"
        
        # Get all draft IDs for this user
        draft_ids = redis_client.hkeys(user_drafts_key)
        deleted_count = 0
        
        if draft_ids:
            # Delete each draft
            for draft_id in draft_ids:
                deleted_count += redis_client.hdel(user_drafts_key, draft_id)
            
            # Reset the draft count
            redis_client.delete(user_count_key)
            
            return deleted_count, 2  # Count drafts and the count key
        return 0, 0
    else:
        # Delete all drafts for all users
        draft_keys = get_all_draft_keys()
        deleted_keys = 0
        total_drafts = 0
        
        for key in draft_keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            
            # For draft hash, count the drafts first
            if key_str.startswith("html5_drafts:"):
                total_drafts += redis_client.hlen(key)
            
            # Delete the key
            redis_client.delete(key)
            deleted_keys += 1
        
        return total_drafts, deleted_keys

def get_submissions_by_gallery_type(gallery_type):
    """Get submissions filtered by gallery type"""
    all_submissions = get_all_submissions()
    return [s for s in all_submissions if s.get('galleryType') == gallery_type]

def get_available_gallery_types():
    """Get a list of all available gallery types"""
    all_submissions = get_all_submissions()
    return list(set(s.get('galleryType') for s in all_submissions if 'galleryType' in s))

def get_submission_stats():
    """Get statistics about the submissions"""
    all_submissions = get_all_submissions()
    stats = {
        'total_submissions': len(all_submissions),
        'by_gallery_type': {},
        'by_level': {},
        'by_subject': {}
    }
    
    for s in all_submissions:
        # Count by gallery type
        gallery_type = s.get('galleryType')
        if gallery_type:
            stats['by_gallery_type'][gallery_type] = stats['by_gallery_type'].get(gallery_type, 0) + 1
        
        # Count by level
        level = s.get('level')
        if level:
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
        
        # Count by subject
        subject = s.get('subject')
        if subject:
            stats['by_subject'][subject] = stats['by_subject'].get(subject, 0) + 1
    
    return stats

def list_all_keys():
    """List all keys in the Redis database"""
    return redis_client.keys("*")

def get_redis_info():
    """Get Redis server information"""
    return redis_client.info()

def print_submission(submission):
    """Print a submission in a readable format"""
    if not submission:
        print("Submission not found")
        return
    
    # Print basic info
    print(f"Title: {submission.get('title', 'N/A')}")
    print(f"Author: {submission.get('author', 'N/A')}")
    print(f"Gallery Type: {submission.get('galleryType', 'N/A')}")
    print(f"Level: {submission.get('level', 'N/A')}")
    print(f"Subject: {submission.get('subject', 'N/A')}")
    
    # Print ZIP URL
    print(f"ZIP URL: {submission.get('zipUrl', 'N/A')}")
    
    # Print reference images
    ref_images = submission.get('referenceImages', [])
    print(f"Reference Images: {len(ref_images)}")
    for i, img in enumerate(ref_images):
        print(f"  {i+1}. {img}")
    
    # Print other fields if present
    for key, value in submission.items():
        if key not in ['title', 'author', 'galleryType', 'level', 'subject', 'zipUrl', 'referenceImages']:
            print(f"{key}: {value}")

def main():
    parser = argparse.ArgumentParser(description='Query Redis data for HTML5 submissions')
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List submissions
    list_parser = subparsers.add_parser('list', help='List submissions')
    list_parser.add_argument('--gallery-type', help='Filter by gallery type')
    list_parser.add_argument('--format', choices=['table', 'json'], default='table', help='Output format')
    
    # Get submission details
    get_parser = subparsers.add_parser('get', help='Get submission details')
    get_parser.add_argument('id', help='Submission ID')
    
    # Delete a submission
    delete_parser = subparsers.add_parser('delete', help='Delete a submission')
    delete_parser.add_argument('id', help='Submission ID to delete')
    
    # Delete all submissions
    delete_all_parser = subparsers.add_parser('delete-all', help='Delete all submissions')
    delete_all_parser.add_argument('--confirm', action='store_true', help='Confirm deletion of all submissions')
    
    # Show statistics
    subparsers.add_parser('stats', help='Show submission statistics')
    
    # List gallery types
    subparsers.add_parser('gallery-types', help='List available gallery types')
    
    # List all Redis keys
    subparsers.add_parser('keys', help='List all Redis keys')
    
    # Show Redis info
    subparsers.add_parser('info', help='Show Redis server information')
    
    # Delete drafts
    delete_drafts_parser = subparsers.add_parser('delete-drafts', help='Delete all HTML5 drafts')
    delete_drafts_parser.add_argument('--user', help='User ID to delete drafts for (if omitted, delete all drafts)')
    delete_drafts_parser.add_argument('--confirm', action='store_true', help='Confirm deletion without prompting')
    
    # List drafts
    list_drafts_parser = subparsers.add_parser('list-drafts', help='List HTML5 drafts by user')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute command
    if args.command == 'list':
        if args.gallery_type:
            submissions = get_submissions_by_gallery_type(args.gallery_type)
            print(f"Found {len(submissions)} submissions with gallery type '{args.gallery_type}'")
        else:
            submissions = get_all_submissions()
            print(f"Found {len(submissions)} total submissions")
        
        if not submissions:
            return
        
        if args.format == 'json':
            print(json.dumps(submissions, indent=2))
        else:
            # Create table data
            table_data = []
            for s in submissions:
                table_data.append([
                    s.get('id', 'N/A'),
                    s.get('title', 'N/A'),
                    s.get('author', 'N/A'),
                    s.get('galleryType', 'N/A'),
                    s.get('level', 'N/A'),
                    s.get('subject', 'N/A')
                ])
            
            # Print table
            headers = ['ID', 'Title', 'Author', 'Gallery Type', 'Level', 'Subject']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    elif args.command == 'get':
        submission = get_submission(args.id)
        print_submission(submission)
    
    elif args.command == 'delete':
        # Get the submission first to show what's being deleted
        submission = get_submission(args.id)
        if not submission:
            print(f"Submission with ID {args.id} not found")
            return
        
        # Show submission details
        print(f"Deleting submission {args.id}:")
        print(f"  Title: {submission.get('title', 'N/A')}")
        print(f"  Author: {submission.get('author', 'N/A')}")
        print(f"  Gallery Type: {submission.get('galleryType', 'N/A')}")
        
        # Confirm deletion
        confirm = input("Are you sure you want to delete this submission? (y/n): ")
        if confirm.lower() != 'y':
            print("Deletion cancelled")
            return
        
        # Delete the submission
        success = delete_submission(args.id)
        if success:
            print(f"Submission with ID {args.id} deleted successfully")
        else:
            print(f"Failed to delete submission with ID {args.id}")
    
    elif args.command == 'delete-all':
        # Require confirmation flag
        if not args.confirm:
            print("WARNING: This will delete ALL submissions from Redis")
            print("To confirm, run again with --confirm flag")
            return
        
        # Double-check with user
        total_submissions = len(get_all_submissions())
        print(f"WARNING: You are about to delete ALL {total_submissions} submissions from Redis")
        confirm = input("Are you ABSOLUTELY sure? This cannot be undone! (yes/no): ")
        if confirm.lower() != 'yes':
            print("Deletion cancelled")
            return
        
        # Delete all submissions
        deleted_count = delete_all_submissions()
        print(f"Deleted {deleted_count} submissions successfully")
    
    elif args.command == 'stats':
        stats = get_submission_stats()
        print(f"Total Submissions: {stats['total_submissions']}")
        
        print("\nBy Gallery Type:")
        for gallery_type, count in stats['by_gallery_type'].items():
            print(f"  {gallery_type}: {count}")
        
        print("\nBy Level:")
        for level, count in stats['by_level'].items():
            print(f"  {level}: {count}")
        
        print("\nBy Subject:")
        for subject, count in stats['by_subject'].items():
            print(f"  {subject}: {count}")
    
    elif args.command == 'gallery-types':
        gallery_types = get_available_gallery_types()
        print("Available Gallery Types:")
        for gallery_type in gallery_types:
            print(f"  - {gallery_type}")
    
    elif args.command == 'keys':
        keys = list_all_keys()
        print(f"Redis Keys ({len(keys)}):")
        for key in keys:
            print(f"  - {key}")
    
    elif args.command == 'info':
        info = get_redis_info()
        print("Redis Server Information:")
        for section, data in info.items():
            if isinstance(data, dict):
                print(f"\n{section}:")
                for key, value in data.items():
                    print(f"  {key}: {value}")
            else:
                print(f"{section}: {data}")
    
    elif args.command == 'delete-drafts':
        user_id = args.user
        
        # Get draft counts first
        if user_id:
            user_drafts = get_drafts_by_user()
            draft_count = user_drafts.get(user_id, 0)
            print(f"Found {draft_count} drafts for user {user_id}")
        else:
            user_drafts = get_drafts_by_user()
            total_drafts = sum(user_drafts.values())
            print(f"Found {total_drafts} total drafts across {len(user_drafts)} users")
            
            if user_drafts:
                print("\nDrafts by user:")
                for uid, count in user_drafts.items():
                    print(f"  {uid}: {count} drafts")
        
        # Confirm deletion
        if not args.confirm:
            if user_id:
                confirm = input(f"Are you sure you want to delete all drafts for user {user_id}? (y/n): ")
            else:
                confirm = input("Are you sure you want to delete ALL drafts for ALL users? (y/n): ")
                
            if confirm.lower() != 'y':
                print("Deletion cancelled")
                return
        
        # Delete drafts
        deleted_drafts, deleted_keys = delete_all_drafts(user_id)
        
        if user_id:
            print(f"Deleted {deleted_drafts} drafts for user {user_id}")
        else:
            print(f"Deleted {deleted_drafts} drafts across {len(user_drafts)} users ({deleted_keys} Redis keys)")
    
    elif args.command == 'list-drafts':
        user_drafts = get_drafts_by_user()
        total_drafts = sum(user_drafts.values())
        
        print(f"Found {total_drafts} total drafts across {len(user_drafts)} users")
        
        if user_drafts:
            print("\nDrafts by user:")
            table_data = []
            for uid, count in user_drafts.items():
                table_data.append([uid, count])
            
            headers = ['User ID', 'Draft Count']
            print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 