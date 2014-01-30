#!/usr/bin/python

import redis
import json
import time

red = redis.StrictRedis()

red.publish("fooshack", json.dumps({"player":{"position":1,"tag":"123"}}))
red.publish("fooshack", json.dumps({"player":{"position":2,"tag":"qwe"}}))
red.publish("fooshack", json.dumps({"player":{"position":3,"tag":"asd"}}))
red.publish("fooshack", json.dumps({"player":{"position":4,"tag":"zxc"}}))
time.sleep(1)
red.publish("fooshack", json.dumps({"goal":{"team":1, "spd":1}}))
red.publish("fooshack", json.dumps({"goal":{"team":2, "spd":1}}))

