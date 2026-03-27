import pyautogui
import numpy as np
import pygetwindow as gw
import cv2
import time

if __name__ != "__main__":
    from .Ship import Ship
else:
    from Ship import Ship


class PlayerShip(Ship):
    def __init__(self):
        super().__init__()
        self.HEALTH_BAR_REGION = (10, 34, 360, 5)  # Define the region of interest (ROI) for the health bar
        #ROI of shield bar is 30,50 to 130,80 with 30,50 being being top left corner and 130,80 being bottom right corner, so width is 100 and height is 30
        self.SHIELD_BAR_REGION = (30, 62, 100, 3)  # Define the region of interest (ROI) for the shield bar
        # ROI for rooms is 110, 110 to 850, 620
        self.ROOM_REGION = (110, 110, 740, 510)  # Define the region of interest (ROI) for the rooms


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
    rooms = player_ship.detect_rooms(screenshot, DEBUG=True)
    print(f"Rooms: {rooms}")
