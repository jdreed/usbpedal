#!/usr/bin/python

import time
import logging

logging.basicConfig(level=logging.INFO)

import pedal

p = pedal.Connection()

print p.model
p.pedals[0].set_mouse(20, 20, 2)
p.pedals[1].set_string('This is a string')
p.pedals[2].set_key('B')
#p.updateConfig()
for i,v in enumerate(p.pedals, 1):
    print "Pedal {0}: {1}".format(i, v)

