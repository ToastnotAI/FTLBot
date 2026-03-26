import pyautogui
import numpy as np
import pygetwindow as gw
import cv2
import time


class Ship: 

    HEALTH_BAR_REGION = None # Define the region of interest (ROI) for the health bar, to be set by subclasses
    SHIELD_BAR_REGION = None # Define the region of interest (ROI) for the shield bar, to be set by subclasses

    def __init__(self):
        self.ftl_window = gw.getWindowsWithTitle("FTL: Faster Than Light")[0]  # Get the FTL window
        self.screen_width, self.screen_height = self.ftl_window.width, self.ftl_window.height
        self.TITLE_BAR_HEIGHT = 30  # Adjust this based on your window's title bar height

    def screenshot(self):
        self.ftl_window.activate()  # Activate the FTL window
        # Capture the window content area excluding the title bar
        time.sleep(0.5)
        screenshot = pyautogui.screenshot(region=(
            self.ftl_window.left, 
            self.ftl_window.top + self.TITLE_BAR_HEIGHT,  # Start below title bar
            self.ftl_window.width, 
            self.ftl_window.height - self.TITLE_BAR_HEIGHT  # Reduce height by title bar
        ))
        return screenshot

    def mask_color(self, image, lower_bound, upper_bound):
        # Convert PIL Image to numpy array and then to HSV
        image_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2HSV)
        # Create a mask for the specified color range
        mask = cv2.inRange(image_array, lower_bound, upper_bound)
        return mask

    def health_mask(self, mask):
        # This method should be implemented by subclasses to return a mask of the health bar based on the specific colors used in the game
        raise NotImplementedError("Subclasses must implement health_mask method")

    def shield_mask(self, mask):
        # This method should be implemented by subclasses to return a mask of the shield bar based on the specific colors used in the game
        raise NotImplementedError("Subclasses must implement shield_mask method")

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
            input("Press Enter to continue...")
        
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
                

        return shield




class PlayerShip(Ship):
    def __init__(self):
        super().__init__()
        self.HEALTH_BAR_REGION = (0, 34, 380, 5)  # Define the region of interest (ROI) for the health bar
        #ROI of shield bar is 30,50 to 130,80 with 30,50 being being top left corner and 130,80 being bottom right corner, so width is 100 and height is 30
        self.SHIELD_BAR_REGION = (30, 62, 100, 3)  # Define the region of interest (ROI) for the shield bar


    def health_mask(self, health_bar_image):
        # Define the lower and upper bounds for the green color in HSV
        lower_green = np.array([50, 100, 100])  # Adjust these values based on the actual color
        upper_green = np.array([70, 255, 255])  # Adjust these

        mask = self.mask_color(health_bar_image, lower_green, upper_green)

        # There are 3 possible colours for the health bar, all must be checked
        if np.sum(mask) == 0:
            lower_yellow = np.array([20, 100, 100])  # Adjust these values based on the actual color
            upper_yellow = np.array([30, 255, 255])  # Adjust
            mask = self.mask_color(health_bar_image, lower_yellow, upper_yellow)
            if np.sum(mask) == 0:
                lower_red = np.array([0, 100, 100])  # Adjust these values based on the actual color
                upper_red = np.array([10, 255, 255])  # Adjust these
                mask = self.mask_color(health_bar_image, lower_red, upper_red)
                if np.sum(mask) == 0:
                    return 0  # No health detected 
        return mask

    def shield_mask(self, shield_bar_image):
        # Define the lower and upper bounds for the blue color in HSV
        lower_blue = np.array([100, 100, 100]) 
        upper_blue = np.array([130, 255, 255])  

        mask = self.mask_color(shield_bar_image, lower_blue, upper_blue)

        if np.sum(mask) == 0:
            #return 0  # No shield detected 
            pass
        return mask


    




if __name__ == "__main__":
    print(gw.getAllTitles())
    player_ship = PlayerShip()
    screenshot = player_ship.screenshot()

    shield = player_ship.detect_shield(screenshot)
    print(f"Shield: {shield}")
    health = player_ship.detect_health(screenshot)
    print(f"Health: {health}")
