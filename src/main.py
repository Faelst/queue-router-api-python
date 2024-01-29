import redis
import json
from flask import Flask, request, jsonify
from pymongo import MongoClient, DESCENDING

app = Flask(__name__)

redisClient = redis.StrictRedis(host="localhost", port=6379, db=0)

mongo_uri = "mongodb://root:example@localhost:27017/admin"
client = MongoClient(mongo_uri)
db = client.admin
collection = db.vendors

vendors_queue = []
VENDORS_QUEUE_KEY = "vendors_queue"
LOCK_VENDOR_SELECT = "lock-vendor-select"


def buildVendorsQueue():
    vendors = collection.find().sort("weight", DESCENDING)

    vendors_queue = [
        {
            "name": vendor["name"],
            "weight": vendor["weight"],
            "currentWeight": vendor["weight"],
        }
        for vendor in list(vendors)
    ]

    redisClient.set(VENDORS_QUEUE_KEY, json.dumps(vendors_queue))

    return vendors_queue


def getResponsible():
    cacheSting = redisClient.get(VENDORS_QUEUE_KEY)
    queue = json.loads(cacheSting)
    
    if len(queue) <= 0:
        queue = buildVendorsQueue()
        
    vendorSelect = queue[0]

    if vendorSelect["currentWeight"] <= 1:
        queue.remove(vendorSelect)
    else:
        for index, vendor in enumerate(queue):
            if vendor['name'] == vendorSelect['name']:
                queue[index]['currentWeight'] = vendorSelect['currentWeight'] - 1
                
    redisClient.set(VENDORS_QUEUE_KEY, json.dumps(queue))

    return {"vendorSelect": vendorSelect, "queue": queue}
                


@app.route("/vendor", methods=["GET"])
def getVendor():
    vendor = getResponsible()
    return jsonify(vendor)


if __name__ == "__main__":
    buildVendorsQueue()
    app.run(debug=True)
