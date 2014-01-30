#!/usr/bin/python

import redis
import json
import time

red = redis.StrictRedis()

red.publish("fooshack", json.dumps({"goal":{"team":2, "spd":1}}))

