import pyautogui
import numpy as np
import pygetwindow as gw
import cv2
import time


class PlayerShip:
    def __init__(self):
        self.ftl_window = gw.getWindowsWithTitle("FTL: Faster Than Light")[0]  # Get the FTL window
        self.screen_width, self.screen_height = self.ftl_window.width, self.ftl_window.height
        self.TITLE_BAR_HEIGHT = 30  # Adjust this based on your window's title bar height
        self.HEALTH_BAR_REGION = (0, 34, 380, 5)  # Define the region of interest (ROI) for the health bar

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
        

    def detect_health(self, screenshot):
        # Define the region of interest (ROI) for the health bar
        # Assuming 1280 x 720 resolution, the health bar is located at the top left corner from 0,0 to 380, 50
        health_bar_region = self.HEALTH_BAR_REGION
        

        # Crop the screenshot to the health bar region
        # health_bar_region is (left, top, width, height), convert to (left, top, right, bottom) for PIL
        left, top, width, height = health_bar_region
        health_bar_image = screenshot.crop((left, top, left + width, top + height))
        
        # Debug: Save cropped health bar
        health_bar_image.save('health_bar_cropped_debug.png')
        
        # Convert PIL Image to numpy array and then to HSV
        health_bar_array = cv2.cvtColor(np.array(health_bar_image), cv2.COLOR_RGB2HSV)

        
        # Define lower and upper bounds for green colors in HSV
        lower_green = np.array([50, 100, 100])
        upper_green = np.array([80, 255, 255])

        # Create a mask for similar colors
        mask = cv2.inRange(health_bar_array, lower_green, upper_green)
        
        # Debug: Save mask to file
        cv2.imwrite('health_bar_mask_debug.png', mask)

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

if __name__ == "__main__":
    print(gw.getAllTitles())
    player_ship = PlayerShip()
    screenshot = player_ship.screenshot()
    health = player_ship.detect_health(screenshot)
    print(f"Player health: {health} hit points")