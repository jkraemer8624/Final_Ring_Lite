# Impport libraries
import os, logging, traceback, boto3, smtplib
from datetime import datetime, timezone
from typing import Optional, Tuple
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.image     import MIMEImage

# Basic configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("utils")

# Grad environment variables saved to EC2 server
BUCKET  = os.getenv("BUCKET",  "iotfinalbucket")
REGION  = os.getenv("REGION",  "us-east-2")
SITEURL = f"http://{BUCKET}.s3-website.{REGION}.amazonaws.com"

# Recphnized image extensions for list-bucket
_IMG_EXT = {".jpg", ".jpeg", ".png", ".gif"}

# AWS services to be used
s3  = boto3.client("s3",  region_name=REGION)
rek = boto3.client("rekognition", region_name=REGION)

# Detect knife helper function using Rekognition, will return true or false based on if knife is detected
def detect_knife(key: str, bucket: str = BUCKET, min_conf: int = 70) -> bool:

    try:
        # Call AWS Rekognition and fetch up to 50 labels AWS created for said image within minimum confidence threshold
        resp = rek.detect_labels(
            Image={"S3Object": {"Bucket": bucket, "Name": key}},
            MaxLabels=50,
            MinConfidence=min_conf,
        )

        # Extract label names and place in list
        labels = [l["Name"] for l in resp["Labels"]]
        log.info("Rekognition labels for %s: %s", key, labels)

        # Go through labels and determine if "knife" was a label returned
        knife = any(l["Name"].lower() == "knife" for l in resp["Labels"])
        log.info("Knife detected: %s", knife)
        return knife

    except Exception as e:
        # Log error and return false if "knife" is not found in labels
        log.error("detect_knife failed: %s\n%s", e, traceback.format_exc())
        return False


# Create alert page helper function, generates and HTML status page to the bucket's website endpoint
def create_alert_page(key: str, knife: bool, bucket: str = BUCKET) -> Tuple[str, str]:
    
    # Build UTC timestamp 
    ts   = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Derive filenames - strip extension to be used for HTML
    base = os.path.splitext(os.path.basename(key))[0]
    html_key = f"alerts/{base}.html"

    # File template placeholders for knife detection text and image url
    knife_txt = "Yes" if knife else "No"
    img_url   = f"https://{bucket}.s3.amazonaws.com/{key}"

    # Self contained HTML
    html = f"""<!doctype html><html><head>
<meta charset='utf-8'><title>Intruder Alert</title></head>
<body style='font-family:sans-serif;max-width:600px;margin:auto'>
<h1>🚨 Intruder Alert 🚨</h1>
<p><b>Timestamp:</b> {ts}</p>
<p><b>Knife Detected:</b> {knife_txt}</p>
<img src='{img_url}' style='width:100%;border:1px solid #ccc'>
</body></html>"""

    # Uplaod to bucket
    s3.put_object(Bucket=bucket,
                  Key=html_key,
                  Body=html.encode(),
                  ContentType="text/html")

    return f"{SITEURL}/{html_key}", ts

# Helper function to send email notification via GMAIL SMTP
def send_email(to_addr: str, subject: str, plain: str, html: str, img_bytes: bytes) -> None:

    # Grab environment variables from EC2 server for notifying email
    sender = os.environ["GMAIL_USER"]
    pwd    = os.environ["GMAIL_APP_PASS"]

    # Build root MIME message and initialize to be able to add attachments
    msg = MIMEMultipart("related")

    # Set header
    msg["From"], msg["To"], msg["Subject"] = sender, to_addr, subject

    # Create part of email text that allows regukar text and then HTML
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(plain, "plain"))
    alt.attach(MIMEText(html,  "html"))
    msg.attach(alt)

    # Attach the image 
    img = MIMEImage(img_bytes)
    img.add_header("Content-ID", "<snap>") # Matches <img src='cid:snap> in HTML
    msg.attach(img)

    # Send email via SMPT
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        # Upgrade connection to encrypted TLS
        s.starttls()
        # Authenticate with GMAIL app password
        s.login(sender, pwd)
        s.sendmail(sender, [to_addr], msg.as_string())
