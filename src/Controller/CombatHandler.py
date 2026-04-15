

if __name__ == "__main__":
    #change working directory to src
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
from Model.PlayerShip import PlayerShip
from Model.EnemyShip import EnemyShip
import time
import random

class CombatHandler:
    def __init__(self, player_ship, hostile_ship):
        self.player_ship = player_ship
        self.hostile_ship = hostile_ship
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

            # TODO: Send pause command to the interface
        
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

            #TODO: Send unpause command to the interface
    

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


    # Current version will not utilise any tactics, and will instead fire all available weapons
    def main_combat_loop(self):
        while True:
            self.pause()
            screenshot = self.player_ship.screenshot()
            weapons_to_fire = self.get_available_weapons()
            for weapon in weapons_to_fire:
                target = random.choice(self.hostile_ship.rooms)
                print(f"Firing {weapon.name} at {target.name}")
                weapon.fired()
                # TODO: Send fire command to the interface
            self.unpause()
            time.sleep(0.1)


    
        