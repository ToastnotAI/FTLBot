import time
import cv2
import numpy as np

try:
    from .Masker import Masker
except ImportError:
    from Masker import Masker



class System(Masker):

    def __init__(self, name, shape, max_power, pos, uipos = None):
        super().__init__()
        self.name = name
        self.pos = pos
        self.uipos = uipos
        self.shape = shape
        self.damage = 0
        self.max_power = max_power
        self.power = 0

    def send_damage(self, damage):
        self.damage += damage

    def is_destroyed(self):
        return self.damage >= 3


    def power_mask(self, power_bar_image):
        # Define lower and upper bounds for green in HSV from 64ff64
        lower_green = np.array([50, 100, 100])
        upper_green = np.array([70, 255, 255])
        mask = self.mask_color(power_bar_image, lower_green, upper_green)
        return mask

    def get_power(self, screenshot, DEBUG=False):
        scale_y = screenshot.height / 720
        top = int(550 * scale_y)
        height = max(1, int(120 * scale_y))
        # uipos is already in screenshot coordinates, so do not rescale it again.
        bar_region = (int(self.uipos[0]), top, 3, height)
        mask = self.mask_region(screenshot, mask_function=self.power_mask, bar_region=bar_region, DEBUG=DEBUG)
        # count groups of green pixels
        power = 0
        state = 0
        for row in range(mask.shape[0]):
            row_has_green = np.any(mask[row, :] > 0)
            if state == 0:
                if row_has_green:
                    power += 1
                    state = 1
            else:
                if not row_has_green:
                    state = 0
        return power

    


class Weapon():
    def __init__(self, name, pos, damage, base_cooldown, power_cost, shots_per_burst = 1, shield_pen = 0, is_beam = False, is_enabled = True):
        self.name = name
        self.pos = pos
        self.damage = damage
        self.base_cooldown = base_cooldown
        self.power_cost = power_cost
        self.shots_per_burst = shots_per_burst
        self.shield_pen = shield_pen
        self.is_beam = is_beam
        self.is_enabled = is_enabled
        self.last_fired = 0

    def can_fire(self, current_time = None, cooldown_multiplier = 1):
        if current_time is None:
            current_time = time.time()
        return ((current_time - self.last_fired) >= (self.base_cooldown * cooldown_multiplier)) and self.is_enabled

    def fired(self):
        self.last_fired = time.time()
    
    def toggle_enabled(self):
        self.is_enabled = not self.is_enabled
        if self.is_enabled:
            # When enabled the weapon needs to charge before it can fire, so we set last_fired to the current time to enforce the cooldown
            self.last_fired = time.time()

    
class Reactor(Masker):

    # Power bar region from 25, 500 to 25, 700
    POWER_BAR_REGION = None
    def __init__(self, max_power):
        super().__init__()
        self.max_power = max_power
        self.available_power = max_power
        # Recompute per instance so tests with different window scales do not reuse stale ROI values.
        self.POWER_BAR_REGION = self.rescale_region((25, 500, 3, 200))

    def power_mask(self, power_bar_image):
        # Define lower and upper bounds for green in HSV
        lower_green = np.array([50, 100, 100])
        upper_green = np.array([70, 255, 255])
        mask = self.mask_color(power_bar_image, lower_green, upper_green)
        return mask

    def refresh_power(self, screenshot, DEBUG=False):
        mask = self.mask_region(screenshot, mask_function=self.power_mask, bar_region=self.POWER_BAR_REGION, DEBUG=DEBUG)
        # count groups of green pixels
        power = 0
        state = 0
        for row in range(mask.shape[0]):
            row_has_green = np.any(mask[row, :] > 0)
            if state == 0:
                if row_has_green:
                    power += 1
                    state = 1
            else:
                if not row_has_green:
                    state = 0
        self.available_power = power
