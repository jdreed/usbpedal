"""
The pedal uses the USB HID keyboard page (0x07).

See http://www.usb.org/developers/devclass_docs/Hut1_11.pdf
"""

import string

class ShiftMap(dict):
    """
    A bi-directional mapping between keys on a U.S keyboard 
    and their Shift-ed equivalents.
    """
    
    def __init__(self):
        super(ShiftMap, self).__init__()
        self.update(zip([c for c in string.ascii_uppercase],
                              [c for c in string.ascii_lowercase]))

        self.update(dict(zip(['!', '@', '#', '$', '%', '^', '&', '*', '(', ')'], [str(x) for x in range(1, 10) + [0]])))
        self.update(dict(zip(KeyMap.punctuation_upper, 
                                   KeyMap.punctuation)))
        # No duplicate values
        assert len(self.values()) == len(set(self.values()))
        # Keys and Values must be unique
        assert len(set(self.values()).intersection(set(self.keys()))) == 0
        self.update(dict((v,k) for k,v in self.items()))

class KeyMap(dict):
    punctuation = ('-', '=', '[', ']', '\\', '# (non-US)', ';', '\'', '`', ',', '.', '/')
    punctuation_upper = ('_', '+', '{', '}', '|', '| (Eur)', ':', '"', '~', '<', '>', '?')


    def __init__(self):
        # Internally, teh windows version examines the first key data
        # to see if it's > 0x83 or not.  If yes, it's a string.
        super(KeyMap, self).__init__()
        self.update(dict(zip([c for c in string.ascii_lowercase],
                             range(0x04, 0x1e))))
        # numbers start at 0x1e, but unlike ASCII, 0 is last, not first
        self.update(dict(zip([str(x) for x in range(1, 10) + [0]],
                             range(0x1e, 0x28))))

        # whitespace
        self.update({'\n': 0x28,
                     'Escape': 0x29,
                     'Backspace': 0x2a,
                     '\t': 0x2b,
                     ' ' : 0x2c})

        # 0x32 is "Non-US # and ~".  The key is in AT position 42,
        # which is not usually present on US keyboards.  (It is
        # an extra key, between the US quote key (" and ') and the 
        # Enter key, which is shaped differently on European keyboards.
        # However, this device maps it identical to 0x31.
        # The key in AT position 1 (where grave/tilde is on US keyboards)
        # is the "not" sign (U+00AC) on other keyboards
        self.update(dict(zip(self.punctuation,
                             [x for x in range(0x2d, 0x39)])))

        # Function keys (0x3a through 0x45 for F1-F12)
        self.update(dict([('F{0}'.format(x - 0x39),
                           x) for x in range(0x3a, 0x36)]))
        # Miscellaneous Keys
        self['CapsLock'] = 0x39
        self['NumLock'] = 0x53
        self.update(dict(zip(['PrintScreen', 'Scroll Lock', 'Pause', 'Insert',
                              'Home', 'PageUp', 'DeleteForward', 'End',
                              'PageDown', 'RightArrow', 'LeftArrow',
                              'DownArrow', 'UpArrow'],
                             range(0x46, 0x53))))
        # The numpad
        self.update(dict(zip(['KP_Divide', 'KP_Multiply', 'KP_Subtract',
                              'KP_Add', 'KP_Enter'],
                             range(0x54, 0x59))))
        self.update(dict([('KP_{0}'.format((x - 0x58) % 10),
                           x) for x in range(0x59, 0x63)]))
        self['KP_Period'] = 0x63
        # 0x64 is \ and | on non-US keyboards.  This is
        # in AT-102 position 45 (between Shift_L and 'z'), and is usually
        # where backslash lives
        self['\ (non-US)'] = 0x64
        self['Application'] = 0x65  #Compose?
        self['Power'] = 0x66
        self['KP_Equals'] = 0x67
        # More function keys
        self.update(dict([('F{0}'.format(x - 0x5b),
                           x) for x in range(0x68, 0x74)]))
        # The hilarious Sun keys
        self.update(dict(zip(['Execute', 'Help', 'Menu',
                              'Select', 'Stop', 'Again', 'Undo',
                              'Cut', 'Copy', 'Paste', 'Find'],
                             range(0x74, 0x7f))))
        self.update({'Mute': 0x7f,
                     'VolumeUp': 0x80,
                     'VolumeDown': 0x81})
        # 0x82 and 0x83 are the locking versions of CapsLock and NumLock
        # Unless you are a time-traveler, you don't have these.

        # whitespace keys
        # There is a "hole" in the 0x80 offset table here, since
        # "uppercase" versions of these are meaningless
        # Modifier keys
        # (these match the HID mapping)
        modifiers = ['Ctrl', 'Shift', 'Alt', 'Super']
        self.modifiers = dict()
        self.modifiers.update(dict(zip([x + '_L' for x in modifiers],
                             range(0xe0, 0xe4))))
        self.modifiers.update(dict(zip([x + '_R' for x in modifiers],
                             range(0xe4, 0xe9))))
         # And load the inverse mapping
        assert len(self.values()) == len(set(self.values()))
        self.update(dict((v,k) for k,v in self.items()))

        self.aliases = { 'Enter': '\n',
                         'Return': '\n',
                         'Tab': '\t',
                         'Space': ' ',
                         'Spacebar': ' ',
                         'Esc' : 'Escape' }
        self.shifted = ShiftMap()

    def string_lookup(self, key):
        if isinstance(key, int):
            if key in self:
                return self.get(key)
            if (key ^ 0x80) in self:
                return self.shifted[self.get(key ^ 0x80)]
        else:
            if key in self:
                return self.get(key)
            if self.shifted[key] in self:
                return self.get(self.shifted[key]) | 0x80
            raise KeyError("Invalid character: " + key)

    def __getitem__(self, key):
        if isinstance(key, int):
            if key in self:
                return self.get(key)
            else:
                return "<{0:#04x}>".format(key)
        else:
            if key in self:
                # basic keys
                return self.get(key)
            if key in self.aliases:
                # aliases
                return self.get(self.aliases[key])
            raise KeyError("Not a valid key: " + key)


