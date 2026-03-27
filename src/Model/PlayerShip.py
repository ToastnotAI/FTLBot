import pyautogui
import numpy as np
import pygetwindow as gw
import cv2
import time

if __name__ != "__main__":
    from .Ship import Ship
else:
    from Ship import Ship


class System():

    def __init__(self, name):
        self.name = name
        self.pos = [0, 0]
        self.shape = None
        self.damage = 0

    def send_damage(self, damage):
        self.damage += damage

    def is_destroyed(self):
        return self.damage >= 3


class Weapon():
    def __init__(self, name, pos, damage, base_cooldown, shots_per_burst = 1, shield_pen = 0, is_beam = False, is_enabled = True):
        self.name = name
        self.pos = pos
        self.damage = damage
        self.base_cooldown = base_cooldown
        self.shots_per_burst = shots_per_burst
        self.shield_pen = shield_pen
        self.is_beam = is_beam
        self.is_enabled = is_enabled
        self.last_fired = 0

    def can_fire(self, cooldown_multiplier = 1):
        current_time = time.time()
        return ((current_time - self.last_fired) >= (self.base_cooldown * cooldown_multiplier)) and self.is_enabled

    def fired(self):
        self.last_fired = time.time()
    
    def toggle_enabled(self):
        self.is_enabled = not self.is_enabled
        if self.is_enabled:
            # When enabled the weapon needs to charge before it can fire, so we set last_fired to the current time to enforce the cooldown
            self.last_fired = time.time()

    
    
    

class PlayerShip(Ship):
    def __init__(self):
        super().__init__()
        self.HEALTH_BAR_REGION = (10, 34, 360, 5)  # Define the region of interest (ROI) for the health bar
        #ROI of shield bar is 30,50 to 130,80 with 30,50 being being top left corner and 130,80 being bottom right corner, so width is 100 and height is 30
        self.SHIELD_BAR_REGION = (30, 62, 100, 3)  # Define the region of interest (ROI) for the shield bar
        # ROI for rooms is 110, 110 to 850, 620
        self.ROOM_REGION = (110, 110, 740, 510)  # Define the region of interest (ROI) for the rooms

        self.systems = []

        self.weapons = []

    def health_mask(self, health_bar_image):

        mask = super().health_mask(health_bar_image)

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

    def _point_in_room(self, point, polygon):
        x1, y1 = point
        x2, y2, xoffset, yoffset = polygon

        if (x1 >= x2 and x1 <= x2 + xoffset) and (y1 >= y2 and y1 <= y2 + yoffset):
            return True
        else:
            return False

    def detect_rooms(self, screenshot, DEBUG=False):
        rooms = super().detect_rooms(screenshot, DEBUG)
        print("Rooms:", rooms)
        system_names = [[[380,350],"Weapons"], [[270,350],"Engines"], [[265,300],"Oxygen"], [[510,320],"Medbay"], [[700,345],"Piloting"], [[510,380],"Shields"], [[585,365],"Sensors"], [[585,330],"Doors"]]
        for room in rooms:
            for system in system_names:

                if self._point_in_room(system[0], room):
                    print(f"System {system[1]} is in room {room}")
                    self.systems.append(System(system[1]))
                    self.systems[-1].pos = system[0]
                    self.systems[-1].shape = room

        if DEBUG:
            # OpenCV drawing functions require a numpy image, not a PIL image.
            debug_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            # draw circles on screen for each system that is detected
            for system in self.systems:
                cv2.circle(debug_image, tuple(system.pos), 5, (0, 255, 0), -1)
            cv2.imshow("Rooms with Systems", debug_image)
            cv2.waitKey(0)

        return rooms

    def detect_weapons(self, screenshot, DEBUG=False):
        # For this version all weapons will be hardcoded
        weapons = [
            Weapon("Artemis Missile", [300,650], 2, 11, 1, 5),
            Weapon("Burst Laser Mk II", [400,650], 1, 12, 3)
        ]
        self.weapons = weapons
        return weapons




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
