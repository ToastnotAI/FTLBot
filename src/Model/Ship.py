import pyautogui
import numpy as np
import pygetwindow as gw
import cv2
import time


class Ship: 

    HEALTH_BAR_REGION = None # Define the region of interest (ROI) for the health bar, to be set by subclasses
    SHIELD_BAR_REGION = None # Define the region of interest (ROI) for the shield bar, to be set by subclasses
    ROOM_REGION = None # Define the region of interest (ROI) for the rooms, to be set by subclasses

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

    def health_mask(self, health_bar_image):
        # Define the lower and upper bounds for the green color in HSV
        lower_green = np.array([50, 100, 100]) 
        upper_green = np.array([70, 255, 255])  

        mask = self.mask_color(health_bar_image, lower_green, upper_green)

        return mask

    def shield_mask(self, shield_bar_image):
        # shield mask will be same as player ship, as the colour of the shield bar is the same for both player and enemy ships
        lower_blue = np.array([100, 100, 100])
        upper_blue = np.array([130, 255, 255])

        mask = self.mask_color(shield_bar_image, lower_blue, upper_blue)

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
        if DEBUG:
            bar_image.save("debug_bar_image.png")
            print(f"Bar region: {bar_region}")
            time.sleep(1)  # Pause to allow time to check the saved image
        
        mask = mask_function(bar_image)
        if DEBUG:
            cv2.imwrite("debug_mask.png", mask)
            cv2.imshow("Mask", mask)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


        return mask

    def detect_health(self, screenshot, DEBUG=False):
        mask = self.mask_region(screenshot, mask_function=self.health_mask, bar_region=self.HEALTH_BAR_REGION, DEBUG=DEBUG)
        similar_pixels = np.where(mask > 0)
        # return the number of pixel groups separated by gaps of one or more pixels horizontally, which corresponds to the number of hit points
        health = 0
        state = 0
        # Since we have a 1-pixel high strip, iterate through the columns
        for col in range(mask.shape[1]):
            if state == 0:
                if mask[0, col] > 0:  # Found green pixel
                    health += 1
                    state = 1
            else:
                if mask[0, col] == 0:  # Found non-green pixel after green
                    state = 0

        self.health = health
        return health

    def detect_shield(self, screenshot, DEBUG=False):
        mask = self.mask_region(screenshot, mask_function=self.shield_mask, bar_region=self.SHIELD_BAR_REGION, DEBUG=DEBUG)
        # save debug image of the shield mask
        if DEBUG:
            cv2.imwrite("debug_shield_mask.png", mask)

        shield = 0
        state = 0
        for col in range(mask.shape[1]):
            if state == 0:
                if mask[0, col] > 0:  # Found blue pixel
                    first_blue_col = col
                    state = 1
            elif state == 1:
                if mask[0, col] == 0:  # Found non-blue pixel after blue
                    if col - first_blue_col > 8:  # If the gap is more than 3 pixels, we consider it a new shield point
                        shield += 1
                        state = 0
                    else:
                        state = 0
                
        self.shield = shield
        return shield

    def detect_rooms(self, screenshot, DEBUG=False):
        mask = self.mask_region(screenshot, mask_function=self.room_mask, bar_region=self.ROOM_REGION, DEBUG=DEBUG)
        if DEBUG:
            cv2.imshow("debug_room_mask.png", mask)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

                # Locate rectangles in the mask which correspond to rooms, using contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rooms = []
        if DEBUG:
            debug_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Adjust coordinates to be relative to the full screenshot instead of the cropped region
            x += self.ROOM_REGION[0]
            y += self.ROOM_REGION[1]
            if w > 20 and h > 20:  # These thresholds may need to be adjusted based on the actual sizes of rooms in the game
                rooms.append((x, y, w, h))
                if DEBUG:
                    cv2.rectangle(debug_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        if DEBUG:
            cv2.imshow("debug_rooms", debug_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
                
        
        return rooms
        


