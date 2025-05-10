# Standard library imports
import time, os

# Libraries for camera operation, AWS SDK, HTTP client
from picamera2 import Picamera2
import boto3
import requests

# Configuration for S3
BUCKET = 'iotfinalbucket'
REGION = 'us-east-2'
ACCESS_KEY = 'AKIAQGGKUUGPVUR5OPU7'
SECRET_KEY = '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'
IMG_DIR = '/home/pi/images'
API_URL = "http://54.153.13.152:5000/s3-event" 

# Create file, give name of file current timestamp
ts = time.strftime('%Y%m%d-%H%M%S')
filename = f"{ts}.jpg"
path = f"/home/pi/images/{filename}"

# Camera Inititialization
camera = Picamera2()

# Ensures image directory exists
os.makedirs(IMG_DIR, exist_ok=True)

# Initialize boto3 S3 client
s3 = boto3.client('s3', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

# Capture photo and upload to S3
camera.start()
camera.capture_file(path)
camera.close()
s3.upload_file(path, BUCKET, filename)

# Wait for file to upload
time.sleep(10)

# POST JSON body to Flask route
try:
    requests.post(API_URL, json={"object_key": filename})
except Exception as e:
    print("POST failed:", e)








