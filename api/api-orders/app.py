import os
from fastapi import FastAPI, HTTPException
import boto3
from boto3.dynamodb.types import TypeDeserializer
from fastapi.middleware.cors import CORSMiddleware

AWS_REGION = os.getenv("AWS_REGION", "eu-west-3")
TABLE_NAME = os.getenv("TABLE_NAME", "tp-orders")

ddb = boto3.client("dynamodb", region_name=AWS_REGION)
deser = TypeDeserializer()

app = FastAPI(title="Orders API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def ddb_to_py(item): 
    return {k: deser.deserialize(v) for k, v in item.items()}

def make_pk(order_id: str) -> str:
    return f"ORDER#{order_id}"

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/orders")
def list_orders(limit: int = 50):
    resp = ddb.scan(TableName=TABLE_NAME, Limit=min(max(limit, 1), 100))
    items = [ddb_to_py(i) for i in resp.get("Items", [])]
    return {"count": len(items), "items": items}

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    resp = ddb.get_item(TableName=TABLE_NAME, Key={"pk": {"S": make_pk(order_id)}})
    if "Item" not in resp:
        raise HTTPException(status_code=404, detail="order not found")
    return ddb_to_py(resp["Item"])
