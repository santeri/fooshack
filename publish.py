import redis
import json
import time

red = redis.StrictRedis()

while True:
    red.publish("fooshack", json.dumps({"player":{"position":1,"tag":"123"}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"player":{"position":2,"tag":"qwe"}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"player":{"position":3,"tag":"asd"}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"player":{"position":4,"tag":"zxc"}}))
    time.sleep(5)


    red.publish("fooshack", json.dumps({"goal":{"team":1, "spd":1}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":2, "spd":2}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":1, "spd":1}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":2, "spd":2}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":1, "spd":1}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":2, "spd":2}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":1, "spd":1}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":2, "spd":2}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":1, "spd":1}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":2, "spd":2}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":1, "spd":1}}))
    time.sleep(1)
    red.publish("fooshack", json.dumps({"goal":{"team":2, "spd":2}}))
    time.sleep(1)

