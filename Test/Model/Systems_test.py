import time
import unittest
import sys
import os
from mock import patch, MagicMock
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from Model.PlayerShip import PlayerShip
from Model.Systems import System, Weapon, Reactor

class TestPlayerShipWeapons(unittest.TestCase):
    @patch('Model.PlayerShip.pyautogui.screenshot')
    @patch('Model.PlayerShip.gw.getWindowsWithTitle')
    def setUp(self, mock_get_windows, mock_screenshot):
        # Mock the FTL window
        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_window.left = 0
        mock_window.top = 0
        mock_get_windows.return_value = [mock_window]

        self.player_ship = PlayerShip()
        self.player_ship.TITLE_BAR_HEIGHT = 0  # Set title bar height to 0 for testing
        self.player_ship.WINDOW_LEFT_BORDER = 0  # Set left border to 0 for testing

        screenshot = Image.open('Test/Model/TestImage1.jpg') # As weapons are hard-coded, the screenshot can be any image for now
        self.player_ship.detect_weapons(screenshot)

    def test_weapons_initialise_with_expected_weapons(self):
        # Assuming TestImage1.jpg has 2 weapons, we can assert that the detected weapons are correct
        self.assertEqual(len(self.player_ship.weapons), 2)

    def test_weapons_can_fire_when_no_cooldown(self):
        # Assuming TestImage1.jpg has 2 weapons, we can assert that both weapons can fire when there is no cooldown
        for weapon in self.player_ship.weapons:
            weapon.last_fired = 0
            self.assertTrue(weapon.can_fire())

    def test_weapons_cooldown_enforced(self):
        # Assuming TestImage1.jpg has 2 weapons, we can assert that both weapons cannot fire when there is a cooldown
        for weapon in self.player_ship.weapons:
            weapon.last_fired = time.time()
            self.assertFalse(weapon.can_fire())


class TestReactor(unittest.TestCase):
    @patch('Model.PlayerShip.pyautogui.screenshot')
    @patch('Model.PlayerShip.gw.getWindowsWithTitle')
    def setUp(self, mock_get_windows, mock_screenshot):
        # Mock the FTL window
        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_window.left = 0
        mock_window.top = 0
        mock_get_windows.return_value = [mock_window]

        self.reactor = Reactor(8)

    def test_reactor_initial_power(self):
        self.assertEqual(self.reactor.available_power, 8)

    def test_reactor_refresh_power(self):
        # Assuming available power in TestImage1.jpg is 1, we can assert that the reactor refreshes power correctly
        test_image = Image.open('Test/Model/TestImage1.jpg')
        self.reactor.refresh_power(test_image)
        self.assertEqual(self.reactor.available_power, 1)