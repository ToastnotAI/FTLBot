from Controller.CombatHandler import CombatHandler
from Model.PlayerShip import PlayerShip
from Model.EnemyShip import EnemyShip



instance = CombatHandler(player_ship=PlayerShip(), hostile_ship=EnemyShip())

instance.main_combat_loop()