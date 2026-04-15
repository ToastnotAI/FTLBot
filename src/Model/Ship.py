import pyautogui
import numpy as np
import pygetwindow as gw
import cv2
import time
try:
    from .Masker import Masker
except ImportError:
    from Masker import Masker



class Ship(Masker): 

    HEALTH_BAR_REGION = None # Define the region of interest (ROI) for the health bar, to be set by subclasses
    SHIELD_BAR_REGION = None # Define the region of interest (ROI) for the shield bar, to be set by subclasses
    ROOM_REGION = None # Define the region of interest (ROI) for the rooms, to be set by subclasses


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

    def detect_health(self, screenshot, DEBUG=False):
        mask = self.mask_region(screenshot, mask_function=self.health_mask, bar_region=self.HEALTH_BAR_REGION, DEBUG=DEBUG)
        if not isinstance(mask, np.ndarray):
            self.health = 0
            return 0
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

        if DEBUG:
            cv2.imwrite("debug_shield_mask.png", mask)

        # Count shield pips as connected blue blobs so x-position shifts between
        # different window scales/fixtures do not affect detection.
        binary_mask = (mask > 0).astype(np.uint8)
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary_mask, connectivity=8)

        shield = 0
        for label in range(1, num_labels):
            width = stats[label, cv2.CC_STAT_WIDTH]
            height = stats[label, cv2.CC_STAT_HEIGHT]
            area = stats[label, cv2.CC_STAT_AREA]
            box_area = max(1, width * height)
            fill_ratio = area / box_area

            # Keep dense, pip-like blobs and reject sparse ring/noise artifacts.
            if width >= 3 and height >= 3 and area >= 30 and fill_ratio >= 0.65:
                shield += 1
                
        self.shield = shield
        return shield

    def detect_rooms(self, screenshot, DEBUG=False):
        mask = self.mask_region(screenshot, mask_function=self.room_mask, bar_region=self.ROOM_REGION, DEBUG=DEBUG)
        # Bridge thin gaps caused by interior line artifacts so one room is not split into many.
        # This is not necessary on images at or below the base resolution since the rooms are already merged at that scale, but helps maintain consistency across scales and fixtures.
        if self.scale_x > 1 or self.scale_y > 1:
            close_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            room_mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel, iterations=2)
        else:
            room_mask = mask
        if DEBUG:
            cv2.imshow("debug_room_mask.png", room_mask)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

                # Locate rectangles in the mask which correspond to rooms, using contours
        contours, _ = cv2.findContours(room_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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
            
        self.rooms = rooms        
        
        return rooms
        


