# Import libraries
import logging, traceback, os
from flask import Flask, request, jsonify
import boto3, json
import utils  

# Grab destination email from EC2 server environment variables
DEFAULT_EMAIL = os.getenv("ALERT_EMAIL", "jakekraemer12@gmail.com")

# Initialize log and flask application 
log = logging.getLogger("app")
app = Flask(__name__)

# Handle new S3 upload, run knife detection, build page, and send alert
@app.route("/s3-event", methods=["POST"])
def s3_event():
    
    # Verify handshake
    try:
        payload = request.get_json(force=True)

        key = payload.get("object_key") or payload.get("key")
        if not key:
            return jsonify({"status": "error", "message": "'object_key' missing"}), 400
        log.info("Processing %s", key)

        # Knife detection
        knife = utils.detect_knife(key)

        # Build alert page
        page_url, ts = utils.create_alert_page(key, knife)

        # Build text to send be sent to email
        img_bytes = utils.s3.get_object(Bucket=utils.BUCKET, Key=key)["Body"].read()

        subj  = "🚨 Motion Alert – Knife Detected" if knife else "Motion Alert"
        plain = (f"Motion detected at {ts}\n"
                 f"Knife detected: {'Yes' if knife else 'No'}\n"
                 f"View: {page_url}")
        html  = (f"<p>Motion detected at {ts}.</p>"
                 f"<p>Knife detected: {'Yes' if knife else 'No'}.</p>"
                 f"<p><a href='{page_url}'>View details</a></p>"
                 f"<img src='cid:snap' style='max-width:100%'>")

        # Send email and log send
        utils.send_email(DEFAULT_EMAIL, subj, plain, html, img_bytes)
        log.info("Alert e-mail sent to %s", DEFAULT_EMAIL)

        # Return 200 when successful
        return jsonify({"status": "ok",
                        "knife": knife,
                        "page": page_url}), 200

    # Exception handling
    except Exception as e:
        log.error("Unhandled error:\n%s", traceback.format_exc())
        return jsonify({"status": "error", "message": str(e)}), 500

# Configure root logger to output to EC2 console
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    app.run(host="0.0.0.0", port=5000)
