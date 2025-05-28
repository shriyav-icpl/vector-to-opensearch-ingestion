import time
import random
import requests
import json
import os
from dotenv import load_dotenv  # Import to load environment variables from .env file (if used)


# Load environment variables from .env file (if you use python-dotenv)
load_dotenv()

# This is the Vector HTTP source endpoint you will configure 

base_url = os.getenv("VECTOR_HTTP_SOURCE")  # Base URL of the API
 
messages = [
    "User logged in",
    "Failed to load resource",
    "Connection timeout",
    "Database updated",
    "Unexpected error occurred"
]
 
while True:
    log_entry = {
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "level": "INFO",
        "message": random.choice(messages)
    } 
    try:
        response = requests.post(
            base_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(log_entry)
        )
        print(f"Sent log: {log_entry} - Status: {response.status_code}")
    except Exception as e:
        print(f"Failed to send log: {e}") 
    time.sleep(3)

 