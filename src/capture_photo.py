#import time, os
from picamera2 import Picamera2
import boto3

BUCKET = 'intruder-images-bucket456909876432'
REGION = 'us-west-1'
ACCESS_KEY = 'AKIARPAZFN3Y4F2MWSKW'
SECRET_KEY = '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'
IMG_DIR = '/home/pi/images'

camera = Picamera2()
#os.makedirs(IMG_DIR, exist_ok=True)
s3 = boto3.client('s3', region_name=REGION, aws_access_key_id=ACCESS_KEY, aws_secret_access_key=SECRET_KEY)

#ts = time.strftime('%Y%m%d-%H%M%S')
path = 'test_image.jpg'
camera.start()
camera.capture_file(path)
camera.close()
s3.upload_file(path, BUCKET, 'test_image.jpg')







