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




if __name__ == "__main__":
    print(gw.getAllTitles())
    enemy_ship = EnemyShip()
    screenshot = enemy_ship.screenshot()
    rooms = enemy_ship.detect_rooms(screenshot, DEBUG=True)