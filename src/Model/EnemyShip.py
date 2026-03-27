import pyautogui
import numpy as np
import pygetwindow as gw
import cv2
import time

if __name__ != "__main__":
    from .Ship import Ship
else:
    from Ship import Ship

class EnemyShip(Ship):
    def __init__(self):
        super().__init__()
        self.HEALTH_BAR_REGION = (890, 100, 160, 1)  # Define the region of interest (ROI) for the health bar
        self.SHIELD_BAR_REGION = (890, 130, 120, 1)  # Define the region of interest (ROI) for the shield bar
        # 890,160 to 1255, 530
        self.ROOM_REGION = (890, 160, 365, 370) # Define the region of interest (ROI) for the rooms

    def health_mask(self, health_bar_image):
        # health bar is always green for enemy ships, so we can use the same mask as player ship but only check for green pixels
        # The green in html notation is #78ff78, be strict with setting upper and lower bounds to match this colour as closely as possible to avoid detecting other green pixels in the game
        lower_green = np.array([50, 90, 180], dtype=np.uint8)
        upper_green = np.array([70, 200, 255], dtype=np.uint8)
        
        mask = self.mask_color(health_bar_image, lower_green, upper_green)

        if np.sum(mask) == 0:
            return 0  # No health detected 

        return mask

    def shield_mask(self, shield_bar_image):
        # shield mask will be same as player ship, as the colour of the shield bar is the same for both player and enemy ships
        lower_blue = np.array([100, 100, 100])
        upper_blue = np.array([130, 255, 255])

        mask = self.mask_color(shield_bar_image, lower_blue, upper_blue)

        return mask




if __name__ == "__main__":
    print(gw.getAllTitles())
    enemy_ship = EnemyShip()
    screenshot = enemy_ship.screenshot()
    rooms = enemy_ship.detect_rooms(screenshot, DEBUG=True)