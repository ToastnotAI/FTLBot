import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import time

class Masker():
    def __init__(self):
        self.ftl_window = gw.getWindowsWithTitle("FTL: Faster Than Light")[0]  # Get the FTL window
        self.screen_width, self.screen_height = self.ftl_window.width, self.ftl_window.height
        self.TITLE_BAR_HEIGHT = 30  # Adjust this based on your window's title bar height
        self.WINDOW_LEFT_BORDER = 8  # Crop out to the left as needed

    def screenshot(self, DEBUG=False):
        # Refresh geometry in case the window moved/resized since construction.
        if hasattr(self.ftl_window, "isMinimized") and self.ftl_window.isMinimized:
            self.ftl_window.restore()

        self.ftl_window.activate()  # Activate the FTL window
        time.sleep(0.5)

        if self.ftl_window.width <= 0 or self.ftl_window.height <= 0:
            raise ValueError(
                "Invalid screenshot region computed for FTL window. "
                f"Window geometry: left={self.ftl_window.left}, top={self.ftl_window.top}, "
                f"width={self.ftl_window.width}, height={self.ftl_window.height}. "
                f"Borders: left_border={self.WINDOW_LEFT_BORDER}, title_bar={self.TITLE_BAR_HEIGHT}."
            )

        # Clamp crop constants so they cannot create negative/zero capture dimensions.
        effective_left_border = min(self.WINDOW_LEFT_BORDER, max(0, (self.ftl_window.width - 1) // 2))
        effective_title_bar = min(self.TITLE_BAR_HEIGHT, max(0, self.ftl_window.height - 1))

        left = self.ftl_window.left + effective_left_border
        top = self.ftl_window.top + effective_title_bar
        width = self.ftl_window.width - (2 * effective_left_border)
        height = self.ftl_window.height - effective_title_bar

        screenshot = pyautogui.screenshot(region=(left, top, width, height))
        if DEBUG:
            screenshot.save("debug_screenshot.png")
        return screenshot

    def mask_color(self, image, lower_bound, upper_bound):
        # Convert PIL Image to numpy array and then to HSV
        image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2HSV)
        # Create a mask for the specified color range
        mask = cv2.inRange(image_array, lower_bound, upper_bound)
        return mask

    def room_mask(self, enemy_ship_image, DEBUG=False):
        # Ship interiors can be white/black/grey depending on vision and lighting.
        # Keep these ranges very tight around exact target colours from comments.
        # White: #e6e2db -> HSV [19, 12, 230]
        lower_white = np.array([18, 9, 227])
        upper_white = np.array([20, 15, 233])
        mask_white = self.mask_color(enemy_ship_image, lower_white, upper_white)

        
        # Black: #373737 -> HSV [0, 0, 55]
        lower_black = np.array([0, 0, 52])
        upper_black = np.array([2, 3, 58])
        mask_black = self.mask_color(enemy_ship_image, lower_black, upper_black)

        # Grey: #aca9a4 -> HSV [19, 12, 172]
        lower_grey = np.array([18, 9, 169])
        upper_grey = np.array([20, 15, 175])
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