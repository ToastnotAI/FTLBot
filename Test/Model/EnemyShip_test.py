import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))
from Model.EnemyShip import EnemyShip
from unittest.mock import patch, MagicMock
from PIL import Image

RESIZED_FIXTURE = 'Test/Model/TestResizedWindow.png'
RESIZED_TEST_TITLE_BAR = 45
RESIZED_TEST_LEFT_BORDER = 8

class TestEnemyShip(unittest.TestCase):
    @patch('Model.EnemyShip.pyautogui.screenshot')
    @patch('Model.EnemyShip.gw.getWindowsWithTitle')
    def setUp(self, mock_get_windows, mock_screenshot):
        # Mock the FTL window
        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_window.left = 0
        mock_window.top = 0
        mock_get_windows.return_value = [mock_window]

        self.enemy_ship = EnemyShip()
        self.enemy_ship.TITLE_BAR_HEIGHT = 0  # Set title bar height to 0 for testing
        self.enemy_ship.WINDOW_LEFT_BORDER = 0  # Set left border to 0 for testing


    def test_detect_health(self):
        test_image = Image.open('Test/Model/TestImage2.png')
        health = self.enemy_ship.detect_health(test_image)
        # Assuming TestImage2.png has 14 hit points for the enemy ship, we can assert that the detected health is correct
        self.assertEqual(health, 14)
        self.assertEqual(self.enemy_ship.health, 14)

    def test_detect_shield(self):
        test_image = Image.open('Test/Model/TestImage2.png')
        shield = self.enemy_ship.detect_shield(test_image, DEBUG=True)
        # Assuming TestImage2.png has 3 shield points for the enemy ship, we can assert that the detected shield is correct
        self.assertEqual(shield, 3)
        self.assertEqual(self.enemy_ship.shield, 3)

    def test_detect_shield_broken(self):
        test_image = Image.open('Test/Model/TestYellowBar.png')
        shield = self.enemy_ship.detect_shield(test_image)
        # Assuming TestYellowBar.png has 0 shield points for the enemy ship, we can assert that the detected shield is correct
        self.assertEqual(shield, 0)
        self.assertEqual(self.enemy_ship.shield, 0)


class TestEnemyShipResizedWindow(unittest.TestCase):
    @patch('Model.EnemyShip.pyautogui.screenshot')
    @patch('Model.EnemyShip.gw.getWindowsWithTitle')
    def setUp(self, mock_get_windows, mock_screenshot):
        # Use the resized fixture dimensions as the mocked window geometry.
        with Image.open(RESIZED_FIXTURE) as fixture_image:
            self.fixture_image = fixture_image.copy()
        fixture_width, fixture_height = self.fixture_image.size

        mock_window = MagicMock()
        mock_window.width = fixture_width
        mock_window.height = fixture_height
        mock_window.left = 0
        mock_window.top = 0
        mock_get_windows.return_value = [mock_window]

        def _mock_capture(region=None):
            if region is None:
                return self.fixture_image.copy()
            left, top, width, height = region
            return self.fixture_image.crop((left, top, left + width, top + height))

        mock_screenshot.side_effect = _mock_capture

        self.enemy_ship = EnemyShip()
        self.enemy_ship.TITLE_BAR_HEIGHT = RESIZED_TEST_TITLE_BAR
        self.enemy_ship.WINDOW_LEFT_BORDER = RESIZED_TEST_LEFT_BORDER
        self.test_image = self.enemy_ship.screenshot()

    def test_detect_health_resized_fixture(self):
        health = self.enemy_ship.detect_health(self.test_image)
        self.assertEqual(health, 10)
        self.assertEqual(self.enemy_ship.health, 10)

    def test_detect_shield_resized_fixture(self):
        shield = self.enemy_ship.detect_shield(self.test_image)
        self.assertEqual(shield, 1)
        self.assertEqual(self.enemy_ship.shield, 1)