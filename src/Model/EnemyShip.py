import pyautogui
import numpy as np
import pygetwindow as gw
import cv2
import time

try:
    from .Ship import Ship
except ImportError:
    from Ship import Ship

class EnemyShip(Ship):
    def __init__(self):
        super().__init__()
        self.refresh_scale_factors()
        self._health_bar_base_region = (890, 100, 160, 4)
        self._shield_bar_base_region = (890, 125, 120, 20)
        self._room_base_region = (900, 95, 365, 440)
        self.refresh_regions()

    def refresh_regions(self):
        self.HEALTH_BAR_REGION = self.rescale_region(self._health_bar_base_region)
        self.SHIELD_BAR_REGION = self.rescale_region(self._shield_bar_base_region)
        self.ROOM_REGION = self.rescale_region(self._room_base_region)




if __name__ == "__main__":
    print(gw.getAllTitles())
    enemy_ship = EnemyShip()
    screenshot = enemy_ship.screenshot(DEBUG=True)
    #rooms = enemy_ship.detect_rooms(screenshot, DEBUG=True)
    #health = enemy_ship.detect_health(screenshot, DEBUG=True)
    #print(f"Detected health: {health}")
    shield = enemy_ship.detect_shield(screenshot, DEBUG=True)
    print(f"Detected shield: {shield}")