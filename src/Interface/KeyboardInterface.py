#import a library that can mimic keyboard input
import ctypes
import pyautogui

try:
    from .Interface import Interface
except ImportError:
    from Interface import Interface


class KeyboardInterface(Interface):
    
    
    # Immediately exit the program when called, used for emergency stopping of the bot if something goes wrong.
    def kill_switch(self):
        raise SystemExit("Kill switch activated")
    
    def is_kill_switch_pressed(self):
        # On Windows, query asynchronous key state to detect if ESC is held.
        try:
            VK_ESCAPE = 0x1B
            return bool(ctypes.windll.user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000)
        except Exception:
            return False

    def press(self, key):
        self._activate_ftl_window()
        pyautogui.press(key)



    def press_key(self, key):
        self.press(key)
    
    def hold_key(self, key, duration):
        self._activate_ftl_window()
        pyautogui.keyDown(key)
        pyautogui.sleep(duration)
        pyautogui.keyUp(key)

    def pause_input(self):
        pyautogui.press("space")

