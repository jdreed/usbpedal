import array
import logging

import usb

from .common import *

logger = logging.getLogger('pedal.backend')

class Backend():
    def __init__(self):
        self.dh = None
        footswitch = None
        self.iface = None
        self.location = None
        for bus in usb.busses():
            for dev in bus.devices:
                if dev.idVendor == VENDOR_ID and dev.idProduct == PRODUCT_ID:
                    footswitch = dev
                    self.location = (bus.dirname, dev.filename)
                    break
        if footswitch is None:
            raise BackendError("Device not found")
        for intf in footswitch.configurations[0].interfaces:
            if intf[0].interfaceNumber == INTERFACE_NUMBER:
                self.iface = intf
        self.dh = footswitch.open()
        # TODO: flaky after an ACPI suspend
        self.dh.reset()
        # This sometimes fails, and then errno doesn't get reset
        # so subsequent errors are still populated with this.
        try:
            self.dh.detachKernelDriver(self.iface[0])
        except usb.USBError as e:
            if 'Operation not permitted' in e.message:
                raise BackendError("Permission denied while removing kernel driver")
        self.dh.claimInterface(self.iface[0])

    def write(self, data):
        rv = 0
        for packet in packets(data):
            logger.debug("Sending %s", packet)
            rv += self.dh.controlMsg(requestType=usb.TYPE_CLASS | \
                                         usb.RECIP_INTERFACE | \
                                         usb.ENDPOINT_OUT,
                                     request=usb.REQ_SET_CONFIGURATION,
                                     buffer=packet,
                                     value=WVALUE,
                                     index=INTERFACE_NUMBER)
        return rv

    def read(self, length):
        logger.debug("Reading %d bytes", length)
        try:
            rv = self.dh.interruptRead(READ_ENDPOINT, length, 500)
            logger.debug("Received bytes: %s", rv)
            return array.array('B', rv)
        except usb.USBError as e:
            raise BackendError(e)

    def __del__(self):
        if self.dh is not None:
            logger.debug("Releasing interface")
            try:
                self.dh.releaseInterface()
            except usb.USBError:
                pass
