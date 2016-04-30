# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


from ctypes import wintypes, windll, byref


class GlobalHotKeys():
    """
    Register a key using the register() method, or using the @register decorator
    Use listen() to start the message pump
    """

    key_mapping = []
    user32 = windll.user32

    WM_HOTKEY = 0x0312

    kmap = {
                '': 0,
                'ALT': 0x0001,
                'CTRL': 0x0002,
                'CONTROL': 0x0002,
                'SHIFT': 0x0004,
                'WIN': 0x0008,
                'NUMLOCK': 0x90,
                'F2': 0x71,
                'F3': 0x72,
                'F4': 0x73,
                'F5': 0x74,
                'F6': 0x75,
                'F7': 0x76,
                'F8': 0x77,
                'F9': 0x78,
                'F10': 0x79,
                'F11': 0x7A,
                'F12': 0x7B,
            }


    # for full list of VKs see: http://msdn.microsoft.com/en-us/library/dd375731
    # for list of MODs modifiers and WM_HOTKEY: http://msdn.microsoft.com/en-us/library/windows/desktop/ms646279

    @classmethod
    def register(cls, vk, modifier=0, func=None):
        """
        VK is a windows virtual key code:
         - can use ord('X') for A-Z, and 0-1 (note uppercase letter only)
         - or VK_* constants
        modifier is a MOD_* constant
        func is the function to run.  If False then break out of the message loop
        """

        # Called as a decorator?
        if func is None:
            def register_decorator(f):
                cls.register(vk, modifier, f)
                return f
            return register_decorator
        else:
            cls.key_mapping.append((vk, modifier, func))


    @classmethod
    def listen(cls):

        for index, (vk, modifiers, func) in enumerate(cls.key_mapping):
            if not cls.user32.RegisterHotKey(None, index, modifiers, vk):
                raise KeyError

        try:
            msg = wintypes.MSG()
            while cls.user32.GetMessageA(byref(msg), None, 0, 0) != 0:
                if msg.message == cls.WM_HOTKEY:
                    (vk, modifiers, func) = cls.key_mapping[msg.wParam]
                    if not func:
                        break
                    func()

                cls.user32.TranslateMessage(byref(msg))
                cls.user32.DispatchMessageA(byref(msg))

        finally:
            for index, (vk, modifiers, func) in enumerate(cls.key_mapping):
                cls.key_mapping.clear()
                cls.user32.UnregisterHotKey(None, index)


    @classmethod
    def unreg(cls):
        for index, (vk, modifiers, func) in enumerate(cls.key_mapping):
            cls.key_mapping.clear()
            cls.user32.UnregisterHotKey(None, index)
