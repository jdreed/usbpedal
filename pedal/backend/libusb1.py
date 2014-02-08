#!/usr/bin/python

import logging

import usb.core
import usb.util

from .common import *

logger = logging.getLogger('pedal.backend')

class Backend():
    def __init__(self):
        self._iface = None
        self._endpoint = None
        logger.debug('Searching for device')
        self._dev = usb.core.find(idVendor=VENDOR_ID,
                                  idProduct=PRODUCT_ID)
        if self._dev is None:
            raise BackendError("Device not found")
        
        try:
            if self._dev.is_kernel_driver_active(INTERFACE_NUMBER):
                logger.debug('Attempting to detach kernel driver')
                self._dev.detach_kernel_driver(INTERFACE_NUMBER)
        except usb.core.USBError as e:
            raise BackendError("Could not detach kernel driver: " + str(e))
        # That is all the setup that is needed.  PyUSB 1.x will take care of
        # claiming interfaces, etc.
            

    def write(self, data):
        rv = 0
        for packet in packets(data):
            logger.debug("Sending %s", packet)
            rv += self._dev.ctrl_transfer(usb.TYPE_CLASS | \
                                              usb.RECIP_INTERFACE | \
                                              usb.ENDPOINT_OUT,
                                          usb.REQ_SET_CONFIGURATION,
                                          wValue=WVALUE,
                                          wIndex=INTERFACE_NUMBER,
                                          data_or_wLength=packet)
        return rv
        

    def read(self, length):
        logger.debug("Reading %d bytes", length)
        return self._dev.read(READ_ENDPOINT, length, INTERFACE_NUMBER)
