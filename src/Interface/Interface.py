import pyautogui
import pygetwindow as gw

class Interface:
    def __init__(self, ftl_window=None):
        if ftl_window is None:
            self.ftl_window = gw.getWindowsWithTitle("FTL: Faster Than Light")[0]  # Get the FTL window
        else:
            self.ftl_window = ftl_window
               
               
    def _activate_ftl_window(self):
        if self.ftl_window is None:
            return

        if hasattr(self.ftl_window, "isMinimized") and self.ftl_window.isMinimized:
            self.ftl_window.restore()

        self.ftl_window.activate()
