#!/usr/bin/python
import redis

red = redis.StrictRedis()
sub = red.pubsub()
sub.subscribe('fooshack')

for m in sub.listen():
	print m


