import pyautogui
import numpy as np
import pygetwindow as gw
import cv2
import pytesseract
import time
import os
import sys

try:
    from .Ship import Ship
    from .Masker import Masker
    from ..Interface.MouseInterface import MouseInterface
except ImportError:
    # Allow running this file directly, e.g. `python src/Model/EnemyShip.py`.
    src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from Model.Ship import Ship
    from Model.Masker import Masker
    from Interface.MouseInterface import MouseInterface

class EnemyShip(Ship):
    '''Represents the enemy ship in a combat encounter.
    arguments:
        mouse_interface: an instance of MouseInterface

    methods:
        full_scan(screenshot): performs a full scan of the enemy ship, detecting health, shield and rooms
        initialize_systems(screenshot): detects the ship's systems and their positions, to be called
            after detect_rooms since it relies on room positions for system-room linking
        update_systems(screenshot): updates the status of each system, to be called each combat turn after the initial scan
    '''
    def __init__(self, mouse_interface=None):
        super().__init__()
        self.refresh_scale_factors()
        self._health_bar_base_region = (890, 100, 160, 4)
        self._shield_bar_base_region = (890, 125, 120, 20)
        self._room_base_region = (900, 95, 365, 440)
        self.mouse_interface = mouse_interface if mouse_interface else MouseInterface()
        self.refresh_regions()
        self.systems = EnemyShipSystems(mouse_interface=self.mouse_interface)

    def refresh_regions(self):
        self.HEALTH_BAR_REGION = self.rescale_region(self._health_bar_base_region)
        self.SHIELD_BAR_REGION = self.rescale_region(self._shield_bar_base_region)
        self.ROOM_REGION = self.rescale_region(self._room_base_region)

    def full_scan(self, screenshot):
        self.detect_health(screenshot)
        self.detect_shield(screenshot)
        self.detect_rooms(screenshot)

    def initialize_systems(self, screenshot, DEBUG=False):
        self.systems.refresh_region()
        systems_image = self.mask_region(screenshot, mask_function=self.systems.mask_ui_icons, bar_region=self.systems.REGION)
        if not self.rooms:
            raise Exception("Rooms must be detected before initializing systems, as system-room linking relies on room positions. Call full_scan() first")
        self.systems.identify_system_status_and_position(screenshot, DEBUG=DEBUG)
        self.systems.identify_system_names(screenshot, DEBUG=DEBUG)
        self.systems.locate_system_rooms(self.rooms)
        
    
    def update_systems(self, screenshot):
        systems_image = self.mask_region(screenshot, mask_function=self.systems.mask_ui_icons, bar_region=self.systems.REGION)
        self.systems.identify_system_status_and_position(screenshot)

    


