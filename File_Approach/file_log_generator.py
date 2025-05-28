import logging
import time
import random
 
# Set up logging to file

logging.basicConfig(
    filename='file_log_generatorfile.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
 
# Generate logs forever

messages = [
    "User logged in",
    "Failed to load resource",
    "Connection timeout",
    "Database updated",
    "Unexpected error occurred"
]
 
while True:
    msg = random.choice(messages)
    logging.info(msg)
    time.sleep(3)

 