import pyautogui
import numpy as np
import pygetwindow as gw
import cv2
import time

try:
    from .Ship import Ship
    from .Systems import System, Weapon, Reactor
except ImportError:
    from Ship import Ship
    from Systems import System, Weapon, Reactor
    

class PlayerShip(Ship):
    def __init__(self):
        super().__init__()
        DEFAULT_REACTOR_POWER = 8

        self.refresh_scale_factors()
        self._health_bar_base_region = (10, 39, 360, 5)
        self._shield_bar_base_region = (30, 67, 100, 5)
        self._room_base_region = (110, 115, 740, 510)
        self.refresh_regions()

        self.systems = []

        self.weapons = []

        self.reactor = Reactor(DEFAULT_REACTOR_POWER)

    def refresh_regions(self):
        self.HEALTH_BAR_REGION = self.rescale_region(self._health_bar_base_region)
        self.SHIELD_BAR_REGION = self.rescale_region(self._shield_bar_base_region)
        self.ROOM_REGION = self.rescale_region(self._room_base_region)

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
                    # Keep return type consistent with cv2 masks to avoid scalar-shape crashes.
                    return np.zeros((health_bar_image.height, health_bar_image.width), dtype=np.uint8)
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
        # Scale system anchors from base 1280x720 using the actual screenshot size.
        screenshot_width, screenshot_height = screenshot.size
        scale_x = screenshot_width / 1280
        scale_y = screenshot_height / 720
        system_names = [
            [(380, 330), "Weapons", (235, 650)],
            [(270, 330), "Engines", (120, 650)],
            [(265, 280), "Oxygen", (200, 650)],
            [(510, 300), "Medbay", (165, 650)],
            [(700, 325), "Piloting"],
            [(510, 360), "Shields", (90, 650)],
            [(585, 345), "Sensors"],
            [(585, 310), "Doors"],
        ]
        for room in rooms:
            for system in system_names:
                system_pos = (int(system[0][0] * scale_x), int(system[0][1] * scale_y))
                system_uipos = (int(system[2][0] * scale_x), int(system[2][1] * scale_y)) if len(system) == 3 else None
                if self._point_in_room(system_pos, room):
                    print(f"System {system[1]} is in room {room}")
                    if len(system) == 3:
                        self.systems.append(System(system[1], room, 0, system_pos, system_uipos))
                    else:
                        self.systems.append(System(system[1], room, 0, system_pos))

        if DEBUG:
            # OpenCV drawing functions require a numpy image, not a PIL image.
            debug_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            # draw circles on screen for each system that is detected
            for system in self.systems:
                cv2.circle(debug_image, tuple(system.pos), 5, (0, 255, 0), -1)
                if system.uipos:
                    cv2.circle(debug_image, tuple(system.uipos), 5, (255, 0, 0), -1)
                    #draw a line between the system position and the ui position
                    cv2.line(debug_image, tuple(system.pos), tuple(system.uipos), (255, 0, 0), 1)
            cv2.imshow("Rooms with Systems", debug_image)
            cv2.waitKey(0)

        return rooms

    def detect_weapons(self, screenshot, DEBUG=False):
        # For this version all weapons will be hardcoded
        weapons = [
            Weapon("Artemis Missile", (300, 650), 2, 11, 1, 5),
            Weapon("Burst Laser Mk II", (400, 650), 1, 12, 3)
        ]
        self.weapons = weapons
        return weapons

    def detect_system_power(self, screenshot, DEBUG=False):
        for system in self.systems:
            if system.uipos:
                system.power = system.get_power(screenshot, DEBUG=DEBUG)
                print(f"{system.name} power: {system.power}")



if __name__ == "__main__":
    print(gw.getAllTitles())
    player_ship = PlayerShip()
    screenshot = player_ship.screenshot(DEBUG=True)

    
    shield = player_ship.detect_shield(screenshot, DEBUG=True)
    print(f"Shield: {shield}")
    health = player_ship.detect_health(screenshot, DEBUG=True)
    print(f"Health: {health}")
    

    rooms = player_ship.detect_rooms(screenshot,DEBUG=True)
    print(f"Rooms: {rooms}")
    #player_ship.detect_system_power(screenshot, DEBUG=True)
    #print(f"Systems: {[(system.name, system.power) for system in player_ship.systems]}")
    #player_ship.reactor.refresh_power(screenshot, DEBUG=True)
    #print(f"Reactor power: {player_ship.reactor.available_power}")