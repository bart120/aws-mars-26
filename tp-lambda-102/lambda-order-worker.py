import boto3, json, os
from datetime import datetime
from botocore.exceptions import ClientError

ddb = boto3.client("dynamodb")
cw = boto3.client("cloudwatch")

DDB_TABLE = os.environ["DDB_TABLE"]
METRIC_NAMESPACE = os.environ.get("METRIC_NAMESPACE", "INOW/Orders")
METRIC_DIMENSION_ENV = os.environ.get("METRIC_DIMENSION_ENV", "tp")  # optionnel

def log(level, msg, **fields):
    print(json.dumps({"ts": datetime.utcnow().isoformat()+"Z", "level": level, "message": msg, **fields}, ensure_ascii=False))

def put_metric(metric_name: str, value: float = 1.0, unit: str = "Count"):
    cw.put_metric_data(
        Namespace=METRIC_NAMESPACE,
        MetricData=[{
            "MetricName": metric_name,
            "Value": value,
            "Unit": unit,
            "Dimensions": [
                {"Name": "Env", "Value": METRIC_DIMENSION_ENV}
            ]
        }]
    )

def pk(order_id: str) -> str:
    return f"ORDER#{order_id}"

def put_status(order_id: str, status: str, **extras):
    item = {
        "pk": {"S": pk(order_id)},
        "order_id": {"S": order_id},
        "status": {"S": status},
        "updated_at": {"S": datetime.utcnow().isoformat()+"Z"},
    }
    for k, v in extras.items():
        item[k] = {"S": str(v)}

    ddb.put_item(TableName=DDB_TABLE, Item=item)

def put_if_not_exists(order_id: str, status: str, **extras):
    item = {
        "pk": {"S": pk(order_id)},
        "order_id": {"S": order_id},
        "status": {"S": status},
        "updated_at": {"S": datetime.utcnow().isoformat()+"Z"},
    }
    for k, v in extras.items():
        item[k] = {"S": str(v)}

    ddb.put_item(
        TableName=DDB_TABLE,
        Item=item,
        ConditionExpression="attribute_not_exists(pk)"
    )

def lambda_handler(event, context):
    for rec in event["Records"]:
        try:
            body = json.loads(rec["body"])
            order = body["order"]
            meta = body["meta"]

            order_id = order.get("order_id", "UNKNOWN")
            ok = bool(meta.get("validation_ok", False))
            reason = meta.get("validation_reason", "unknown")

            # 1) Cas REJECTED (commande invalide)
            if not ok:
                put_status(order_id, "REJECTED", reason=reason)
                put_metric("OrdersRejected", 1)
                log("ERROR", "Order rejected (will go to DLQ after retries)", order_id=order_id, reason=reason)

                # on lève une exception pour déclencher retries -> DLQ
                raise Exception(f"Order rejected: {reason}")

            # 2) Cas PROCESSED (idempotent)
            try:
                put_if_not_exists(
                    order_id,
                    "PROCESSED",
                    amount=order.get("amount"),
                    currency=order.get("currency")
                )
                put_metric("OrdersProcessed", 1)
                log("INFO", "Order processed", order_id=order_id)

            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    # 3) Cas DUPLICATE
                    put_status(order_id, "DUPLICATE")
                    put_metric("OrdersDuplicate", 1)
                    log("WARN", "Duplicate order ignored", order_id=order_id)
                else:
                    # Erreur DynamoDB : on marque failed + on relance
                    put_metric("OrdersFailed", 1)  # optionnel
                    log("ERROR", "DynamoDB error", order_id=order_id, error=str(e))
                    raise

        except Exception as e:
            # Erreur globale message: on marque failed (optionnel) et on relance
            # NB: pour REJECTED on a déjà publié OrdersRejected, mais ce compteur peut servir aux pannes techniques
            if "Order rejected" not in str(e):
                put_metric("OrdersFailed", 1)  # optionnel
            raise

    return {"status": "OK"}
