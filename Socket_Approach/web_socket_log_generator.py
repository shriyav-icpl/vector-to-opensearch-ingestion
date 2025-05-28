import socket
import time
import json
import random
from datetime import datetime
import os
from dotenv import load_dotenv  # Import to load environment variables from .env file (if used)

# Load environment variables from .env file (if you use python-dotenv)
load_dotenv()

# This is the Vector HTTP source endpoint you will configure 

port = os.getenv("PORT")  # Port for the TCP source
host = os.getenv("HOST")  # Host for the TCP source


messages = [
    "User logged in",
    "Failed to load resource",
    "Connection timeout",
    "Database updated",
    "Unexpected error occurred"
]

def log_stream():
    with socket.create_connection((host, port)) as s:
        print(f"Connected to Vector TCP socket at {host}:{port}")
        while True:
            log_entry = {
                "timestamp": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
                "level": "INFO",
                "message": random.choice(messages)
            }
            json_log = json.dumps(log_entry) + "\n"
            s.sendall(json_log.encode('utf-8'))
            print(f"Sent: {json_log.strip()}")
            time.sleep(3)

if __name__ == "__main__":
    log_stream()
