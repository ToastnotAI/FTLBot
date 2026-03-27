import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from Model.PlayerShip import PlayerShip
from mock import patch, MagicMock
from PIL import Image
import time

class TestPlayerShip(unittest.TestCase):
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

    @patch('Model.PlayerShip.pyautogui.screenshot')
    def test_screenshot(self, mock_screenshot):
        # Mock the screenshot function to return a dummy image
        mock_screenshot.return_value = "dummy_screenshot"
        screenshot = self.player_ship.screenshot()
        self.assertEqual(screenshot, "dummy_screenshot")


    def test_detect_health(self):
        # Replace screenshot with a preset image TestImage1.jpg that has a known health bar state
        test_image = Image.open('Test/Model/TestImage1.jpg')
        
        health = self.player_ship.detect_health(test_image)
        # Assuming TestImage1.jpg has 25 hit points, we can assert that the detected health is correct
        self.assertEqual(health, 25)
        self.assertEqual(self.player_ship.health, 25)

    def test_detect_health_yellow(self):
        # Replace screenshot with a preset image TestYellowBar. that has a known health bar state with yellow pixels
        test_image = Image.open('Test/Model/TestYellowBar.png')
        
        health = self.player_ship.detect_health(test_image)
        # Assuming TestYellowBar.png has 18 hit points, we can assert that the detected health is correct
        self.assertEqual(health, 18)
        self.assertEqual(self.player_ship.health, 18)

    def test_detect_health_red(self):
        # Replace screenshot with a preset image TestImage2.pngthat has a known health bar state with red pixels
        # The border on test image 2 has flashed red, but should not be counted as a hit point
        test_image = Image.open('Test/Model/TestImage2.png')
        
        health = self.player_ship.detect_health(test_image)
        # Assuming TestImage2.png has 6 hit points, we can assert that the detected health is correct
        self.assertEqual(health, 6)
        self.assertEqual(self.player_ship.health, 6)

    def test_detect_shield(self):
        # Replace screenshot with a preset image TestImage1.jpg that has a known shield bar state
        test_image = Image.open('Test/Model/TestImage1.jpg')
        
        shield = self.player_ship.detect_shield(test_image)
        # Assuming TestImage1.jpg has 2 shield points, we can assert that the detected shield is correct
        self.assertEqual(shield, 2)
        self.assertEqual(self.player_ship.shield, 2)
        
    def test_detect_shield_broken(self):
        # screenshot is the same as detect_health_yellow, which has a broken shield bar with 0 shield points
        test_image = Image.open('Test/Model/TestYellowBar.png')
        shield = self.player_ship.detect_shield(test_image)
        # Assuming TestYellowBar.png has 0 shield points, we can assert that the detected shield is correct
        self.assertEqual(shield, 0)
        self.assertEqual(self.player_ship.shield, 0)