class EnemyShipSystems(Masker):

    '''Represents the systems of the enemy ship, which can be detected by their icons in the bottom right of the screen during combat.
    Each system has a status indicated by the colour of its icon: green, yellow or red

    attributes:
        systems: a list of dictionaries representing the detected systems, with keys "name", "position" and "status"
        mouse_interface: an instance of MouseInterface for moving the mouse to hover over system icons for OCR and room linking
    methods:
        identify_system_status_and_position(screenshot): detects the position and status of each system by colour masking their icons
        identify_system_names(screenshot): identifies the name of each system by hovering over its icon and using OCR on the resulting tooltip
        locate_system_room(system): locates which room a system is in by hovering over its icon and detecting which room highlights with a yellow border
    '''
    
    # System structure in list is {name: str, ui_position: (x,y), room_position: (x,y), status: "green"/"yellow"/"red"/"unknown"}
    _BASE_TOOLTIP_REGION = (890, 560, 370, 140) # Region to capture for OCR when hovering over system icons, relative to the bottom left of the systems region. Scaled by current scale factors.
    _BASE_REGION = (920, 520, 320, 60) # Base region of the system icons on a 1280x720 resolution, to be scaled by current scale factors.

    def __init__(self, mouse_interface=None):
        super().__init__()
        self.refresh_scale_factors()
        self.mouse_interface = mouse_interface if mouse_interface else MouseInterface()
        # top left is (920,520) and bottom right is (1260, 660) on 1280 x 720
        self.refresh_region()
        self.systems = []

    def refresh_region(self):
        self.REGION = self.rescale_region(self._BASE_REGION)
        # TOOLTIP_REGION must be absolute screen coordinates for pyautogui.screenshot
        capture_left, capture_top, _, _ = self._get_capture_geometry()
        scaled = self.rescale_region(self._BASE_TOOLTIP_REGION)
        self.TOOLTIP_REGION = (
            capture_left + scaled[0],
            capture_top + scaled[1],
            scaled[2],
            scaled[3],
        )

    def mask_ui_icons(self, image, DEBUG=False):
        # UI icons are either green, yellow or red depending on their status
        # Define the lower and upper bounds for the green color in HSV
        lower_green = np.array([50, 100, 100]) 
        upper_green = np.array([70, 255, 255])  
        # Define the lower and upper bounds for the yellow color in HSV
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([30, 255, 255])
        # Define the lower and upper bounds for the red color in HSV
        # Target: #fa5541 -> HSV(OpenCV) approx (3, 189, 250); very strict bounds
        lower_red = np.array([0, 185, 230])
        upper_red = np.array([4, 255, 255])

        self.green_mask = self.mask_color(image, lower_green, upper_green)
        self.yellow_mask = self.mask_color(image, lower_yellow, upper_yellow)
        self.red_mask = self.mask_color(image, lower_red, upper_red)

        if DEBUG:
            cv2.imwrite("DEBUG_green_mask.png", self.green_mask)
            cv2.imwrite("DEBUG_yellow_mask.png", self.yellow_mask)
            cv2.imwrite("DEBUG_red_mask.png", self.red_mask)

    def identify_system_status_and_position(self, image, DEBUG=False):
        self.mask_ui_icons(image, DEBUG=DEBUG)

        region_x, region_y, region_w, region_h = self.REGION

        # Combine all colour masks and crop to the systems region so contour
        # detection is not confused by matching colours elsewhere on screen.
        combined_mask = cv2.bitwise_or(
            self.green_mask,
            cv2.bitwise_or(self.yellow_mask, self.red_mask)
        )
        region_mask = combined_mask[region_y:region_y + region_h, region_x:region_x + region_w]
        # Erode to separate adjacent icons that bleed into each other
        kernel = np.ones((3, 3), np.uint8)
        region_mask = cv2.erode(region_mask, kernel, iterations=1)

        if DEBUG:
            cv2.imwrite("DEBUG_combined_region_mask.png", region_mask)

        contours, _ = cv2.findContours(region_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Expected icon width at current scale; blobs wider than 1.5x this are merged icons
        icon_width = max(1, int(30 * self.scale_x))
        dedupe_distance_x = max(5, int(icon_width * 0.55))
        dedupe_distance_y = max(5, int(icon_width * 1.0))

        # Decompose each contour into icon-sized sub-regions if it is too wide
        # Prevents stubbornly merged icons from being treated as one, which would cause missed detections of adjacent systems.
        icon_boxes = []
        for contour in contours:
            cx, cy, cw, ch = cv2.boundingRect(contour)
            if cw > icon_width * 1.5:
                # Split horizontally into icon_width-wide slices
                for sub_x in range(cx, cx + cw, icon_width):
                    sub_w = min(icon_width, cx + cw - sub_x)
                    icon_boxes.append((sub_x, cy, sub_w, ch))
            else:
                icon_boxes.append((cx, cy, cw, ch))

        for cx, cy, cw, ch in icon_boxes:
            # Keep icon coordinates in client-area space so they can be passed
            # directly to MouseInterface.move_to/click_at_position.
            system_center_x = region_x + cx + cw // 2
            system_center_y = region_y + cy + ch // 2

            # Determine status from which colour mask dominates inside this bounding box
            mx0 = region_x + cx
            mx1 = mx0 + cw
            my0 = region_y + cy
            my1 = my0 + ch
            green_pixels = np.sum(self.green_mask[my0:my1, mx0:mx1])
            yellow_pixels = np.sum(self.yellow_mask[my0:my1, mx0:mx1])
            red_pixels = np.sum(self.red_mask[my0:my1, mx0:mx1])

            if green_pixels > yellow_pixels and green_pixels > red_pixels:
                status = "green"
            elif yellow_pixels > green_pixels and yellow_pixels > red_pixels:
                status = "yellow"
            elif red_pixels > green_pixels and red_pixels > yellow_pixels:
                status = "red"
            else:
                status = "unknown"

            if status != "unknown":
                position = (system_center_x, system_center_y)
                matching_system = None
                for system in self.systems:
                    existing_x, existing_y = system["position"]
                    if abs(existing_x - position[0]) <= dedupe_distance_x and abs(existing_y - position[1]) <= dedupe_distance_y:
                        matching_system = system
                        break

                if matching_system is None:
                    self.systems.append({"name": None, "position": position, "status": status})
                else:
                    matching_system["status"] = status
               
    def room_highlight_mask(self, image):
        # When hovering over a system icon, the corresponding room highlights with a yellow border. This mask detects that highlight to link systems to rooms.
        lower_yellow = np.array([20, 100, 100])  # Adjust these values based on the actual color
        upper_yellow = np.array([30, 255, 255])  # Adjust these values based on the actual color
        mask = self.mask_color(image, lower_yellow, upper_yellow)
        return mask

    def locate_system_rooms(self, rooms):
        # when hovering over a system icon, the icon in its corresponding room highlights with a yellow border.
        for system in self.systems:
            self.mouse_interface.move_to(system["position"][0], system["position"][1])
            time.sleep(0.1)
            screenshot = self.screenshot()
            for room in rooms:
                room_mask = self.mask_region(screenshot, mask_function=self.room_highlight_mask, bar_region=room.bounds)
                if np.sum(room_mask) > 0:
                    system["room"] = room
                    break


    def identify_system_names(self, rooms = [], DEBUG=False):

        system_identifiers = ["shields", "weapons", "engines", "oxygen", "medbay", "cloaking", "drones", "hacking", "piloting"]

        # As text recognition is more reliable than image recognition, and each system will provide a tooltip when hovered over,
        # we can use OCR to identify which system is which by hovering over each system icon and reading the tooltip text using pytesseract.
        if self.systems == []:
            return

        for system in self.systems:
            self.mouse_interface.move_to(system["position"][0], system["position"][1])
            # from bottom left of base region, go down and right by an amount  ( on 1280x720, go from (920, 560) to (1260, 700)) scaled by current scale factors, and capture a small region there for OCR
            tooltip_screenshot = pyautogui.screenshot(region = self.TOOLTIP_REGION)
            if DEBUG:
                tooltip_screenshot.save(f"DEBUG_tooltip_{system['position'][0]}_{system['position'][1]}.png")
            tooltip_text = pytesseract.image_to_string(tooltip_screenshot)
            for identifier in system_identifiers:
                if identifier in tooltip_text.lower():
                    system["name"] = identifier
                    break  
        
        if DEBUG:
            print(self.systems)

        return self.systems

    def __iter__(self):
        return iter(self.systems)

    def __len__(self):
        return len(self.systems)

    def __repr__(self):
        return f"EnemyShipSystems(systems={self.systems})"

        




if __name__ == "__main__":
    print(gw.getAllTitles())
    enemy_ship = EnemyShip()
    screenshot = enemy_ship.screenshot(DEBUG=True)
    #rooms = enemy_ship.detect_rooms(screenshot, DEBUG=True)
    #health = enemy_ship.detect_health(screenshot, DEBUG=True)
    #print(f"Detected health: {health}")
    #shield = enemy_ship.detect_shield(screenshot)
    #print(f"Detected shield: {shield}")
    enemy_ship.full_scan(screenshot)
    enemy_ship.initialize_systems(screenshot, DEBUG=True)
    print(enemy_ship.systems)