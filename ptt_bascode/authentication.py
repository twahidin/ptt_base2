import os
from dotenv import load_dotenv
load_dotenv()
import hashlib
from pymongo import MongoClient
import pytz
from datetime import datetime

# MongoDB connection setup
MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")

client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client[DATABASE_NAME]
users_collection = db["users"]
auth_logs_collection = db["auth_success_logs"]

def hash_password(password):
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(username, password):
    hashed_password = hash_password(password)
    user_document = users_collection.find_one({"username": username})
    if user_document and hashed_password == user_document['password']:
        record_auth_success_attempt(user_document)
        return user_document  # ✅ Return the full user document
    return None  # ❌ Instead of returning False, return None


def record_auth_success_attempt(user_document):
    """Logs successful authentication attempts."""
    timezone = pytz.timezone("Asia/Shanghai")
    utc_time = datetime.utcnow()
    local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone)
    timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")

    record = {
        "user_id": user_document["user_id"],
        "user_name": user_document["username"],
        "profile": user_document["profile"],
        "org_name": user_document["sch_name"],
        "timestamp": timestamp,
    }
    auth_logs_collection.insert_one(record)