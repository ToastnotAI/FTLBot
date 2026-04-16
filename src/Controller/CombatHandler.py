
if __name__ == "__main__":
    #change working directory to src
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
from Interface.KeyboardInterface import KeyboardInterface
from Interface.MouseInterface import MouseInterface
from Model.PlayerShip import PlayerShip
from Model.EnemyShip import EnemyShip
import time
import random

class CombatHandler:
    def __init__(self, player_ship, hostile_ship, keyboard_interface=None, mouse_interface=None):
        self.player_ship = player_ship
        self.hostile_ship = hostile_ship
        self.keyboard_interface = keyboard_interface or KeyboardInterface()
        self.mouse_interface = mouse_interface or MouseInterface()
        self.is_paused = True # Assume combat starts paused
        self.player_ship.full_scan(self.player_ship.screenshot())
        self.hostile_ship.full_scan(self.hostile_ship.screenshot())    
        self.last_pause = time.time()
        self.paused_duration = 0
    
    def pause(self):
        if not self.is_paused:
            self.is_paused = True
            self.last_pause = time.time()
            self.paused_duration = 0
            self.keyboard_interface.pause_input()
            
    # After game is unpaused, cooldown timers need to be adjusted as time does not pass when paused    
    def _set_cooldowns(self):
        for weapon in self.player_ship.weapons:
            weapon.last_fired += self.paused_duration
        
    
    def unpause(self):
        if self.is_paused:
            self.is_paused = False
            self.paused_duration += time.time() - self.last_pause
            self.last_pause = 0
            self._set_cooldowns()
            self.keyboard_interface.pause_input()
    

    def check_player_status(self, screenshot):
        health = self.player_ship.detect_health(screenshot)
        shield = self.player_ship.detect_shield(screenshot)
        return health, shield
    
    def check_hostile_status(self, screenshot):
        health = self.hostile_ship.detect_health(screenshot)
        shield = self.hostile_ship.detect_shield(screenshot)
        return health, shield
    
    def get_available_weapons(self):
        available_weapons = []
        if self.is_paused:
            current_time = self.last_pause
        else:
            current_time = time.time()
        for weapon in self.player_ship.weapons:
            if weapon.can_fire(current_time=current_time):
                available_weapons.append(weapon)
        return available_weapons


    def fire_weapon(self, weapon, target):
        print(f"Firing {weapon.name} at {target}")
        weapon.fired()
        self.mouse_interface.click_at_position(weapon.pos[0], weapon.pos[1])
        self.mouse_interface.click_at_position(target.pos[0], target.pos[1])


    # Current version will not utilise any tactics, and will instead fire all available weapons
    def main_combat_loop(self):
        while True:
            # Detect keypress of escape key to break loop and end combat
            if self.keyboard_interface.is_kill_switch_pressed():
                self.keyboard_interface.kill_switch()
            screenshot = self.player_ship.screenshot()
            weapons_to_fire = self.get_available_weapons()
            if len(weapons_to_fire) > 0:
                self.pause()
                for weapon in weapons_to_fire:
                    self.fire_weapon(weapon, random.choice(self.hostile_ship.rooms))
                self.unpause()
            time.sleep(0.5)


    
        