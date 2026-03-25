import boto3, json, os, urllib.parse
from datetime import datetime

s3 = boto3.client("s3")
sqs = boto3.client("sqs")

QUEUE_URL = os.environ["QUEUE_URL"]
ORDERS_PREFIX = os.environ.get("ORDERS_PREFIX", "orders/")

def log(level, msg, **fields):
    print(json.dumps({"ts": datetime.utcnow().isoformat()+"Z", "level": level, "message": msg, **fields}, ensure_ascii=False))

def validate_order(order: dict):
    required = ["order_id", "customer_id", "created_at", "currency", "amount", "items"]
    for k in required:
        if k not in order:
            return False, f"missing_field:{k}"

    if not isinstance(order["items"], list) or len(order["items"]) == 0:
        return False, "items_empty"

    if not isinstance(order["amount"], (int, float)) or order["amount"] <= 0:
        return False, "amount_invalid"

    if order["currency"] not in ["EUR", "USD"]:
        return False, "currency_not_supported"

    # Simple consistency check (optional but nice)
    calc = 0.0
    for it in order["items"]:
        if it.get("qty", 0) <= 0 or it.get("unit_price", 0) < 0:
            return False, "item_invalid"
        calc += float(it["qty"]) * float(it["unit_price"])

    # Allow small rounding diff
    if abs(calc - float(order["amount"])) > 0.02:
        return False, "amount_mismatch"

    return True, "ok"

def lambda_handler(event, context):
    rec = event["Records"][0]
    bucket = rec["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(rec["s3"]["object"]["key"])

    if not key.startswith(ORDERS_PREFIX) or not key.endswith(".json"):
        log("INFO", "Ignored (not an order json)", bucket=bucket, key=key)
        return {"status": "IGNORED"}

    obj = s3.get_object(Bucket=bucket, Key=key)
    raw = obj["Body"].read().decode("utf-8")
    order = json.loads(raw)

    ok, reason = validate_order(order)
    order_id = order.get("order_id", "UNKNOWN")

    message = {
        "order": order,
        "meta": {
            "src_bucket": bucket,
            "src_key": key,
            "validated_at": datetime.utcnow().isoformat()+"Z",
            "validation_ok": ok,
            "validation_reason": reason
        }
    }

    # Always enqueue; worker decides status + DLQ path based on ok/ko
    sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))

    log("INFO", "Enqueued order", order_id=order_id, ok=ok, reason=reason, queue_url=QUEUE_URL)
    return {"status": "ENQUEUED", "order_id": order_id, "ok": ok, "reason": reason}
