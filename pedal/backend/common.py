"""
Constants and common functions for the backend
"""
# Output report (0x02)
REPORT_TYPE = 0x02
# There is only one report
REPORT_NUM = 0x00

# From the HID spec: "The wValue field specifies the Report Type in
# the high byte and the Report ID in the low byte. Set Report ID to 0
# (zero) if Report IDs are not used."
WVALUE = REPORT_NUM | (REPORT_TYPE << 8)

# We use interface 1
INTERFACE_NUMBER = 0x01

READ_ENDPOINT = 0x82

VENDOR_ID = 0x0c45
PRODUCT_ID = 0x7403

class BackendError(Exception):
    """Backend Error"""
    pass

def packets(data, size=8):
    """
    Break data into 'size' packets, padding the last packet
    with NULLs if necessary.
    """
    for i in xrange(0, len(data), size):
        padding = [0] * (size - len(data[i:i+size]))
        yield data[i:i+size] + padding
