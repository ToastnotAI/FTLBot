import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from Model.PlayerShip import PlayerShip
from mock import patch, MagicMock
from PIL import Image

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

    @patch('Model.PlayerShip.pyautogui.screenshot')
    def test_screenshot(self, mock_screenshot):
        # Mock the screenshot function to return a dummy image
        mock_screenshot.return_value = "dummy_screenshot"
        screenshot = self.player_ship.screenshot()
        self.assertEqual(screenshot, "dummy_screenshot")

    def test_detect_health(self):
        # Replace screenshot with a preset image TestImage1.jpg that has a known health bar state
        test_image = Image.open('Test/Model/TestImage1.jpg')
        self.player_ship.TITLE_BAR_HEIGHT = 0  # Set title bar height to 0 for testing
        
        health = self.player_ship.detect_health(test_image)
        # Assuming TestImage1.jpg has 25 hit points, we can assert that the detected health is correct
        self.assertEqual(health, 25)



