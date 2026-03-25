import boto3
from PIL import Image
import io
import os
import json
import urllib.parse
from datetime import datetime

# AWS clients
s3 = boto3.client("s3")
cloudwatch = boto3.client("cloudwatch")

# Required
DEST_BUCKET = os.environ["DEST_BUCKET"]

# Optional (with defaults)
THUMB_SIZE = int(os.environ.get("THUMB_SIZE", "200"))  # square size (px)
OUTPUT_FORMAT = os.environ.get("OUTPUT_FORMAT", "JPEG").upper()  # JPEG | PNG
KEY_PREFIX = os.environ.get("KEY_PREFIX", "thumb_")
ALLOWED_EXTENSIONS = {
    ext.strip().lower()
    for ext in os.environ.get("ALLOWED_EXTENSIONS", ".jpg,.jpeg,.png").split(",")
    if ext.strip()
}
METRIC_NAMESPACE = os.environ.get("METRIC_NAMESPACE", "INOW/Lambda101")


def log(level: str, message: str, **fields):
    """Structured JSON logs for CloudWatch."""
    entry = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "level": level,
        "message": message,
        **fields,
    }
    print(json.dumps(entry, ensure_ascii=False))


def put_metric(name: str, value: float = 1.0, unit: str = "Count"):
    """Publish a custom CloudWatch metric."""
    cloudwatch.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=[
            {
                "MetricName": name,
                "Value": value,
                "Unit": unit,
            }
        ],
    )


def lambda_handler(event, context):
    """
    S3 ObjectCreated -> generate thumbnail -> write to DEST_BUCKET
    - Filters by extension
    - Logs explicitly
    - Uses environment variables
    - Publishes CloudWatch custom metric ImagesProcessed
    """
    try:
        record = event["Records"][0]
        src_bucket = record["s3"]["bucket"]["name"]
        raw_key = record["s3"]["object"]["key"]
        key = urllib.parse.unquote_plus(raw_key)

        ext = os.path.splitext(key)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            log(
                "INFO",
                "File ignored (extension not allowed)",
                src_bucket=src_bucket,
                key=key,
                ext=ext,
                allowed=list(ALLOWED_EXTENSIONS),
            )
            # Optional: track ignored files
            # put_metric("FilesIgnored", 1)
            return {"status": "IGNORED", "reason": "extension_not_allowed", "key": key}

        log(
            "INFO",
            "Processing image",
            src_bucket=src_bucket,
            key=key,
            thumb_size=THUMB_SIZE,
            output_format=OUTPUT_FORMAT,
        )

        obj = s3.get_object(Bucket=src_bucket, Key=key)
        image_bytes = obj["Body"].read()

        # Image processing
        img = Image.open(io.BytesIO(image_bytes))
        img.thumbnail((THUMB_SIZE, THUMB_SIZE))

        buffer = io.BytesIO()
        content_type = "image/jpeg"
        out_ext = ".jpg"

        if OUTPUT_FORMAT == "PNG":
            img.save(buffer, "PNG")
            content_type = "image/png"
            out_ext = ".png"
        else:
            # Default to JPEG (convert to RGB to avoid issues with alpha channels)
            img = img.convert("RGB")
            img.save(buffer, "JPEG", quality=85, optimize=True)

        buffer.seek(0)

        # Build destination key
        base_name = os.path.basename(key)
        base_no_ext = os.path.splitext(base_name)[0]
        dest_key = f"{KEY_PREFIX}{base_no_ext}{out_ext}"

        s3.put_object(
            Bucket=DEST_BUCKET,
            Key=dest_key,
            Body=buffer,
            ContentType=content_type,
        )

        # Publish a metric for observability
        put_metric("ImagesProcessed", 1)

        log(
            "INFO",
            "Thumbnail created",
            src_bucket=src_bucket,
            src_key=key,
            dest_bucket=DEST_BUCKET,
            dest_key=dest_key,
            size=THUMB_SIZE,
        )

        return {"status": "OK", "src": key, "dest": dest_key}

    except Exception as e:
        # Explicit error logging; re-raise to mark invocation as failed
        log(
            "ERROR",
            "Unhandled error",
            error=str(e),
            event_preview=str(event)[:800],
        )
        raise
