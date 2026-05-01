import unittest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from Controller.CombatHandler import CombatHandler


class StubWeapon:
    def __init__(self, name, can_fire_response, last_fired=0.0):
        self.name = name
        self.last_fired = last_fired
        self._can_fire_response = can_fire_response
        self.can_fire_calls = []

    def can_fire(self, current_time):
        self.can_fire_calls.append(current_time)
        return self._can_fire_response


class TestCombatHandler(unittest.TestCase):
    def setUp(self):
        self._get_windows_patcher = patch('Interface.Interface.gw.getWindowsWithTitle')
        self.mock_get_windows = self._get_windows_patcher.start()

        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_window.left = 0
        mock_window.top = 0
        mock_window.right = 1280
        mock_window.bottom = 720
        mock_window.activate = MagicMock()
        mock_window.isMinimized = False
        self.mock_get_windows.return_value = [mock_window]

        self.player_ship = MagicMock()
        self.hostile_ship = MagicMock()

        self.player_screenshot = object()
        self.hostile_screenshot = object()

        self.player_ship.screenshot.return_value = self.player_screenshot
        self.hostile_ship.screenshot.return_value = self.hostile_screenshot

        self.player_ship.weapons = []
        self.hostile_ship.rooms = []

        self.player_ship.detect_health.return_value = 25
        self.player_ship.detect_shield.return_value = 2
        self.hostile_ship.detect_health.return_value = 12
        self.hostile_ship.detect_shield.return_value = 1

    def tearDown(self):
        self._get_windows_patcher.stop()

    @patch('Controller.CombatHandler.time.time', return_value=100.0)
    def test_init_scans_both_ships_and_starts_paused(self, mock_time):
        handler = CombatHandler(self.player_ship, self.hostile_ship)

        self.assertTrue(handler.is_paused)
        self.assertEqual(handler.last_pause, 100.0)
        self.assertEqual(handler.paused_duration, 0)

        self.player_ship.screenshot.assert_called_once()
        self.player_ship.full_scan.assert_called_once_with(self.player_screenshot)

        self.hostile_ship.screenshot.assert_called_once()
        self.hostile_ship.full_scan.assert_called_once_with(self.hostile_screenshot)

    @patch('Controller.CombatHandler.time.time', return_value=200.0)
    def test_pause_sets_pause_state_and_resets_duration(self, mock_time):
        handler = CombatHandler(self.player_ship, self.hostile_ship)
        handler.is_paused = False
        handler.paused_duration = 9.5

        handler.pause()

        self.assertTrue(handler.is_paused)
        self.assertEqual(handler.last_pause, 200.0)
        self.assertEqual(handler.paused_duration, 0)

    @patch('Controller.CombatHandler.time.time', side_effect=[100.0, 150.0])
    def test_unpause_updates_duration_and_weapon_cooldowns(self, mock_time):
        weapon_one = StubWeapon('Basic Laser', can_fire_response=True, last_fired=10.0)
        weapon_two = StubWeapon('Artemis', can_fire_response=False, last_fired=25.0)
        self.player_ship.weapons = [weapon_one, weapon_two]

        handler = CombatHandler(self.player_ship, self.hostile_ship)
        handler.unpause()

        self.assertFalse(handler.is_paused)
        self.assertEqual(handler.paused_duration, 50.0)
        self.assertEqual(handler.last_pause, 0)
        self.assertEqual(weapon_one.last_fired, 60.0)
        self.assertEqual(weapon_two.last_fired, 75.0)

    def test_check_player_status_delegates_to_player_ship(self):
        handler = CombatHandler(self.player_ship, self.hostile_ship)
        screenshot = object()

        health, shield = handler.check_player_status(screenshot)

        self.assertEqual(health, 25)
        self.assertEqual(shield, 2)
        self.player_ship.detect_health.assert_called_once_with(screenshot)
        self.player_ship.detect_shield.assert_called_once_with(screenshot)

    def test_check_hostile_status_delegates_to_hostile_ship(self):
        handler = CombatHandler(self.player_ship, self.hostile_ship)
        screenshot = object()

        health, shield = handler.check_hostile_status(screenshot)

        self.assertEqual(health, 12)
        self.assertEqual(shield, 1)
        self.hostile_ship.detect_health.assert_called_once_with(screenshot)
        self.hostile_ship.detect_shield.assert_called_once_with(screenshot)

    @patch('Controller.CombatHandler.time.time', return_value=100.0)
    def test_get_available_weapons_when_paused_uses_last_pause_time(self, mock_time):
        weapon_available = StubWeapon('Burst Laser', can_fire_response=True)
        weapon_unavailable = StubWeapon('Missile', can_fire_response=False)
        self.player_ship.weapons = [weapon_available, weapon_unavailable]

        handler = CombatHandler(self.player_ship, self.hostile_ship)
        handler.last_pause = 77.5
        handler.is_paused = True

        available = handler.get_available_weapons()

        self.assertEqual(available, [weapon_available])
        self.assertEqual(weapon_available.can_fire_calls, [77.5])
        self.assertEqual(weapon_unavailable.can_fire_calls, [77.5])

    @patch('Controller.CombatHandler.time.time', side_effect=[100.0, 250.0])
    def test_get_available_weapons_when_unpaused_uses_current_time(self, mock_time):
        weapon_available = StubWeapon('Burst Laser', can_fire_response=True)
        weapon_unavailable = StubWeapon('Missile', can_fire_response=False)
        self.player_ship.weapons = [weapon_available, weapon_unavailable]

        handler = CombatHandler(self.player_ship, self.hostile_ship)
        handler.is_paused = False

        available = handler.get_available_weapons()

        self.assertEqual(available, [weapon_available])
        self.assertEqual(weapon_available.can_fire_calls, [250.0])
        self.assertEqual(weapon_unavailable.can_fire_calls, [250.0])


if __name__ == '__main__':
    unittest.main()
