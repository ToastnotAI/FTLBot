import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import time
import platform

if platform.system() == "Windows":
    import ctypes
    from ctypes import wintypes

class Masker():
    def __init__(self):
        self.ftl_window = gw.getWindowsWithTitle("FTL: Faster Than Light")[0]  # Get the FTL window
        self.screen_width, self.screen_height = self.ftl_window.width, self.ftl_window.height
        # Default desktop-window chrome crop for FTL window captures.
        self.TITLE_BAR_HEIGHT = 30
        self.WINDOW_TOP_OFFSET = 0
        self.WINDOW_LEFT_BORDER = 8  # Crop out to the left as needed
        self._detect_window_chrome_offsets()
        self.refresh_scale_factors()

    def _get_capture_geometry(self):
        # Compute the same effective capture region used by screenshot().
        effective_left_border = min(self.WINDOW_LEFT_BORDER, max(0, (self.screen_width - 1) // 2))
        top_offset = self.TITLE_BAR_HEIGHT + self.WINDOW_TOP_OFFSET
        effective_title_bar = max(0, min(top_offset, max(0, self.screen_height - 1)))

        left = self.ftl_window.left + effective_left_border
        top = self.ftl_window.top + effective_title_bar
        width = self.screen_width - (2 * effective_left_border)
        height = self.screen_height - effective_title_bar
        return left, top, width, height

    def _detect_window_chrome_offsets(self):
        if platform.system() != "Windows":
            return

        hwnd = getattr(self.ftl_window, "_hWnd", None)
        if hwnd is None:
            # In tests, mocked window objects often have no native handle.
            # Assume screenshots are already client-area aligned.
            self.WINDOW_LEFT_BORDER = 0
            self.TITLE_BAR_HEIGHT = 0
            return

        # Unit tests often mock window objects and _hWnd is not a real native handle.
        try:
            hwnd = int(hwnd)
        except (TypeError, ValueError):
            self.WINDOW_LEFT_BORDER = 0
            self.TITLE_BAR_HEIGHT = 0
            return

        if hwnd <= 0:
            self.WINDOW_LEFT_BORDER = 0
            self.TITLE_BAR_HEIGHT = 0
            return

        user32 = ctypes.windll.user32

        if not user32.IsWindow(hwnd):
            self.WINDOW_LEFT_BORDER = 0
            self.TITLE_BAR_HEIGHT = 0
            return

        # Measure chrome thickness by comparing full window rect and client rect in screen coordinates.
        win_rect = wintypes.RECT()
        client_rect = wintypes.RECT()
        client_origin = wintypes.POINT(0, 0)
        if not user32.GetWindowRect(hwnd, ctypes.byref(win_rect)):
            return
        if not user32.GetClientRect(hwnd, ctypes.byref(client_rect)):
            return
        if not user32.ClientToScreen(hwnd, ctypes.byref(client_origin)):
            return

        left_border = client_origin.x - win_rect.left
        title_bar_height = client_origin.y - win_rect.top

        # Keep previously configured defaults if API returns unexpected values.
        if left_border >= 0:
            self.WINDOW_LEFT_BORDER = int(left_border)
        if title_bar_height >= 0:
            self.TITLE_BAR_HEIGHT = int(title_bar_height)

    def refresh_scale_factors(self):
        # Calculate scale factors from the effective capture area (client content), not full window chrome.
        base_width, base_height = 1280, 720
        _, _, capture_width, capture_height = self._get_capture_geometry()
        capture_width = max(1, capture_width)
        capture_height = max(1, capture_height)
        self.scale_x = capture_width / base_width
        self.scale_y = capture_height / base_height
    
    def _rescale_screenshot(self, screenshot):
        # Resize screenshot to base resolution for consistent masking
        return screenshot.resize((1280, 720))

    def rescale_region(self, region):
        # Rescale a region defined as (left, top, width, height) according to the current scale factors
        left, top, width, height = region
        rescaled_left = int(left * self.scale_x)
        rescaled_top = int(top * self.scale_y)
        # Keep ROI dimensions non-zero after downscaling so crop/mask operations remain valid.
        rescaled_width = max(1, int(width * self.scale_x))
        rescaled_height = max(1, int(height * self.scale_y))
        return (rescaled_left, rescaled_top, rescaled_width, rescaled_height)
    
    def rescale_point(self, point):
        # Rescale a point defined as (x, y) according to the current scale factors
        x, y = point
        self.refresh_scale_factors()  # Ensure scale factors are up to date before rescaling
        rescaled_x = int(x * self.scale_x)
        rescaled_y = int(y * self.scale_y)
        return (rescaled_x, rescaled_y)

    def screenshot(self, DEBUG=False):
        # Refresh geometry in case the window moved/resized since construction.
        if hasattr(self.ftl_window, "isMinimized") and self.ftl_window.isMinimized:
            self.ftl_window.restore()

        self.ftl_window.activate()  # Activate the FTL window
        time.sleep(0.5)

        self.screen_width, self.screen_height = self.ftl_window.width, self.ftl_window.height
        self.refresh_scale_factors()
        if hasattr(self, "refresh_regions"):
            self.refresh_regions()

        if self.ftl_window.width <= 0 or self.ftl_window.height <= 0:
            raise ValueError(
                "Invalid screenshot region computed for FTL window. "
                f"Window geometry: left={self.ftl_window.left}, top={self.ftl_window.top}, "
                f"width={self.ftl_window.width}, height={self.ftl_window.height}. "
                f"Borders: left_border={self.WINDOW_LEFT_BORDER}, title_bar={self.TITLE_BAR_HEIGHT}."
            )

        left, top, width, height = self._get_capture_geometry()

        if width <= 0 or height <= 0:
            raise ValueError(
                "Invalid screenshot capture area. "
                f"Computed capture geometry: left={left}, top={top}, width={width}, height={height}."
            )

        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        #resize screenshot to base resolution for consistent masking
        #screenshot = self._rescale_screenshot(screenshot)
        
        if DEBUG:
            screenshot.save("debug_screenshot.png")
        return screenshot

    def mask_color(self, image, lower_bound, upper_bound):
        # Convert PIL Image to numpy array and then to HSV
        image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2HSV)
        # Create a mask for the specified color range
        mask = cv2.inRange(image_array, lower_bound, upper_bound)
        return mask


    # TODO: Factor rooms with lower oxygen values going red
    
    def room_mask(self, enemy_ship_image, DEBUG=False):
        # Ship interiors can be white/black/grey depending on vision and lighting.
        # White: #e6e2db -> HSV [19, 12, 230]
        lower_white = np.array([18, 9, 227])
        upper_white = np.array([20, 15, 233])
        mask_white = self.mask_color(enemy_ship_image, lower_white, upper_white)

        
        # Black: #373737 -> HSV [0, 0, 55]
        lower_black = np.array([0, 0, 52])
        upper_black = np.array([2, 3, 58])
        mask_black = self.mask_color(enemy_ship_image, lower_black, upper_black)

        # Grey: #aca9a4 -> HSV [19, 12, 172]
        lower_grey = np.array([17, 8, 152])
        upper_grey = np.array([21, 17, 197])
        mask_grey = self.mask_color(enemy_ship_image, lower_grey, upper_grey)

        mask = cv2.bitwise_or(mask_white, mask_black)
        mask = cv2.bitwise_or(mask, mask_grey)

        if DEBUG:
            cv2.imwrite("debug_room_mask.png", mask)
        
        return mask


    def mask_region(self, screenshot, mask_function = None, bar_region=None, DEBUG=False):
        if mask_function is None:
            raise ValueError("mask_function must be provided")
        if bar_region is None:
            raise ValueError("bar_region must be provided")

        # bar_region is (left, top, width, height), convert to (left, top, right, bottom) for PIL
        left, top, width, height = bar_region
        bar_image = screenshot.crop((left, top, left + width, top + height))
        
        mask = mask_function(bar_image)
        if DEBUG:
            cv2.imwrite("debug_mask.png", mask)
            cv2.imshow("Mask", mask)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

        return mask