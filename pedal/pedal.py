import array
import logging
import time

logger = logging.getLogger('pedal')
# Add a NullHandler() in case the caller hasn't configured logging
logger.addHandler(logging.NullHandler())

from . import keymap

try:
    from .backend import libusb1 as backend
    logger.info("Using libusb-1.0 backend")
except ImportError:
    from .backend import libusb0 as backend
    logger.info("Using libusb-0.x backend")


_backend = backend.Backend()
_keymap = keymap.KeyMap()

class InputType:
    NONE = 0x00
    KEY = 0x01
    MOUSE = 0x02
    STRING = 0x04

KEY_NO_REPEAT = 0x80

modifier_keys = {
    'Ctrl' : 0x01,
    'Shift' : 0x02,
    'Alt' : 0x04,
    # "Windows Key" or "Command Key"
    'Super' : 0x08
    }

mouse_buttons = {
    'Left': 0x01,
    'Right': 0x02,
    'Middle': 0x04
    }

class Commands:
    CLEAR = 0x80
    WRITE = 0x81
    READ = 0x82
    IDENTIFY = 0x83

class Coords:
    directions = [{True: 'Right',
                   False: 'Left'},
                  {True: 'Up',
                   False: 'Down'},
                  {True: 'Back',
                   False: 'Forward'}]

    # The scroll wheel is technically buttons 4 and 5, when you
    # move it forward and back, respectively.  

    def __init__(self, data=None, coords=None):
        self.coords = coords if coords is not None else [0,0,0]
        if data is not None:
            assert len(data) == 3
            self.coords = [(i ^ 128) - 128 for i in data]
        for x in self.coords:
            assert x in range(-128, 128)

    def to_bytes(self):
        return [(128 + i) ^ 128 for i in self.coords]

    def __str__(self):
        rv = ['{0} {1}'.format(abs(v), self.directions[i][v < 0]) 
              for (i, v) in enumerate(self.coords)]
        return ', '.join(rv)

class PedalError(Exception):
    pass

class Connection:
    def __init__(self):
        self._sendCommand(Commands.IDENTIFY)
        self.model = ''.join([chr(x) for x in _backend.read(8) + _backend.read(8)])
        self.pedals = []
        for i in (1, 2, 3):
            self._sendCommand(Commands.READ, pedal=i)
            data = _backend.read(8)
            # The first packet has a 2-byte header: size and type
            # Size is max(total number of bytes that will be sent, 8)
            size = data[0]
            bytes_read = len(data)
            while bytes_read < size:
                data += _backend.read(8)
                bytes_read += 8
            if ((size == 0) and
                (bytes_read == 8)):
                # The buffer was cleared, but not written to.
                # Fix it for when we write.
                data[0] = 8
            try:
                self.pedals.append(PedalConfig(data))
            except AssertionError:
                self.pedals.append(PedalConfig())
            
    def _sendCommand(self, command, size=0x08, pedal=0x00):
        buf = [0] * 8
        buf[0] = 0x01
        buf[1] = command
        buf[2] = size
        buf[3] = pedal
        _backend.write(buf)

    def updateConfig(self):
        self._sendCommand(Commands.CLEAR)
        time.sleep(0.2)
        for i, p in enumerate(self.pedals, start=1):
            self._sendCommand(Commands.WRITE, size=p.size, pedal=i)
            _backend.write(p.get_bytes())
            time.sleep(0.05)


class PedalConfig:
    def __init__(self, data=None):
        if data is None:
            data = array.array('B', [0] * 8)
            data[0] = 8
        self.size = data.pop(0)
        self.type = data.pop(0)
        self.bytes = data[:self.size-1]
        if not (self.type & InputType.STRING):
            assert self.size == 8, "Size must be 8 unless type is string"
            self.coords = Coords(self.bytes[3:6])

    def clear(self):
        self.size = 8
        self.type = InputType.NONE
        self.bytes = array.array('B', [0] * 6)

    def set_key(self, key, modifiers=[], repeat=True):
        assert isinstance(key, str)
        if self.type & InputType.STRING:
            self.clear()
        try:
            keyval = _keymap[key]
        except KeyError:
            keyval = _keymap[_keymap.shifted[key]]
            modifiers.append('Shift')
        self.bytes[0] = 0
        for m in modifiers:
            self.bytes[0] |= modifier_keys[m]
        self.type = InputType.KEY | (KEY_NO_REPEAT if not repeat else 0x00)
        self.bytes[1] = keyval

    def set_mouse(self, x, y, z, buttons=[]):
        # TODO: clear?
        # TODO: double-click supported or chords?
        self.type = InputType.MOUSE | 0x81
        self.size = 8
        self.bytes[2] = 0
        for m in buttons:
            self.bytes[2] |= mouse_buttons[m]
        self.coords = Coords([x, y, z])
        self.bytes[3:6] = array.array('B', self.coords.to_bytes())

    def set_string(self, string):
        if isinstance(string, unicode):
            raise ValueError("Unicode strings not supported")
        assert isinstance(string, str)
        self.type = InputType.STRING
        self.bytes = array.array('B', [_keymap.string_lookup(x) for x in string])
        self.size = len(self.bytes) + 1
        self.bytes.extend([0] * (6 - len(self.bytes)))
    def get_bytes(self):
        return [self.size, self.type] + self.bytes.tolist()

    def _formatString(self):
        # TODO: Fix this.
        # Hack for when strings are < 6 chars
        return ''.join([_keymap.string_lookup(x) for x in self.bytes if x > 0])
        
    def __str__(self):
        rv = ''
        if self.type == InputType.NONE:
            rv += "Not present"
        if self.type & InputType.KEY:
            modifiers = [x for x in modifier_keys if modifier_keys[x] & self.bytes[0]]
            rv += "Key: {0}".format('{0}{1}{2}'.format('+'.join(modifiers),
                                                       '-' if len(modifiers) else '',
                                                       _keymap[self.bytes[1]]))
        if self.type & InputType.MOUSE:
            buttons = [x for x in mouse_buttons if mouse_buttons[x] & self.bytes[2]]
            rv += " Mouse: {0}".format('{0}{1}{2}'.format('+'.join(buttons),
                                                          ' Click' if len(buttons) else '',
                                                          str(self.coords)))
        if self.type & InputType.STRING:
            rv += "String: {0}".format(self._formatString())
        return rv
        

