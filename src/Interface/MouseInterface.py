import pyautogui
import platform
import time
if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes
try:
    from .Interface import Interface
except ImportError:
    from Interface import Interface

class MouseInterface(Interface):

    def __init__(self, ftl_window=None):
        super().__init__(ftl_window)
        self.refresh_bounds()
    
    def refresh_bounds(self):
        self.screen_width, self.screen_height = self.ftl_window.width, self.ftl_window.height  
        self.left_bound = self.ftl_window.left
        self.top_bound = self.ftl_window.top
        self.right_bound = self.ftl_window.right
        self.bottom_bound = self.ftl_window.bottom

    def _get_client_origin(self):
        # Room/system coordinates are in client-area space, so clicks must be translated
        # from client origin rather than full window origin.
        if platform.system() != "Windows":
            return self.left_bound, self.top_bound

        hwnd = getattr(self.ftl_window, "_hWnd", None)
        try:
            hwnd = int(hwnd)
        except (TypeError, ValueError):
            hwnd = None

        if not hwnd or hwnd <= 0:
            return self.left_bound, self.top_bound

        user32 = ctypes.windll.user32
        if not user32.IsWindow(hwnd):
            return self.left_bound, self.top_bound

        point = wintypes.POINT(0, 0)
        if not user32.ClientToScreen(hwnd, ctypes.byref(point)):
            return self.left_bound, self.top_bound
        return point.x, point.y


    def click_at_position(self, x, y):
        self._activate_ftl_window()
        self.refresh_bounds()
        client_left, client_top = self._get_client_origin()
        click_pos = (x + client_left, y + client_top)
        if self.left_bound <= click_pos[0] <= self.right_bound and self.top_bound <= click_pos[1] <= self.bottom_bound:
            pyautogui.moveTo(click_pos)
            time.sleep(0.1)  # Small delay to ensure the mouse has moved before clicking
            pyautogui.click(*click_pos)
        else:
            raise ValueError(f"Click position ({x}, {y}) is outside the bounds of the FTL window.")

    def move_to(self, x, y):
        self._activate_ftl_window()
        self.refresh_bounds()
        client_left, client_top = self._get_client_origin()
        move_pos = (x + client_left, y + client_top)
        if self.left_bound <= move_pos[0] <= self.right_bound and self.top_bound <= move_pos[1] <= self.bottom_bound:
            pyautogui.moveTo(move_pos)
        else:
            raise ValueError(f"Move position ({x}, {y}) is outside the bounds of the FTL window.")